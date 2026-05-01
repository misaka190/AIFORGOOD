from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path

import numpy as np
import pydicom
import torch
from PIL import Image
from torchvision import models, transforms

from app.core.config import get_settings
from app.schemas.schemas import DISCLAIMER_TEXT


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

THRESHOLDS = {
    "Atelectasis": 0.45,
    "Cardiomegaly": 0.5,
    "Consolidation": 0.45,
    "Edema": 0.45,
    "Pleural Effusion": 0.48,
    "Pneumonia": 0.43,
    "Pneumothorax": 0.4,
    "Lung Opacity": 0.45,
    "Enlarged Cardiomediastinum": 0.5,
    "Fracture": 0.4,
    "Support Devices": 0.5,
    "No Finding": 0.55,
}


class MedVisionModelService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model()
        self.preprocessing = transforms.Compose(
            [
                transforms.Resize((320, 320)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def _load_model(self) -> torch.nn.Module:
        model = models.densenet121(weights=None)
        classifier_in = model.classifier.in_features
        model.classifier = torch.nn.Linear(classifier_in, len(LABELS))
        artifact_path = Path(self.settings.model_artifact_path)
        if artifact_path.exists():
            state_dict = torch.load(artifact_path, map_location=self.device)
            if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
                state_dict = state_dict["model_state_dict"]
            model.load_state_dict(state_dict, strict=False)
        model.to(self.device)
        model.eval()
        return model

    def load_image(self, contents: bytes, extension: str) -> Image.Image:
        if extension == ".dcm":
            dataset = pydicom.dcmread(io.BytesIO(contents), force=True)
            pixel_array = dataset.pixel_array.astype(np.float32)
            pixel_array -= pixel_array.min()
            pixel_array /= np.clip(pixel_array.max(), 1e-6, None)
            pixel_array = (pixel_array * 255).astype(np.uint8)
            image = Image.fromarray(pixel_array).convert("RGB")
            return image
        return Image.open(io.BytesIO(contents)).convert("RGB")

    def preprocess_image(self, contents: bytes, extension: str) -> tuple[torch.Tensor, Image.Image]:
        image = self.load_image(contents, extension)
        tensor = self.preprocessing(image).unsqueeze(0).to(self.device)
        return tensor, image

    def _overall_risk_level(self, probabilities: dict[str, float]) -> str:
        peak = max(probabilities.values())
        if peak >= 0.85:
            return "priority-review"
        if peak >= 0.65:
            return "high"
        if peak >= 0.35:
            return "medium"
        return "low"

    def _uncertainty_flag(self, probabilities: dict[str, float]) -> bool:
        for label, probability in probabilities.items():
            if abs(probability - THRESHOLDS[label]) <= 0.1:
                return True
        entropy_values = []
        for probability in probabilities.values():
            prob = min(max(probability, 1e-6), 1 - 1e-6)
            entropy = -(prob * np.log(prob) + (1 - prob) * np.log(1 - prob))
            entropy_values.append(entropy)
        return max(entropy_values, default=0.0) >= 0.65

    @torch.no_grad()
    def predict(self, contents: bytes, extension: str) -> dict:
        tensor, _ = self.preprocess_image(contents, extension)
        logits = self.model(tensor)
        probabilities_array = torch.sigmoid(logits).squeeze(0).cpu().numpy()
        probabilities = {label: float(probabilities_array[idx]) for idx, label in enumerate(LABELS)}
        flags = {label: probabilities[label] >= THRESHOLDS[label] for label in LABELS}
        overall_risk_level = self._overall_risk_level(probabilities)
        uncertainty_flag = self._uncertainty_flag(probabilities)
        doctor_review_required = uncertainty_flag or overall_risk_level in {"high", "priority-review"}
        confidence_score = float(np.max(probabilities_array))

        findings = [
            {
                "label": label,
                "risk_probability": round(probabilities[label], 6),
                "threshold": THRESHOLDS[label],
                "risk_flag": flags[label],
            }
            for label in LABELS
        ]

        return {
            "model_version": self.settings.model_version_name,
            "result_type": "AI-assisted risk assessment",
            "risk_assessment": {
                "overall_risk_level": overall_risk_level,
                "confidence_score": round(confidence_score, 6),
                "uncertainty_flag": uncertainty_flag,
                "doctor_review_required": doctor_review_required,
            },
            "triage_result": {
                "queue_priority": "urgent" if doctor_review_required else "standard",
                "review_reason": "high-risk-or-uncertain" if doctor_review_required else "routine-review",
            },
            "ai_assisted_findings": findings,
            "doctor_review_suggestion": (
                "当前结果提示高风险或存在不确定性，建议由医生优先复核，并结合临床信息综合判断。"
                if doctor_review_required
                else "当前结果未触发高优先级复核条件，但仍建议由医生结合临床背景进行常规复核。"
            ),
            "disclaimer": DISCLAIMER_TEXT,
        }


@lru_cache
def get_model_service() -> MedVisionModelService:
    return MedVisionModelService()
