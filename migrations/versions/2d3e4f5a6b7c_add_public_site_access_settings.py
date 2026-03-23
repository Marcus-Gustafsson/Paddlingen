"""add public site access settings

Revision ID: 2d3e4f5a6b7c
Revises: 7baf30d0c9e1
Create Date: 2026-03-21 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "2d3e4f5a6b7c"
down_revision = "7baf30d0c9e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the table that stores the shared public-site password hash."""

    op.create_table(
        "public_site_access_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Remove the table that stores the shared public-site password hash."""

    op.drop_table("public_site_access_settings")
