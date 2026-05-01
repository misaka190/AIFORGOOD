"""add deletion request metadata fields

Revision ID: 20260430_0005
Revises: 20260430_0004
Create Date: 2026-04-30 21:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_0005"
down_revision = "20260430_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("deletion_requests", sa.Column("deletion_reason", sa.Text(), nullable=True))
    op.add_column("deletion_requests", sa.Column("approval_note", sa.Text(), nullable=True))
    op.add_column("deletion_requests", sa.Column("rejection_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("deletion_requests", "rejection_reason")
    op.drop_column("deletion_requests", "approval_note")
    op.drop_column("deletion_requests", "deletion_reason")