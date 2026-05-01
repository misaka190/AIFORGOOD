"""deletion requests workflow table

Revision ID: 20260430_0004
Revises: 20260430_0003
Create Date: 2026-04-30 20:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260430_0004"
down_revision = "20260430_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deletion_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cxr_images.id"), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("delete_mode", sa.String(length=16), nullable=False),
        sa.Column("request_status", sa.String(length=32), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deletion_requests_approved_by", "deletion_requests", ["approved_by"], unique=False)
    op.create_index("ix_deletion_requests_delete_mode", "deletion_requests", ["delete_mode"], unique=False)
    op.create_index("ix_deletion_requests_image_id", "deletion_requests", ["image_id"], unique=False)
    op.create_index("ix_deletion_requests_request_status", "deletion_requests", ["request_status"], unique=False)
    op.create_index("ix_deletion_requests_requested_by", "deletion_requests", ["requested_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_deletion_requests_requested_by", table_name="deletion_requests")
    op.drop_index("ix_deletion_requests_request_status", table_name="deletion_requests")
    op.drop_index("ix_deletion_requests_image_id", table_name="deletion_requests")
    op.drop_index("ix_deletion_requests_delete_mode", table_name="deletion_requests")
    op.drop_index("ix_deletion_requests_approved_by", table_name="deletion_requests")
    op.drop_table("deletion_requests")