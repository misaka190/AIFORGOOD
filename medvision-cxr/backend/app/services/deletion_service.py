from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import CXRImage, DeletionRequest, GradCAMOutput, User
from app.schemas.schemas import DeleteImageRequest, DeletionDecisionRequest, DeletionRequestCreate
from app.utils.storage import storage


VALID_DELETE_MODES = {"soft", "hard"}
VALID_DECISION_ACTIONS = {"approve", "reject"}
PENDING_STATUS = "pending"
APPROVED_STATUS = "approved"
REJECTED_STATUS = "rejected"
COMPLETED_STATUS = "completed"


def _ensure_image_access(image: CXRImage, current_user: User) -> None:
    role_code = current_user.role.role_code
    if role_code in {"admin", "doctor"}:
        return
    if image.uploader_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only request deletion for your own images")


def _validate_delete_mode(delete_mode: str) -> str:
    normalized = delete_mode.lower()
    if normalized not in VALID_DELETE_MODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="delete_mode must be 'soft' or 'hard'")
    return normalized


def _apply_delete_mode(db: Session, image: CXRImage, delete_mode: str) -> None:
    image.is_deleted = True
    if delete_mode != "hard":
        return

    storage.delete_object("cxr-raw", image.storage_key)
    gradcams = (
        db.query(GradCAMOutput)
        .join(GradCAMOutput.prediction)
        .filter(GradCAMOutput.prediction.has(image_id=image.id))
        .all()
    )
    for gradcam in gradcams:
        storage.delete_object("cxr-outputs", gradcam.heatmap_storage_key)
        storage.delete_object("cxr-outputs", gradcam.overlay_storage_key)


def direct_delete_image(db: Session, image_id: str, payload: DeleteImageRequest, current_user: User) -> dict:
    delete_mode = _validate_delete_mode(payload.delete_mode)
    image = db.query(CXRImage).filter(CXRImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    _ensure_image_access(image, current_user)
    if image.is_deleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Image has already been deleted")

    completed_at = datetime.now(timezone.utc)
    _apply_delete_mode(db, image, delete_mode)
    db.commit()
    db.refresh(image)
    return {
        "image_id": image.id,
        "request_status": COMPLETED_STATUS,
        "delete_mode": delete_mode,
        "deleted_by": current_user.id,
        "completed_at": completed_at,
        "reason": payload.reason,
    }


def create_deletion_request(db: Session, payload: DeletionRequestCreate, current_user: User) -> DeletionRequest:
    delete_mode = _validate_delete_mode(payload.delete_mode)
    image = db.query(CXRImage).filter(CXRImage.id == payload.image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    _ensure_image_access(image, current_user)

    existing_pending = (
        db.query(DeletionRequest)
        .filter(DeletionRequest.image_id == image.id, DeletionRequest.request_status == PENDING_STATUS)
        .first()
    )
    if existing_pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A pending deletion request already exists for this image")

    deletion_request = DeletionRequest(
        image_id=image.id,
        requested_by=current_user.id,
        delete_mode=delete_mode,
        deletion_reason=payload.reason,
        request_status=PENDING_STATUS,
    )
    db.add(deletion_request)
    db.commit()
    db.refresh(deletion_request)
    return deletion_request


def list_deletion_requests(db: Session, current_user: User, request_status: str | None = None) -> list[DeletionRequest]:
    query = db.query(DeletionRequest)
    if current_user.role.role_code not in {"admin", "doctor"}:
        query = query.filter(DeletionRequest.requested_by == current_user.id)
    if request_status:
        query = query.filter(DeletionRequest.request_status == request_status.lower())
    return query.order_by(DeletionRequest.created_at.desc()).all()


def decide_deletion_request(
    db: Session,
    deletion_request_id: str,
    payload: DeletionDecisionRequest,
    approver: User,
) -> DeletionRequest:
    action = payload.approval_action.lower()
    if action not in VALID_DECISION_ACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="approval_action must be 'approve' or 'reject'")
    if action == "reject" and not payload.rejection_reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rejection_reason is required when rejecting a deletion request")

    deletion_request = db.query(DeletionRequest).filter(DeletionRequest.id == deletion_request_id).first()
    if not deletion_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deletion request not found")
    if deletion_request.request_status != PENDING_STATUS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Deletion request has already been processed")

    image = db.query(CXRImage).filter(CXRImage.id == deletion_request.image_id).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    deletion_request.approved_by = approver.id
    deletion_request.approval_note = payload.approval_note
    if action == "reject":
        deletion_request.request_status = REJECTED_STATUS
        deletion_request.rejection_reason = payload.rejection_reason
        db.commit()
        db.refresh(deletion_request)
        return deletion_request

    deletion_request.request_status = APPROVED_STATUS
    deletion_request.rejection_reason = None
    deletion_request.completed_at = datetime.now(timezone.utc)

    _apply_delete_mode(db, image, deletion_request.delete_mode)

    deletion_request.request_status = COMPLETED_STATUS
    db.commit()
    db.refresh(deletion_request)
    return deletion_request