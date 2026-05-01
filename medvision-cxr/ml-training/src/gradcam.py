from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget


@dataclass
class GradCAMArtifact:
    target_label: str
    target_index: int
    target_layer: str
    heatmap: np.ndarray
    overlay: np.ndarray


def _resolve_single_target_layer(model: torch.nn.Module, model_name: str, target_layer_name: str | None = None):
    if target_layer_name:
        current = model
        for part in target_layer_name.split("."):
            current = current[int(part)] if part.isdigit() else getattr(current, part)
        return current, target_layer_name

    layers = resolve_target_layers(model, model_name)
    layer = layers[0]
    return layer, _default_target_layer_name(model_name)


def _default_target_layer_name(model_name: str) -> str:
    model_name = model_name.lower()
    if model_name == "densenet121":
        return "features.denseblock4"
    if model_name == "resnet50":
        return "layer4.2"
    if model_name == "efficientnet_b0":
        return "features.8"
    if model_name == "convnext_tiny":
        return "features.7.2"
    raise ValueError(f"Unsupported model for Grad-CAM: {model_name}")


def resolve_target_layers(model: torch.nn.Module, model_name: str):
    model_name = model_name.lower()
    if model_name == "densenet121":
        return [model.features.denseblock4]
    if model_name == "resnet50":
        return [model.layer4[-1]]
    if model_name == "efficientnet_b0":
        return [model.features[-1]]
    if model_name == "convnext_tiny":
        return [model.features[-1][-1]]
    raise ValueError(f"Unsupported model for Grad-CAM: {model_name}")


def generate_heatmap(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    class_index: int,
    model_name: str,
    target_layer_name: str | None = None,
) -> np.ndarray:
    target_layer, _ = _resolve_single_target_layer(model, model_name, target_layer_name)
    with GradCAM(model=model, target_layers=[target_layer]) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=[ClassifierOutputTarget(class_index)])
    if grayscale_cam.ndim == 3:
        return grayscale_cam[0]
    return grayscale_cam


def generate_gradcam_overlay(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    rgb_image: np.ndarray,
    class_index: int,
    model_name: str,
    target_layer_name: str | None = None,
) -> np.ndarray:
    grayscale_cam = generate_heatmap(model, input_tensor, class_index, model_name, target_layer_name)
    overlay = show_cam_on_image(rgb_image.astype(np.float32) / 255.0, grayscale_cam, use_rgb=True)
    return overlay


def save_overlay(overlay: np.ndarray, output_path: str | Path) -> None:
    cv2.imwrite(str(output_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))


def save_heatmap(heatmap: np.ndarray, output_path: str | Path) -> None:
    if heatmap.max() <= 1.0:
        heatmap = np.uint8(heatmap * 255)
    colorized = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
    cv2.imwrite(str(output_path), colorized)


def generate_gradcam_artifact(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    rgb_image: np.ndarray,
    class_index: int,
    target_label: str,
    model_name: str,
    target_layer_name: str | None = None,
) -> GradCAMArtifact:
    grayscale_cam = generate_heatmap(model, input_tensor, class_index, model_name, target_layer_name)
    overlay = show_cam_on_image(rgb_image.astype(np.float32) / 255.0, grayscale_cam, use_rgb=True)
    _, resolved_layer_name = _resolve_single_target_layer(model, model_name, target_layer_name)
    return GradCAMArtifact(
        target_label=target_label,
        target_index=class_index,
        target_layer=resolved_layer_name,
        heatmap=grayscale_cam,
        overlay=overlay,
    )


def generate_gradcam_batch(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    rgb_images: np.ndarray,
    class_indices: Iterable[int],
    class_labels: Iterable[str],
    model_name: str,
    target_layer_name: str | None = None,
) -> list[GradCAMArtifact]:
    artifacts: list[GradCAMArtifact] = []
    class_indices = list(class_indices)
    class_labels = list(class_labels)
    if input_tensor.ndim != 4:
        raise ValueError("input_tensor must have shape [batch, channels, height, width]")
    if rgb_images.ndim != 4:
        raise ValueError("rgb_images must have shape [batch, height, width, channels]")
    if input_tensor.shape[0] != rgb_images.shape[0]:
        raise ValueError("Batch size mismatch between input_tensor and rgb_images")
    if input_tensor.shape[0] != len(class_indices) or len(class_indices) != len(class_labels):
        raise ValueError("Provide one class index and class label per image in the batch")

    for batch_index, class_index in enumerate(class_indices):
        artifacts.append(
            generate_gradcam_artifact(
                model=model,
                input_tensor=input_tensor[batch_index : batch_index + 1],
                rgb_image=rgb_images[batch_index],
                class_index=class_index,
                target_label=class_labels[batch_index],
                model_name=model_name,
                target_layer_name=target_layer_name,
            )
        )
    return artifacts


def save_gradcam_artifacts(artifact: GradCAMArtifact, output_dir: str | Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = artifact.target_label.lower().replace(" ", "_")
    heatmap_path = output_dir / f"{safe_label}_heatmap.png"
    overlay_path = output_dir / f"{safe_label}_overlay.png"
    save_heatmap(artifact.heatmap, heatmap_path)
    save_overlay(artifact.overlay, overlay_path)
    return {
        "heatmap_path": str(heatmap_path),
        "overlay_path": str(overlay_path),
        "target_layer": artifact.target_layer,
        "target_label": artifact.target_label,
    }