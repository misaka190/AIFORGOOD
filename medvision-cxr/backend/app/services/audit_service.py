from __future__ import annotations

import hashlib
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.models import AuditLog


def _hash_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()


def create_audit_log(
    db: Session,
    action_type: str,
    resource_type: str,
    resource_id: UUID | None,
    actor_user_id: UUID | None = None,
    request: Request | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    sanitized_payload = payload or {}
    sanitized_payload.pop("password", None)
    sanitized_payload.pop("patient_name", None)
    sanitized_payload.pop("patient_id", None)

    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=getattr(request.state, "request_id", None) if request else None,
        ip_hash=_hash_ip(request.client.host if request and request.client else None),
        user_agent=request.headers.get("user-agent") if request else None,
        event_payload=sanitized_payload,
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def list_audit_logs(
    db: Session,
    *,
    action_type: str | None = None,
    resource_type: str | None = None,
    request_id: str | None = None,
    actor_user_id: UUID | None = None,
    limit: int = 50,
) -> list[AuditLog]:
    query: Select[tuple[AuditLog]] = select(AuditLog)

    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if request_id:
        query = query.where(AuditLog.request_id == request_id)
    if actor_user_id:
        query = query.where(AuditLog.actor_user_id == actor_user_id)

    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    return list(db.scalars(query).all())


def get_audit_log(db: Session, audit_log_id: UUID) -> AuditLog | None:
    query: Select[tuple[AuditLog]] = select(AuditLog).where(AuditLog.id == audit_log_id)
    return db.scalars(query).first()
