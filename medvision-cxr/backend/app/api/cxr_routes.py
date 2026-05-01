from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.models.models import ConsentRecord, CXRImage, CXRPrediction, GradCAMOutput, ModelVersion, PredictionLabel, User
from app.schemas.schemas import AnalyzeRequest, AnalyzeResponse, DeleteImageRequest, DeleteImageResponse, GradCAMGenerateResponse, GradCAMRequest, HeatmapResponse, HistoryResponse, HistoryItemOut, PredictionResultOut, UploadResponse
from app.services.audit_service import create_audit_log
from app.services.deletion_service import direct_delete_image
from app.utils.files import anonymized_filename, detect_image_size, remove_image_exif, sanitize_dicom, validate_upload_file
from app.utils.storage import storage


router = APIRouter(prefix="/cxr", tags=["cxr"])


def _quality_flags(width: int | None, height: int | None) -> dict:
    too_small = bool(width and height and min(width, height) < 224)
    return {
        "too_small": too_small,
        "orientation_warning": bool(width and height and width > height * 2),
        "requires_review": too_small,
    }


def _ensure_model_version(db: Session) -> ModelVersion:
    from app.services.model_service import get_model_service

    model_service = get_model_service()
    active_version = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()
    if active_version:
        return active_version

    version = ModelVersion(
        version_name=model_service.settings.model_version_name,
        model_family="DenseNet121",
        dataset_summary={"source": "CheXpert-based"},
        metrics_json={"status": "demo"},
        artifact_uri=model_service.settings.model_artifact_path,
        is_active=True,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def _load_image_bytes(image: CXRImage) -> bytes:
    try:
        return storage.get_bytes("cxr-raw", image.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stored image is unavailable") from exc


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_cxr(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    validate_upload_file(file)
    contents = await file.read()
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

    extension = Path(file.filename or "").suffix.lower()
    if extension == ".dcm":
        contents = sanitize_dicom(contents)
        content_type = "application/dicom"
    else:
        contents = remove_image_exif(contents, extension)
        content_type = file.content_type or "image/jpeg"

    width, height, modality = detect_image_size(contents, extension)
    object_name = f"uploads/{anonymized_filename(file.filename or f'image{extension}') }"
    storage_key = storage.put_bytes("cxr-raw", object_name, contents, content_type)

    consent = ConsentRecord(user_id=current_user.id, consent_version="v1.0", consent_text_snapshot="Upload consent accepted")
    db.add(consent)
    db.commit()
    db.refresh(consent)

    image = CXRImage(
        uploader_id=current_user.id,
        consent_id=consent.id,
        storage_key=storage_key,
        original_format=extension.replace(".", ""),
        width=width,
        height=height,
        modality=modality,
        quality_flags=_quality_flags(width, height),
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    create_audit_log(db, "upload", "cxr_image", image.id, actor_user_id=current_user.id, request=request, payload={"image_id": str(image.id)})
    return UploadResponse(image_id=image.id, storage_key=image.storage_key, quality_check=image.quality_flags)


@router.post("/{image_id}/analyze", response_model=AnalyzeResponse)
def analyze_cxr(
    image_id: str,
    payload: AnalyzeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    from app.services.gradcam_service import GradCAMService
    from app.services.model_service import get_model_service

    image = db.query(CXRImage).filter(CXRImage.id == image_id, CXRImage.is_deleted.is_(False)).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    contents = _load_image_bytes(image)

    model_version = _ensure_model_version(db)
    inference = get_model_service().predict(contents, f".{image.original_format}")
    prediction = CXRPrediction(
        image_id=image.id,
        model_version_id=model_version.id,
        job_status="completed",
        overall_risk_level=inference["risk_assessment"]["overall_risk_level"],
        uncertainty_flag=inference["risk_assessment"]["uncertainty_flag"],
        doctor_review_required=inference["risk_assessment"]["doctor_review_required"],
        confidence_score=inference["risk_assessment"]["confidence_score"],
        disclaimer=inference["disclaimer"],
        raw_scores_json={item["label"]: item["risk_probability"] for item in inference["ai_assisted_findings"]},
        triage_result_json=inference["triage_result"],
    )
    db.add(prediction)
    db.flush()

    for item in inference["ai_assisted_findings"]:
        db.add(
            PredictionLabel(
                prediction_id=prediction.id,
                label_code=item["label"],
                risk_probability=item["risk_probability"],
                threshold_used=item["threshold"],
                risk_flag=item["risk_flag"],
                calibrated_score=item["risk_probability"],
                finding_text=f"提示存在 {item['label']} 相关风险特征，建议结合医生复核。" if item["risk_flag"] else "当前标签未触发明显风险提示。",
            )
        )

    requested_heatmaps = payload.requested_heatmaps or [inference["ai_assisted_findings"][0]["label"]]
    gradcam_service = GradCAMService(get_model_service())
    for label_code in requested_heatmaps[:3]:
        gradcam = gradcam_service.generate(contents, f".{image.original_format}", label_code, str(prediction.id))
        db.add(
            GradCAMOutput(
                prediction_id=prediction.id,
                label_code=label_code,
                heatmap_storage_key=gradcam["heatmap_storage_key"],
                overlay_storage_key=gradcam["overlay_storage_key"],
                target_layer=gradcam["target_layer"],
            )
        )

    db.commit()
    db.refresh(prediction)
    create_audit_log(db, "analyze", "prediction", prediction.id, actor_user_id=current_user.id, request=request, payload={"priority": payload.priority})
    return AnalyzeResponse(job_id=prediction.id, image_id=image.id, status="completed")


@router.post("/{image_id}/gradcam", response_model=GradCAMGenerateResponse)
def generate_gradcam(
    image_id: str,
    payload: GradCAMRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GradCAMGenerateResponse:
    from app.services.gradcam_service import GradCAMService
    from app.services.model_service import get_model_service

    if str(payload.image_id) != image_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="image_id mismatch")

    image = db.query(CXRImage).filter(CXRImage.id == image_id, CXRImage.is_deleted.is_(False)).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    existing_prediction = (
        db.query(CXRPrediction)
        .filter(CXRPrediction.image_id == image.id)
        .order_by(CXRPrediction.created_at.desc())
        .first()
    )
    if not existing_prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generate analysis before requesting Grad-CAM")

    valid_labels = {label.label_code for label in existing_prediction.labels}
    if payload.target_label not in valid_labels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported target label")

    contents = _load_image_bytes(image)
    gradcam_service = GradCAMService(get_model_service())
    gradcam = gradcam_service.generate(contents, f".{image.original_format}", payload.target_label, str(existing_prediction.id))

    record = (
        db.query(GradCAMOutput)
        .filter(GradCAMOutput.prediction_id == existing_prediction.id, GradCAMOutput.label_code == payload.target_label)
        .first()
    )
    if record:
        record.heatmap_storage_key = gradcam["heatmap_storage_key"]
        record.overlay_storage_key = gradcam["overlay_storage_key"]
        record.target_layer = gradcam["target_layer"]
    else:
        record = GradCAMOutput(
            prediction_id=existing_prediction.id,
            label_code=payload.target_label,
            heatmap_storage_key=gradcam["heatmap_storage_key"],
            overlay_storage_key=gradcam["overlay_storage_key"],
            target_layer=gradcam["target_layer"],
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    create_audit_log(
        db,
        "generate_gradcam",
        "gradcam_output",
        record.id,
        actor_user_id=current_user.id,
        request=request,
        payload={"image_id": str(image.id), "target_label": payload.target_label},
    )
    return GradCAMGenerateResponse(
        image_id=image.id,
        target_label=payload.target_label,
        heatmap_url=storage.public_url("cxr-outputs", record.heatmap_storage_key),
        overlay_url=storage.public_url("cxr-outputs", record.overlay_storage_key),
    )


@router.get("/results/{prediction_id}", response_model=PredictionResultOut)
def get_prediction_result(
    prediction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PredictionResultOut:
    del current_user
    prediction = db.query(CXRPrediction).filter(CXRPrediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    return PredictionResultOut(
        prediction_id=prediction.id,
        image_id=prediction.image_id,
        model_version=prediction.model_version.version_name,
        risk_assessment={
            "overall_risk_level": prediction.overall_risk_level,
            "confidence_score": prediction.confidence_score,
            "uncertainty_flag": prediction.uncertainty_flag,
            "doctor_review_required": prediction.doctor_review_required,
        },
        triage_result=prediction.triage_result_json,
        ai_assisted_findings=[
            {
                "label": label.label_code,
                "risk_probability": label.risk_probability,
                "threshold": label.threshold_used,
                "risk_flag": label.risk_flag,
            }
            for label in prediction.labels
        ],
        doctor_review_suggestion=(
            "当前结果存在高风险或不确定性，建议医生优先复核。"
            if prediction.doctor_review_required
            else "建议在常规流程中由医生结合临床信息复核。"
        ),
        disclaimer=prediction.disclaimer,
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    predictions = (
        db.query(CXRPrediction)
        .join(CXRImage, CXRImage.id == CXRPrediction.image_id)
        .filter(CXRImage.uploader_id == current_user.id)
        .order_by(CXRPrediction.created_at.desc())
        .all()
    )
    items = [
        HistoryItemOut(
            prediction_id=prediction.id,
            image_id=prediction.image_id,
            uploaded_at=prediction.created_at,
            overall_risk_level=prediction.overall_risk_level,
            doctor_review_required=prediction.doctor_review_required,
            uncertainty_flag=prediction.uncertainty_flag,
            model_version=prediction.model_version.version_name,
        )
        for prediction in predictions
    ]
    return HistoryResponse(items=items, total=len(items))


@router.get("/{image_id}/heatmap", response_model=HeatmapResponse)
def get_heatmap(
    image_id: str,
    label: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HeatmapResponse:
    del current_user
    prediction = (
        db.query(CXRPrediction)
        .join(CXRImage, CXRImage.id == CXRPrediction.image_id)
        .filter(CXRPrediction.image_id == image_id)
        .order_by(CXRPrediction.created_at.desc())
        .first()
    )
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    heatmap = db.query(GradCAMOutput).filter(GradCAMOutput.prediction_id == prediction.id, GradCAMOutput.label_code == label).first()
    if not heatmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Heatmap not found")

    return HeatmapResponse(
        image_id=prediction.image_id,
        label=label,
        heatmap_url=storage.public_url("cxr-outputs", heatmap.heatmap_storage_key),
        overlay_url=storage.public_url("cxr-outputs", heatmap.overlay_storage_key),
    )


@router.delete("/{image_id}", response_model=DeleteImageResponse)
def delete_cxr_image(
    image_id: str,
    payload: DeleteImageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteImageResponse:
    result = direct_delete_image(db, image_id, payload, current_user)
    create_audit_log(
        db,
        "delete_image_direct",
        "cxr_image",
        result["image_id"],
        actor_user_id=current_user.id,
        request=request,
        payload={"image_id": image_id, "delete_mode": result["delete_mode"], "reason": payload.reason},
    )
    return DeleteImageResponse(**result)
