"""images and model versions

Revision ID: 20260430_0002
Revises: 20260430_0001
Create Date: 2026-04-30 20:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260430_0002"
down_revision = "20260430_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cxr_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("consent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consent_records.id"), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_format", sa.String(length=32), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("modality", sa.String(length=32), nullable=True),
        sa.Column("quality_flags", sa.JSON(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cxr_images_consent_id", "cxr_images", ["consent_id"], unique=False)
    op.create_index("ix_cxr_images_is_deleted", "cxr_images", ["is_deleted"], unique=False)
    op.create_index("ix_cxr_images_modality", "cxr_images", ["modality"], unique=False)
    op.create_index("ix_cxr_images_storage_key", "cxr_images", ["storage_key"], unique=True)
    op.create_index("ix_cxr_images_uploader_id", "cxr_images", ["uploader_id"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("version_name", sa.String(length=128), nullable=False),
        sa.Column("model_family", sa.String(length=128), nullable=False),
        sa.Column("dataset_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("metrics_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("artifact_uri", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_model_versions_is_active", "model_versions", ["is_active"], unique=False)
    op.create_index("ix_model_versions_model_family", "model_versions", ["model_family"], unique=False)
    op.create_index("ix_model_versions_version_name", "model_versions", ["version_name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_model_versions_version_name", table_name="model_versions")
    op.drop_index("ix_model_versions_model_family", table_name="model_versions")
    op.drop_index("ix_model_versions_is_active", table_name="model_versions")
    op.drop_table("model_versions")

    op.drop_index("ix_cxr_images_uploader_id", table_name="cxr_images")
    op.drop_index("ix_cxr_images_storage_key", table_name="cxr_images")
    op.drop_index("ix_cxr_images_modality", table_name="cxr_images")
    op.drop_index("ix_cxr_images_is_deleted", table_name="cxr_images")
    op.drop_index("ix_cxr_images_consent_id", table_name="cxr_images")
    op.drop_table("cxr_images")