from __future__ import annotations

import albumentations as A
from albumentations.pytorch import ToTensorV2


def build_train_transforms(image_size: int, use_clahe: bool = False):
    transforms = []
    if use_clahe:
        transforms.append(A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.5))

    transforms.extend(
        [
            A.RandomResizedCrop(height=image_size, width=image_size, scale=(0.9, 1.0), ratio=(0.95, 1.05), p=0.6),
            A.HorizontalFlip(p=0.1),
            A.Rotate(limit=7, border_mode=0, p=0.4),
            A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.4),
            A.GaussNoise(var_limit=(5.0, 25.0), p=0.2),
            A.Resize(image_size, image_size),
            A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            ToTensorV2(),
        ]
    )
    return A.Compose(transforms)


def build_eval_transforms(image_size: int, use_clahe: bool = False):
    transforms = []
    if use_clahe:
        transforms.append(A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=1.0))

    transforms.extend(
        [
            A.Resize(image_size, image_size),
            A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            ToTensorV2(),
        ]
    )
    return A.Compose(transforms)


UNSAFE_AUGMENTATIONS = [
    "VerticalFlip",
    "LargeRotation",
    "ElasticTransform",
    "GridDistortion",
    "CoarseDropoutOverThorax",
    "AggressiveRandomCrop",
]
