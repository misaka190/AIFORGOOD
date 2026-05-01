import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    role_name: Mapped[str] = mapped_column(String(128), nullable=False)
    permissions_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    role: Mapped[Role] = relationship(back_populates="users")
    cxr_images: Mapped[list["CXRImage"]] = relationship(back_populates="uploader")
    deletion_requests: Mapped[list["DeletionRequest"]] = relationship(
        foreign_keys="DeletionRequest.requested_by", back_populates="requester"
    )
    approved_deletions: Mapped[list["DeletionRequest"]] = relationship(
        foreign_keys="DeletionRequest.approved_by", back_populates="approver"
    )


class ConsentRecord(Base, TimestampMixin):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    consent_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consent_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class CXRImage(Base, TimestampMixin):
    __tablename__ = "cxr_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploader_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    consent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("consent_records.id"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_format: Mapped[str] = mapped_column(String(32), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    modality: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    quality_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    uploader: Mapped[User] = relationship(back_populates="cxr_images")
    predictions: Mapped[list["CXRPrediction"]] = relationship(back_populates="image")
    deletion_requests: Mapped[list["DeletionRequest"]] = relationship(back_populates="image")


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    model_family: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    dataset_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predictions: Mapped[list["CXRPrediction"]] = relationship(back_populates="model_version")


class CXRPrediction(Base, TimestampMixin):
    __tablename__ = "cxr_predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cxr_images.id"), nullable=False, index=True)
    model_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False, index=True)
    job_status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False, index=True)
    overall_risk_level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    uncertainty_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    doctor_review_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    raw_scores_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    triage_result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    image: Mapped[CXRImage] = relationship(back_populates="predictions")
    model_version: Mapped[ModelVersion] = relationship(back_populates="predictions")
    labels: Mapped[list["PredictionLabel"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")
    gradcam_outputs: Mapped[list["GradCAMOutput"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")
    doctor_review: Mapped["DoctorReview | None"] = relationship(back_populates="prediction", uselist=False)


class PredictionLabel(Base, TimestampMixin):
    __tablename__ = "prediction_labels"
    __table_args__ = (UniqueConstraint("prediction_id", "label_code", name="uq_prediction_label_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cxr_predictions.id"), nullable=False, index=True)
    label_code: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_probability: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)
    risk_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    calibrated_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    finding_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    prediction: Mapped[CXRPrediction] = relationship(back_populates="labels")


class GradCAMOutput(Base, TimestampMixin):
    __tablename__ = "gradcam_outputs"
    __table_args__ = (UniqueConstraint("prediction_id", "label_code", name="uq_gradcam_prediction_label"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cxr_predictions.id"), nullable=False, index=True)
    label_code: Mapped[str] = mapped_column(String(64), nullable=False)
    heatmap_storage_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    overlay_storage_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    target_layer: Mapped[str] = mapped_column(String(128), nullable=False)

    prediction: Mapped[CXRPrediction] = relationship(back_populates="gradcam_outputs")


class DoctorReview(Base, TimestampMixin):
    __tablename__ = "doctor_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cxr_predictions.id"), nullable=False, unique=True, index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    review_priority: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    review_action: Mapped[str] = mapped_column(String(32), nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    prediction: Mapped[CXRPrediction] = relationship(back_populates="doctor_review")


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class DeletionRequest(Base, TimestampMixin):
    __tablename__ = "deletion_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cxr_images.id"), nullable=False, index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    delete_mode: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    deletion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    approval_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    image: Mapped[CXRImage] = relationship(back_populates="deletion_requests")
    requester: Mapped[User] = relationship(foreign_keys=[requested_by], back_populates="deletion_requests")
    approver: Mapped[User | None] = relationship(foreign_keys=[approved_by], back_populates="approved_deletions")
