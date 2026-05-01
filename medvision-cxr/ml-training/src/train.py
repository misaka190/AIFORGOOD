from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
from torch.cuda.amp import GradScaler, autocast
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau
from torch.utils.data import DataLoader
from tqdm import tqdm

from dataset import CXRDataset
from losses import build_loss
from metrics import compute_calibration_data, compute_multilabel_metrics, export_error_cases
from models import build_model
from transforms import build_eval_transforms, build_train_transforms
from utils import compute_pos_weight, ensure_dir, load_yaml_config, save_checkpoint, save_json, seed_everything

try:
    import mlflow
except ImportError:  # pragma: no cover
    mlflow = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train MedVision-CXR multi-label classifier")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML config")
    return parser.parse_args()


def create_dataloaders(cfg: Dict) -> Tuple[DataLoader, DataLoader]:
    data_cfg = cfg["data"]
    train_dataset = CXRDataset(
        csv_path=data_cfg["train_csv"],
        image_root=data_cfg["image_root"],
        labels=data_cfg["labels"],
        transform=build_train_transforms(data_cfg["image_size"], use_clahe=data_cfg["use_clahe"]),
        in_channels=data_cfg["in_channels"],
        quality_cfg=data_cfg["quality_checks"],
        chexpert_mapping=data_cfg["chexpert_label_mapping"],
    )
    valid_dataset = CXRDataset(
        csv_path=data_cfg["valid_csv"],
        image_root=data_cfg["image_root"],
        labels=data_cfg["labels"],
        transform=build_eval_transforms(data_cfg["image_size"], use_clahe=data_cfg["use_clahe"]),
        in_channels=data_cfg["in_channels"],
        quality_cfg=data_cfg["quality_checks"],
        chexpert_mapping=data_cfg["chexpert_label_mapping"],
    )

    loader_kwargs = {
        "batch_size": cfg["train"]["batch_size"],
        "num_workers": data_cfg["num_workers"],
        "pin_memory": data_cfg["pin_memory"],
    }
    train_loader = DataLoader(train_dataset, shuffle=True, **loader_kwargs)
    valid_loader = DataLoader(valid_dataset, shuffle=False, **loader_kwargs)
    return train_loader, valid_loader


def run_epoch(model, loader, criterion, optimizer, scaler, device, use_amp: bool, train_mode: bool):
    model.train(mode=train_mode)
    total_loss = 0.0
    num_batches = 0

    for batch in tqdm(loader, leave=False):
        images = batch["image"].to(device)
        targets = batch["targets"].to(device)
        target_mask = batch["target_mask"].to(device)

        if train_mode:
            optimizer.zero_grad(set_to_none=True)

        with autocast(enabled=use_amp):
            logits = model(images)
            loss = criterion(logits, targets, target_mask)

        if train_mode:
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()

        total_loss += float(loss.item())
        num_batches += 1

    return total_loss / max(num_batches, 1)


@torch.no_grad()
def collect_predictions(model, loader, device):
    model.eval()
    probabilities, targets, masks = [], [], []
    image_ids, image_paths = [], []

    for batch in tqdm(loader, leave=False):
        images = batch["image"].to(device)
        logits = model(images)
        probs = torch.sigmoid(logits).cpu().numpy()

        probabilities.append(probs)
        targets.append(batch["targets"].numpy())
        masks.append(batch["target_mask"].numpy())
        image_ids.extend(batch["image_id"])
        image_paths.extend(batch["image_path"])

    return (
        np.concatenate(probabilities, axis=0),
        np.concatenate(targets, axis=0),
        np.concatenate(masks, axis=0),
        image_ids,
        image_paths,
    )


def build_scheduler(cfg: Dict, optimizer: torch.optim.Optimizer):
    scheduler_name = cfg["train"]["scheduler"].lower()
    if scheduler_name == "cosineannealinglr":
        return CosineAnnealingLR(optimizer, T_max=cfg["train"]["epochs"])
    return ReduceLROnPlateau(
        optimizer,
        mode="max",
        patience=cfg["train"]["scheduler_patience"],
        factor=cfg["train"]["scheduler_factor"],
    )


def main() -> None:
    args = parse_args()
    cfg = load_yaml_config(args.config)
    output_dir = ensure_dir(cfg["experiment"]["output_dir"])
    seed_everything(cfg["experiment"]["seed"])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, valid_loader = create_dataloaders(cfg)

    model = build_model(
        name=cfg["model"]["name"],
        num_labels=len(cfg["data"]["labels"]),
        pretrained=cfg["model"]["pretrained"],
        dropout=cfg["model"]["dropout"],
        in_channels=cfg["data"]["in_channels"],
    ).to(device)

    train_dataset = train_loader.dataset
    pos_weight = compute_pos_weight(train_dataset.label_matrix, train_dataset.label_mask).to(device)
    criterion = build_loss(pos_weight=pos_weight)
    optimizer = AdamW(model.parameters(), lr=cfg["train"]["learning_rate"], weight_decay=cfg["train"]["weight_decay"])
    scheduler = build_scheduler(cfg, optimizer)
    scaler = GradScaler(enabled=cfg["train"]["mixed_precision"] and device.type == "cuda")

    if cfg["experiment"]["use_mlflow"] and mlflow is not None:
        mlflow.set_experiment(cfg["experiment"]["name"])
        mlflow.start_run(run_name=cfg["experiment"]["name"])
        mlflow.log_params(
            {
                "model": cfg["model"]["name"],
                "image_size": cfg["data"]["image_size"],
                "batch_size": cfg["train"]["batch_size"],
                "lr": cfg["train"]["learning_rate"],
                "uncertain_strategy": cfg["data"]["chexpert_label_mapping"]["uncertain_strategy"],
            }
        )

    best_macro_auroc = -1.0
    best_epoch = -1
    patience_counter = 0

    for epoch in range(1, cfg["train"]["epochs"] + 1):
        train_loss = run_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            scaler,
            device,
            use_amp=cfg["train"]["mixed_precision"] and device.type == "cuda",
            train_mode=True,
        )
        valid_loss = run_epoch(
            model,
            valid_loader,
            criterion,
            optimizer,
            scaler,
            device,
            use_amp=False,
            train_mode=False,
        )
        valid_probs, valid_targets, valid_masks, image_ids, image_paths = collect_predictions(model, valid_loader, device)
        metrics = compute_multilabel_metrics(
            y_true=valid_targets,
            y_prob=valid_probs,
            y_mask=valid_masks,
            labels=cfg["data"]["labels"],
            default_threshold=cfg["evaluation"]["default_threshold"],
            threshold_search_metric=cfg["evaluation"]["threshold_search_metric"],
        )

        macro_auroc = metrics["macro_auroc"]
        if isinstance(scheduler, ReduceLROnPlateau):
            scheduler.step(macro_auroc)
        else:
            scheduler.step()

        if cfg["experiment"]["use_mlflow"] and mlflow is not None:
            mlflow.log_metrics(
                {
                    "train_loss": train_loss,
                    "valid_loss": valid_loss,
                    "valid_macro_auroc": macro_auroc,
                    "valid_macro_auprc": metrics["macro_auprc"],
                },
                step=epoch,
            )

        is_best = macro_auroc > best_macro_auroc
        if is_best:
            best_macro_auroc = macro_auroc
            best_epoch = epoch
            patience_counter = 0

            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "config": cfg,
                "metrics": metrics,
            }
            save_checkpoint(
                checkpoint,
                output_dir / f"checkpoint_epoch_{epoch}.pt",
                is_best=True,
                best_path=output_dir / "best_model.pt",
            )
            save_json(metrics, output_dir / "best_metrics.json")
            save_json(
                compute_calibration_data(
                    valid_targets,
                    valid_probs,
                    valid_masks,
                    cfg["data"]["labels"],
                    n_bins=cfg["evaluation"]["calibration_bins"],
                ),
                output_dir / "calibration.json",
            )
            if cfg["evaluation"]["export_error_cases"]:
                export_error_cases(
                    image_ids,
                    image_paths,
                    valid_targets,
                    valid_probs,
                    valid_masks,
                    cfg["data"]["labels"],
                    metrics["thresholds"],
                    output_dir / "error_cases.csv",
                )
        else:
            patience_counter += 1

        print(
            f"Epoch {epoch:02d} | train_loss={train_loss:.4f} | valid_loss={valid_loss:.4f} | "
            f"valid_macro_auroc={macro_auroc:.4f}"
        )

        if patience_counter >= cfg["train"]["early_stopping_patience"]:
            print(f"Early stopping triggered at epoch {epoch}. Best epoch was {best_epoch}.")
            break

    if cfg["experiment"]["use_mlflow"] and mlflow is not None:
        mlflow.end_run()


if __name__ == "__main__":
    main()
