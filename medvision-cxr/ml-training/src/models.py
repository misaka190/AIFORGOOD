from __future__ import annotations

import torch.nn as nn
from torchvision import models


def _patch_first_conv(module: nn.Module, in_channels: int) -> None:
    if in_channels == 3:
        return

    if hasattr(module, "conv1"):
        conv = module.conv1
        new_conv = nn.Conv2d(
            in_channels,
            conv.out_channels,
            kernel_size=conv.kernel_size,
            stride=conv.stride,
            padding=conv.padding,
            bias=conv.bias is not None,
        )
        module.conv1 = new_conv
        return

    if hasattr(module, "features") and hasattr(module.features, "conv0"):
        conv = module.features.conv0
        new_conv = nn.Conv2d(
            in_channels,
            conv.out_channels,
            kernel_size=conv.kernel_size,
            stride=conv.stride,
            padding=conv.padding,
            bias=conv.bias is not None,
        )
        module.features.conv0 = new_conv


def build_model(name: str, num_labels: int, pretrained: bool = True, dropout: float = 0.2, in_channels: int = 3):
    model_name = name.lower()
    if model_name == "densenet121":
        weights = models.DenseNet121_Weights.DEFAULT if pretrained else None
        model = models.densenet121(weights=weights)
        _patch_first_conv(model, in_channels)
        classifier_in = model.classifier.in_features
        model.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(classifier_in, num_labels))
        return model

    if model_name == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        _patch_first_conv(model, in_channels)
        classifier_in = model.fc.in_features
        model.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(classifier_in, num_labels))
        return model

    if model_name == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        _patch_first_conv(model, in_channels)
        classifier_in = model.classifier[-1].in_features
        model.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(classifier_in, num_labels))
        return model

    if model_name == "convnext_tiny":
        weights = models.ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
        model = models.convnext_tiny(weights=weights)
        first_conv = model.features[0][0]
        if in_channels != 3:
            model.features[0][0] = nn.Conv2d(
                in_channels,
                first_conv.out_channels,
                kernel_size=first_conv.kernel_size,
                stride=first_conv.stride,
                padding=first_conv.padding,
                bias=first_conv.bias is not None,
            )
        classifier_in = model.classifier[-1].in_features
        model.classifier = nn.Sequential(nn.LayerNorm([classifier_in], eps=1e-6), nn.Flatten(start_dim=1), nn.Dropout(dropout), nn.Linear(classifier_in, num_labels))
        return model

    raise ValueError(f"Unsupported model name: {name}")
