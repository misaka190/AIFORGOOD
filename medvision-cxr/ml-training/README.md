# MedVision-CXR Training Pipeline

## Dataset plan

CheXpert is the recommended primary dataset because it is a chest X-ray benchmark with multi-label annotations and widely used baselines. Each label may appear as positive, negative, uncertain, or blank.

### Label handling

- positive: map to 1
- negative: map to 0
- uncertain: recommended demo strategy is ignore, with optional ablations for positive or negative remapping
- blank: recommended demo strategy is ignore, with optional negative remapping for selected labels only after validation

Ignoring uncertain and blank labels is implemented through a target mask so the loss only uses observed labels.

### CSV format

```csv
image_id,patient_id,image_path,split,Atelectasis,Cardiomegaly,Consolidation,Edema,Pleural Effusion,Pneumonia,Pneumothorax,Lung Opacity,Enlarged Cardiomediastinum,Fracture,Support Devices,No Finding
img_0001,patient_001,train/patient_001/study1_view1.jpg,train,1,0,-1,0,,0,0,1,0,0,0,0
```

### Image directory structure

```text
data/
  images/
    train/
      patient_001/
    valid/
      patient_204/
    test/
      patient_311/
  processed/
    train.csv
    valid.csv
    test.csv
```

### Patient-level split

Split by patient_id, not by image_path, to avoid leakage across train, validation, and test. Keep all studies from the same patient in the same split.

### Small demo recommendation

For a demo build, sample 3000 to 8000 studies with patient-level stratification, keep the 12 target labels, and train DenseNet121 for 10 to 15 epochs.

## Preprocessing guidance

- Chest X-rays are usually grayscale. For pretrained ImageNet backbones, converting grayscale to 3-channel RGB is the simplest baseline.
- Resize to 320x320 for the main run. Use 224x224 only when GPU memory is constrained.
- Normalize with ImageNet statistics when using pretrained CNN backbones.
- CLAHE should be optional and validated experimentally.
- HorizontalFlip should be used cautiously because laterality matters in chest imaging.
- Avoid vertical flips, large rotations, aggressive random crops, elastic distortion, and coarse dropout over thoracic regions.

## Model recommendation

- baseline: DenseNet121
- improved: EfficientNet-B0 for lightweight deployment or ConvNeXt-Tiny for stronger performance

Use a sigmoid activation at inference time because this is a multi-label task. Do not use softmax. Training uses BCEWithLogitsLoss because each label is an independent binary target.

## Training outputs

The training and evaluation scripts save:

- best_model.pt
- best_metrics.json
- calibration.json
- error_cases.csv
- sample_inference_output.json

The inference JSON uses medical-safe fields such as risk_probability, uncertainty_flag, doctor_review_required, and disclaimer.