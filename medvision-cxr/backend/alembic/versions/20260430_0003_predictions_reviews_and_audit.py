"""predictions reviews and audit tables

Revision ID: 20260430_0003
Revises: 20260430_0002
Create Date: 2026-04-30 20:20:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260430_0003"
down_revision = "20260430_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cxr_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cxr_images.id"), nullable=False),
        sa.Column("model_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("job_status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("overall_risk_level", sa.String(length=16), nullable=False),
        sa.Column("uncertainty_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("doctor_review_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("raw_scores_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("triage_result_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cxr_predictions_doctor_review_required", "cxr_predictions", ["doctor_review_required"], unique=False)
    op.create_index("ix_cxr_predictions_image_id", "cxr_predictions", ["image_id"], unique=False)
    op.create_index("ix_cxr_predictions_job_status", "cxr_predictions", ["job_status"], unique=False)
    op.create_index("ix_cxr_predictions_model_version_id", "cxr_predictions", ["model_version_id"], unique=False)
    op.create_index("ix_cxr_predictions_overall_risk_level", "cxr_predictions", ["overall_risk_level"], unique=False)
    op.create_index("ix_cxr_predictions_uncertainty_flag", "cxr_predictions", ["uncertainty_flag"], unique=False)

    op.create_table(
        "prediction_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cxr_predictions.id"), nullable=False),
        sa.Column("label_code", sa.String(length=64), nullable=False),
        sa.Column("risk_probability", sa.Float(), nullable=False),
        sa.Column("threshold_used", sa.Float(), nullable=False),
        sa.Column("risk_flag", sa.Boolean(), nullable=False),
        sa.Column("calibrated_score", sa.Float(), nullable=True),
        sa.Column("finding_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("prediction_id", "label_code", name="uq_prediction_label_code"),
    )
    op.create_index("ix_prediction_labels_prediction_id", "prediction_labels", ["prediction_id"], unique=False)
    op.create_index("ix_prediction_labels_risk_flag", "prediction_labels", ["risk_flag"], unique=False)

    op.create_table(
        "gradcam_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cxr_predictions.id"), nullable=False),
        sa.Column("label_code", sa.String(length=64), nullable=False),
        sa.Column("heatmap_storage_key", sa.String(length=255), nullable=False),
        sa.Column("overlay_storage_key", sa.String(length=255), nullable=False),
        sa.Column("target_layer", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("prediction_id", "label_code", name="uq_gradcam_prediction_label"),
    )
    op.create_index("ix_gradcam_outputs_heatmap_storage_key", "gradcam_outputs", ["heatmap_storage_key"], unique=True)
    op.create_index("ix_gradcam_outputs_overlay_storage_key", "gradcam_outputs", ["overlay_storage_key"], unique=True)
    op.create_index("ix_gradcam_outputs_prediction_id", "gradcam_outputs", ["prediction_id"], unique=False)

    op.create_table(
        "doctor_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cxr_predictions.id"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("review_priority", sa.String(length=16), nullable=False),
        sa.Column("review_action", sa.String(length=32), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("prediction_id", name="uq_doctor_reviews_prediction_id"),
    )
    op.create_index("ix_doctor_reviews_prediction_id", "doctor_reviews", ["prediction_id"], unique=True)
    op.create_index("ix_doctor_reviews_review_priority", "doctor_reviews", ["review_priority"], unique=False)
    op.create_index("ix_doctor_reviews_review_status", "doctor_reviews", ["review_status"], unique=False)
    op.create_index("ix_doctor_reviews_reviewed_at", "doctor_reviews", ["reviewed_at"], unique=False)
    op.create_index("ix_doctor_reviews_reviewer_id", "doctor_reviews", ["reviewer_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("event_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_action_type", "audit_logs", ["action_type"], unique=False)
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False)
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"], unique=False)
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_type", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_doctor_reviews_reviewer_id", table_name="doctor_reviews")
    op.drop_index("ix_doctor_reviews_reviewed_at", table_name="doctor_reviews")
    op.drop_index("ix_doctor_reviews_review_status", table_name="doctor_reviews")
    op.drop_index("ix_doctor_reviews_review_priority", table_name="doctor_reviews")
    op.drop_index("ix_doctor_reviews_prediction_id", table_name="doctor_reviews")
    op.drop_table("doctor_reviews")

    op.drop_index("ix_gradcam_outputs_prediction_id", table_name="gradcam_outputs")
    op.drop_index("ix_gradcam_outputs_overlay_storage_key", table_name="gradcam_outputs")
    op.drop_index("ix_gradcam_outputs_heatmap_storage_key", table_name="gradcam_outputs")
    op.drop_table("gradcam_outputs")

    op.drop_index("ix_prediction_labels_risk_flag", table_name="prediction_labels")
    op.drop_index("ix_prediction_labels_prediction_id", table_name="prediction_labels")
    op.drop_table("prediction_labels")

    op.drop_index("ix_cxr_predictions_uncertainty_flag", table_name="cxr_predictions")
    op.drop_index("ix_cxr_predictions_overall_risk_level", table_name="cxr_predictions")
    op.drop_index("ix_cxr_predictions_model_version_id", table_name="cxr_predictions")
    op.drop_index("ix_cxr_predictions_job_status", table_name="cxr_predictions")
    op.drop_index("ix_cxr_predictions_image_id", table_name="cxr_predictions")
    op.drop_index("ix_cxr_predictions_doctor_review_required", table_name="cxr_predictions")
    op.drop_table("cxr_predictions")