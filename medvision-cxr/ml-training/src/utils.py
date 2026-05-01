from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import torch
import yaml


DISCLAIMER_TEXT = (
    "This system is for AI-assisted risk assessment and triage support only. "
    "It does not provide automated diagnosis, does not replace clinicians, and does not offer treatment advice."
)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def load_yaml_config(config_path: str | Path) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def save_json(payload: Dict[str, Any], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)


def save_checkpoint(
    state: Dict[str, Any],
    checkpoint_path: str | Path,
    is_best: bool = False,
    best_path: Optional[str | Path] = None,
) -> None:
    checkpoint_path = Path(checkpoint_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(state, checkpoint_path)
    if is_best and best_path is not None:
        torch.save(state, Path(best_path))


def compute_pos_weight(label_matrix: np.ndarray, label_mask: Optional[np.ndarray] = None) -> torch.Tensor:
    if label_mask is None:
        positives = label_matrix.sum(axis=0)
        valid_counts = np.full(label_matrix.shape[1], label_matrix.shape[0], dtype=np.float32)
    else:
        positives = (label_matrix * label_mask).sum(axis=0)
        valid_counts = np.clip(label_mask.sum(axis=0), 1.0, None)

    negatives = valid_counts - positives
    weights = np.where(positives > 0, negatives / np.clip(positives, 1.0, None), 1.0)
    return torch.tensor(weights, dtype=torch.float32)


def maybe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sigmoid_numpy(logits: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-logits))


def binary_entropy(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.clip(probabilities, 1e-6, 1.0 - 1e-6)
    return -(probabilities * np.log(probabilities) + (1.0 - probabilities) * np.log(1.0 - probabilities))


def derive_overall_risk(probabilities: np.ndarray, thresholds: Dict[str, float]) -> str:
    peak_probability = float(np.max(probabilities))
    if peak_probability >= thresholds["critical"]:
        return "critical"
    if peak_probability >= thresholds["high"]:
        return "high"
    if peak_probability >= thresholds["medium"]:
        return "medium"
    return "low"


def derive_uncertainty_flag(
    probabilities: np.ndarray,
    margin: float,
    entropy_threshold: float,
    threshold: float,
) -> bool:
    close_to_threshold = np.any(np.abs(probabilities - threshold) <= margin)
    high_entropy = np.any(binary_entropy(probabilities) >= entropy_threshold)
    return bool(close_to_threshold or high_entropy)


def build_inference_output(
    image_id: str,
    labels: Iterable[str],
    probabilities: np.ndarray,
    thresholds: np.ndarray,
    confidence_score: float,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    labels = list(labels)
    threshold_value = float(np.mean(thresholds)) if thresholds.size else 0.5
    uncertainty_flag = derive_uncertainty_flag(
        probabilities,
        margin=cfg["inference"]["uncertainty_margin"],
        entropy_threshold=cfg["inference"]["uncertainty_entropy_threshold"],
        threshold=threshold_value,
    )
    overall_risk_level = derive_overall_risk(
        probabilities,
        thresholds=cfg["inference"]["overall_risk_thresholds"],
    )
    doctor_review_required = uncertainty_flag or overall_risk_level in {"high", "critical"}

    ai_assisted_findings: List[Dict[str, Any]] = []
    for idx, label in enumerate(labels):
        ai_assisted_findings.append(
            {
                "label": label,
                "risk_probability": round(float(probabilities[idx]), 6),
                "threshold": round(float(thresholds[idx]), 6),
                "risk_flag": bool(probabilities[idx] >= thresholds[idx]),
            }
        )

    return {
        "image_id": image_id,
        "result_type": "AI-assisted risk assessment",
        "risk_assessment": {
            "overall_risk_level": overall_risk_level,
            "confidence_score": round(float(confidence_score), 6),
            "uncertainty_flag": uncertainty_flag,
            "doctor_review_required": doctor_review_required,
        },
        "ai_assisted_findings": ai_assisted_findings,
        "disclaimer": DISCLAIMER_TEXT,
    }


def export_torchscript(model: torch.nn.Module, example_input: torch.Tensor, export_path: str | Path) -> None:
    traced = torch.jit.trace(model.eval(), example_input)
    traced.save(str(export_path))


def export_onnx(
    model: torch.nn.Module,
    example_input: torch.Tensor,
    export_path: str | Path,
    opset_version: int,
) -> None:
    torch.onnx.export(
        model.eval(),
        example_input,
        str(export_path),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch_size"}, "logits": {0: "batch_size"}},
    )
