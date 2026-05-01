from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _safe_binary_metric(metric_fn, y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(metric_fn(y_true, y_score))


def search_best_threshold(y_true: np.ndarray, y_prob: np.ndarray, metric_name: str = "f1") -> Tuple[float, float]:
    metric_name = metric_name.lower()
    candidates = np.arange(0.1, 0.91, 0.05)
    best_threshold = 0.5
    best_score = -1.0

    for threshold in candidates:
        y_pred = (y_prob >= threshold).astype(int)
        if metric_name == "precision":
            score = precision_score(y_true, y_pred, zero_division=0)
        elif metric_name == "recall":
            score = recall_score(y_true, y_pred, zero_division=0)
        else:
            score = f1_score(y_true, y_pred, zero_division=0)

        if score > best_score:
            best_threshold = float(threshold)
            best_score = float(score)

    return best_threshold, best_score


def compute_multilabel_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    y_mask: np.ndarray,
    labels: Iterable[str],
    default_threshold: float = 0.5,
    threshold_search_metric: str = "f1",
) -> Dict[str, object]:
    labels = list(labels)
    per_label: Dict[str, Dict[str, object]] = {}
    thresholds: List[float] = []
    aurocs: List[float] = []
    auprcs: List[float] = []

    for idx, label in enumerate(labels):
        mask = y_mask[:, idx].astype(bool)
        label_true = y_true[mask, idx]
        label_prob = y_prob[mask, idx]

        if label_true.size == 0:
            per_label[label] = {
                "auroc": float("nan"),
                "auprc": float("nan"),
                "precision": float("nan"),
                "recall": float("nan"),
                "f1": float("nan"),
                "threshold": default_threshold,
                "confusion_matrix": [[0, 0], [0, 0]],
            }
            thresholds.append(default_threshold)
            continue

        threshold = default_threshold
        if len(np.unique(label_true)) >= 2:
            threshold, _ = search_best_threshold(label_true, label_prob, threshold_search_metric)

        label_pred = (label_prob >= threshold).astype(int)
        cm = confusion_matrix(label_true, label_pred, labels=[0, 1]).tolist()
        auroc = _safe_binary_metric(roc_auc_score, label_true, label_prob)
        auprc = _safe_binary_metric(average_precision_score, label_true, label_prob)
        precision = float(precision_score(label_true, label_pred, zero_division=0))
        recall = float(recall_score(label_true, label_pred, zero_division=0))
        f1 = float(f1_score(label_true, label_pred, zero_division=0))

        per_label[label] = {
            "auroc": auroc,
            "auprc": auprc,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "threshold": threshold,
            "confusion_matrix": cm,
        }
        thresholds.append(threshold)
        if not np.isnan(auroc):
            aurocs.append(auroc)
        if not np.isnan(auprc):
            auprcs.append(auprc)

    return {
        "macro_auroc": float(np.nanmean(aurocs)) if aurocs else float("nan"),
        "macro_auprc": float(np.nanmean(auprcs)) if auprcs else float("nan"),
        "thresholds": thresholds,
        "per_label": per_label,
    }


def compute_calibration_data(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    y_mask: np.ndarray,
    labels: Iterable[str],
    n_bins: int = 10,
) -> Dict[str, Dict[str, List[float]]]:
    results: Dict[str, Dict[str, List[float]]] = {}
    for idx, label in enumerate(labels):
        mask = y_mask[:, idx].astype(bool)
        label_true = y_true[mask, idx]
        label_prob = y_prob[mask, idx]
        if label_true.size == 0 or len(np.unique(label_true)) < 2:
            results[label] = {"prob_true": [], "prob_pred": []}
            continue
        prob_true, prob_pred = calibration_curve(label_true, label_prob, n_bins=n_bins, strategy="uniform")
        results[label] = {
            "prob_true": prob_true.tolist(),
            "prob_pred": prob_pred.tolist(),
        }
    return results


def export_error_cases(
    image_ids: List[str],
    image_paths: List[str],
    y_true: np.ndarray,
    y_prob: np.ndarray,
    y_mask: np.ndarray,
    labels: Iterable[str],
    thresholds: Iterable[float],
    output_path: str | Path,
) -> None:
    records = []
    thresholds = list(thresholds)
    for sample_idx, image_id in enumerate(image_ids):
        for label_idx, label in enumerate(labels):
            if not y_mask[sample_idx, label_idx]:
                continue

            target = int(y_true[sample_idx, label_idx])
            probability = float(y_prob[sample_idx, label_idx])
            pred = int(probability >= thresholds[label_idx])
            if target == pred:
                continue

            records.append(
                {
                    "image_id": image_id,
                    "image_path": image_paths[sample_idx],
                    "label": label,
                    "target": target,
                    "predicted": pred,
                    "risk_probability": probability,
                    "error_type": "false_negative" if target == 1 and pred == 0 else "false_positive",
                }
            )

    pd.DataFrame(records).to_csv(output_path, index=False)
