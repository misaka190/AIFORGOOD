from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.models.models import AuditLog, User
from app.schemas.schemas import AuditLogListResponse, AuditLogOut
from app.services.audit_service import get_audit_log, list_audit_logs


router = APIRouter(prefix="/audit", tags=["audit"])


def _to_response(item: AuditLog) -> AuditLogOut:
    return AuditLogOut.model_validate(item)


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="列出系统审计日志。支持按 action_type、resource_type、request_id、actor_user_id 过滤。仅 doctor/admin 可访问。",
    responses={200: {"description": "Audit logs returned"}, 403: {"description": "Insufficient permissions"}},
)
def get_audit_logs(
    action_type: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    actor_user_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    del current_user
    items = list_audit_logs(
        db,
        action_type=action_type,
        resource_type=resource_type,
        request_id=request_id,
        actor_user_id=actor_user_id,
        limit=limit,
    )
    return AuditLogListResponse(items=[_to_response(item) for item in items], total=len(items))


@router.get(
    "/logs/{audit_log_id}",
    response_model=AuditLogOut,
    summary="Get audit log detail",
    description="获取单条审计日志详情。仅 doctor/admin 可访问。",
    responses={200: {"description": "Audit log returned"}, 403: {"description": "Insufficient permissions"}, 404: {"description": "Audit log not found"}},
)
def get_audit_log_detail(
    audit_log_id: UUID,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db),
) -> AuditLogOut:
    del current_user
    item = get_audit_log(db, audit_log_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return _to_response(item)