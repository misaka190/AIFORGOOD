from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from dataset import CXRDataset
from metrics import compute_calibration_data, compute_multilabel_metrics, export_error_cases
from models import build_model
from transforms import build_eval_transforms
from utils import build_inference_output, ensure_dir, export_onnx, export_torchscript, load_yaml_config, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate MedVision-CXR model")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--split", type=str, default="test", choices=["valid", "test"])
    parser.add_argument("--export-format", type=str, default="", choices=["", "torchscript", "onnx"])
    return parser.parse_args()


@torch.no_grad()
def infer_loader(model, loader, device):
    model.eval()
    probabilities, targets, masks = [], [], []
    image_ids, image_paths = [], []

    for batch in loader:
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


def main() -> None:
    args = parse_args()
    cfg = load_yaml_config(args.config)
    output_dir = ensure_dir(Path(cfg["experiment"]["output_dir"]) / f"evaluation_{args.split}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    csv_path = cfg["data"]["valid_csv"] if args.split == "valid" else cfg["data"]["test_csv"]
    dataset = CXRDataset(
        csv_path=csv_path,
        image_root=cfg["data"]["image_root"],
        labels=cfg["data"]["labels"],
        transform=build_eval_transforms(cfg["data"]["image_size"], use_clahe=cfg["data"]["use_clahe"]),
        in_channels=cfg["data"]["in_channels"],
        quality_cfg=cfg["data"]["quality_checks"],
        chexpert_mapping=cfg["data"]["chexpert_label_mapping"],
    )
    loader = DataLoader(
        dataset,
        batch_size=cfg["train"]["batch_size"],
        shuffle=False,
        num_workers=cfg["data"]["num_workers"],
        pin_memory=cfg["data"]["pin_memory"],
    )

    model = build_model(
        name=cfg["model"]["name"],
        num_labels=len(cfg["data"]["labels"]),
        pretrained=False,
        dropout=cfg["model"]["dropout"],
        in_channels=cfg["data"]["in_channels"],
    ).to(device)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    y_prob, y_true, y_mask, image_ids, image_paths = infer_loader(model, loader, device)
    metrics = compute_multilabel_metrics(
        y_true=y_true,
        y_prob=y_prob,
        y_mask=y_mask,
        labels=cfg["data"]["labels"],
        default_threshold=cfg["evaluation"]["default_threshold"],
        threshold_search_metric=cfg["evaluation"]["threshold_search_metric"],
    )
    save_json(metrics, output_dir / "metrics.json")
    save_json(
        compute_calibration_data(
            y_true=y_true,
            y_prob=y_prob,
            y_mask=y_mask,
            labels=cfg["data"]["labels"],
            n_bins=cfg["evaluation"]["calibration_bins"],
        ),
        output_dir / "calibration.json",
    )
    export_error_cases(
        image_ids,
        image_paths,
        y_true,
        y_prob,
        y_mask,
        cfg["data"]["labels"],
        metrics["thresholds"],
        output_dir / "error_cases.csv",
    )

    first_prediction = build_inference_output(
        image_id=image_ids[0],
        labels=cfg["data"]["labels"],
        probabilities=y_prob[0],
        thresholds=np.array(metrics["thresholds"], dtype=np.float32),
        confidence_score=float(np.max(y_prob[0])),
        cfg=cfg,
    )
    save_json(first_prediction, output_dir / "sample_inference_output.json")

    example_input = torch.randn(1, cfg["data"]["in_channels"], cfg["data"]["image_size"], cfg["data"]["image_size"], device=device)
    if args.export_format == "torchscript":
        export_torchscript(model, example_input, output_dir / "model.ts")
    elif args.export_format == "onnx":
        export_onnx(model, example_input, output_dir / "model.onnx", cfg["export"]["onnx_opset"])

    print(f"Evaluation complete. Macro AUROC: {metrics['macro_auroc']:.4f}")


if __name__ == "__main__":
    main()
