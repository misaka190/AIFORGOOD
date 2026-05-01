from __future__ import annotations

import torch
import torch.nn as nn


class MaskedBCEWithLogitsLoss(nn.Module):
    def __init__(self, pos_weight: torch.Tensor | None = None) -> None:
        super().__init__()
        self.base_loss = nn.BCEWithLogitsLoss(pos_weight=pos_weight, reduction="none")

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, target_mask: torch.Tensor) -> torch.Tensor:
        losses = self.base_loss(logits, targets)
        masked_losses = losses * target_mask
        valid = torch.clamp(target_mask.sum(), min=1.0)
        return masked_losses.sum() / valid


def build_loss(pos_weight: torch.Tensor | None = None) -> MaskedBCEWithLogitsLoss:
    return MaskedBCEWithLogitsLoss(pos_weight=pos_weight)