from __future__ import annotations

import io

import cv2
import numpy as np
import torch
from PIL import Image

from app.services.model_service import LABELS, MedVisionModelService
from app.utils.storage import storage


class GradCAMService:
    def __init__(self, model_service: MedVisionModelService) -> None:
        self.model_service = model_service
        self.activations = None
        self.gradients = None
        self.target_layer, self.target_layer_name = self._resolve_target_layer()
        self._register_hooks()

    def _resolve_target_layer(self):
        model = self.model_service.model
        if hasattr(model, "features") and hasattr(model.features, "denseblock4"):
            return model.features.denseblock4, "features.denseblock4"
        if hasattr(model, "features") and len(model.features) > 0:
            return model.features[-1], f"features.{len(model.features) - 1}"
        raise ValueError("Unsupported model architecture for Grad-CAM")

    def _register_hooks(self) -> None:
        def forward_hook(_, __, output):
            self.activations = output

        def backward_hook(_, grad_input, grad_output):
            del grad_input
            self.gradients = grad_output[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def _cam_from_gradients(self) -> np.ndarray:
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1).squeeze(0)
        cam = torch.relu(cam)
        cam = cam.detach().cpu().numpy()
        cam -= cam.min()
        cam /= np.clip(cam.max(), 1e-6, None)
        return cam

    def _heatmap_and_overlay(self, cam: np.ndarray, pil_image: Image.Image) -> tuple[np.ndarray, np.ndarray]:
        rgb_image = np.array(pil_image.resize((cam.shape[1], cam.shape[0]))).astype(np.uint8)
        heatmap = cv2.applyColorMap(np.uint8(cam * 255), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        overlay = cv2.addWeighted(rgb_image, 0.55, heatmap, 0.45, 0.0)
        return heatmap, overlay

    def generate(self, contents: bytes, extension: str, label_code: str, prediction_id: str) -> dict:
        tensor, pil_image = self.model_service.preprocess_image(contents, extension)
        tensor = tensor.clone().detach().requires_grad_(True)
        logits = self.model_service.model(tensor)
        label_index = LABELS.index(label_code)

        self.model_service.model.zero_grad(set_to_none=True)
        logits[0, label_index].backward(retain_graph=True)
        cam = self._cam_from_gradients()
        heatmap, overlay = self._heatmap_and_overlay(cam, pil_image)

        heatmap_buffer = io.BytesIO()
        overlay_buffer = io.BytesIO()
        Image.fromarray(heatmap).save(heatmap_buffer, format="PNG")
        Image.fromarray(overlay).save(overlay_buffer, format="PNG")

        heatmap_key = f"gradcam/{prediction_id}/{label_code.lower().replace(' ', '_')}_heatmap.png"
        overlay_key = f"gradcam/{prediction_id}/{label_code.lower().replace(' ', '_')}_overlay.png"

        storage.put_bytes("cxr-outputs", heatmap_key, heatmap_buffer.getvalue(), "image/png")
        storage.put_bytes("cxr-outputs", overlay_key, overlay_buffer.getvalue(), "image/png")

        return {
            "label": label_code,
            "heatmap_storage_key": heatmap_key,
            "overlay_storage_key": overlay_key,
            "heatmap_url": storage.public_url("cxr-outputs", heatmap_key),
            "overlay_url": storage.public_url("cxr-outputs", overlay_key),
            "target_layer": self.target_layer_name,
        }
