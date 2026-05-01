from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset


LABELS = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Pleural Effusion",
    "Pneumonia",
    "Pneumothorax",
    "Lung Opacity",
    "Enlarged Cardiomediastinum",
    "Fracture",
    "Support Devices",
    "No Finding",
]


@dataclass
class QualityReport:
    too_small: bool
    low_contrast: bool
    high_blank_ratio: bool
    suspicious: bool


def map_chexpert_value(value: Any, positive: float, negative: float, uncertain_strategy: str, blank_strategy: str) -> float:
    if pd.isna(value) or value == "":
        if blank_strategy == "negative":
            return negative
        if blank_strategy == "positive":
            return positive
        return np.nan

    numeric_value = float(value)
    if numeric_value == 1.0:
        return positive
    if numeric_value == 0.0:
        return negative
    if numeric_value == -1.0:
        if uncertain_strategy == "positive":
            return positive
        if uncertain_strategy == "negative":
            return negative
        return np.nan
    return np.nan


def run_quality_checks(image: np.ndarray, quality_cfg: Dict[str, Any]) -> QualityReport:
    height, width = image.shape[:2]
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    std_intensity = float(gray.std())
    blank_ratio = float(np.mean(gray <= 5) + np.mean(gray >= 250)) / 2.0

    too_small = min(height, width) < quality_cfg["min_size"]
    low_contrast = std_intensity < quality_cfg["min_std"]
    high_blank_ratio = blank_ratio > quality_cfg["max_blank_ratio"]
    suspicious = too_small or low_contrast or high_blank_ratio
    return QualityReport(
        too_small=too_small,
        low_contrast=low_contrast,
        high_blank_ratio=high_blank_ratio,
        suspicious=suspicious,
    )


class CXRDataset(Dataset):
    def __init__(
        self,
        csv_path: str | Path,
        image_root: str | Path,
        labels: Optional[List[str]] = None,
        transform=None,
        in_channels: int = 3,
        quality_cfg: Optional[Dict[str, Any]] = None,
        chexpert_mapping: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.image_root = Path(image_root)
        self.labels = labels or LABELS
        self.transform = transform
        self.in_channels = in_channels
        self.quality_cfg = quality_cfg or {"min_size": 224, "min_std": 8.0, "max_blank_ratio": 0.92}
        self.chexpert_mapping = chexpert_mapping or {
            "positive": 1.0,
            "negative": 0.0,
            "uncertain_strategy": "ignore",
            "blank_strategy": "ignore",
        }

        self.dataframe = pd.read_csv(self.csv_path)
        self._validate_columns()
        self.label_matrix, self.label_mask = self._build_label_arrays()

    def _validate_columns(self) -> None:
        required = {"image_id", "image_path", "patient_id", "split"}
        missing_required = required - set(self.dataframe.columns)
        if missing_required:
            raise ValueError(f"Missing required columns: {sorted(missing_required)}")

        missing_labels = [label for label in self.labels if label not in self.dataframe.columns]
        if missing_labels:
            raise ValueError(f"Missing label columns: {missing_labels}")

    def _build_label_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        label_values = []
        valid_mask = []
        for label in self.labels:
            mapped = self.dataframe[label].apply(
                lambda value: map_chexpert_value(
                    value,
                    positive=self.chexpert_mapping["positive"],
                    negative=self.chexpert_mapping["negative"],
                    uncertain_strategy=self.chexpert_mapping["uncertain_strategy"],
                    blank_strategy=self.chexpert_mapping["blank_strategy"],
                )
            )
            array = mapped.to_numpy(dtype=np.float32)
            label_values.append(np.nan_to_num(array, nan=0.0))
            valid_mask.append(~np.isnan(array))

        return np.stack(label_values, axis=1), np.stack(valid_mask, axis=1).astype(np.float32)

    def __len__(self) -> int:
        return len(self.dataframe)

    def _load_image(self, image_path: str) -> np.ndarray:
        absolute_path = self.image_root / image_path
        pil_image = Image.open(absolute_path)
        grayscale = np.array(pil_image.convert("L"))

        if self.in_channels == 1:
            return grayscale
        return np.stack([grayscale, grayscale, grayscale], axis=-1)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        row = self.dataframe.iloc[index]
        image = self._load_image(str(row["image_path"]))
        quality = run_quality_checks(image, self.quality_cfg)

        if self.transform is not None:
            transformed = self.transform(image=image)
            image = transformed["image"]

        return {
            "image": image,
            "targets": self.label_matrix[index],
            "target_mask": self.label_mask[index],
            "image_id": row["image_id"],
            "patient_id": row["patient_id"],
            "image_path": row["image_path"],
            "quality_report": {
                "too_small": quality.too_small,
                "low_contrast": quality.low_contrast,
                "high_blank_ratio": quality.high_blank_ratio,
                "suspicious": quality.suspicious,
            },
        }
