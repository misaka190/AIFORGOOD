from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.models.models import DeletionRequest, User
from app.schemas.schemas import (
    DeletionDecisionRequest,
    DeletionRequestCreate,
    DeletionRequestListResponse,
    DeletionRequestOut,
)
from app.services.audit_service import create_audit_log
from app.services.deletion_service import create_deletion_request, decide_deletion_request, list_deletion_requests


router = APIRouter(prefix="/deletions", tags=["deletions"])


def _to_response(item: DeletionRequest) -> DeletionRequestOut:
    return DeletionRequestOut(
        request_id=item.id,
        image_id=item.image_id,
        delete_mode=item.delete_mode,
        deletion_reason=item.deletion_reason,
        request_status=item.request_status,
        requested_by=item.requested_by,
        approved_by=item.approved_by,
        approval_note=item.approval_note,
        rejection_reason=item.rejection_reason,
        completed_at=item.completed_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post(
    "/requests",
    response_model=DeletionRequestOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit deletion request",
    description="提交胸片删除请求。普通用户仅可为自己上传的影像发起删除；doctor/admin 也可代表业务流程发起。",
    responses={
        201: {"description": "Deletion request created"},
        400: {"description": "Invalid delete mode or payload"},
        403: {"description": "User cannot request deletion for this image"},
        404: {"description": "Image not found"},
        409: {"description": "Pending deletion request already exists"},
    },
)
def submit_deletion_request(
    payload: DeletionRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeletionRequestOut:
    deletion_request = create_deletion_request(db, payload, current_user)
    create_audit_log(
        db,
        "request_deletion",
        "deletion_request",
        deletion_request.id,
        actor_user_id=current_user.id,
        request=request,
        payload={"image_id": str(payload.image_id), "delete_mode": payload.delete_mode, "reason": payload.reason},
    )
    return _to_response(deletion_request)


@router.get(
    "/requests",
    response_model=DeletionRequestListResponse,
    summary="List deletion requests",
    description="列出删除请求。doctor/admin 可查看全量请求，普通用户仅能查看自己发起的请求。",
    responses={200: {"description": "Deletion requests returned"}},
)
def get_deletion_requests(
    request_status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeletionRequestListResponse:
    items = list_deletion_requests(db, current_user, request_status=request_status)
    return DeletionRequestListResponse(items=[_to_response(item) for item in items], total=len(items))


@router.post(
    "/requests/{deletion_request_id}/decision",
    response_model=DeletionRequestOut,
    summary="Approve or reject deletion request",
    description="由 doctor/admin 审批删除请求。approve 会执行删除流程，reject 会保留拒绝原因与审批备注。",
    responses={
        200: {"description": "Deletion request processed"},
        400: {"description": "Invalid action or missing rejection_reason"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Deletion request or image not found"},
        409: {"description": "Deletion request already processed"},
    },
)
def review_deletion_request(
    deletion_request_id: str,
    payload: DeletionDecisionRequest,
    request: Request,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db),
) -> DeletionRequestOut:
    deletion_request = decide_deletion_request(db, deletion_request_id, payload, current_user)
    create_audit_log(
        db,
        f"deletion_{payload.approval_action.lower()}",
        "deletion_request",
        deletion_request.id,
        actor_user_id=current_user.id,
        request=request,
        payload={
            "image_id": str(deletion_request.image_id),
            "request_status": deletion_request.request_status,
            "approval_note": payload.approval_note,
            "rejection_reason": payload.rejection_reason,
        },
    )
    return _to_response(deletion_request)