"""Stub migration to satisfy missing revision reference

Revision ID: add_user_place_query_normalized
Revises: 20260122_2200
Create Date: 2026-01-23 00:00:00

This is a no-op stub migration added to satisfy a missing
revision reference that some environments may still point to.
It intentionally performs no schema changes.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'add_user_place_query_normalized'
down_revision = '20260122_2200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No schema changes; placeholder to satisfy revision chain."""
    print("ℹ️ Stub migration add_user_place_query_normalized applied (no-op)")


def downgrade() -> None:
    """No-op downgrade for stub migration."""
    print("ℹ️ Stub migration add_user_place_query_normalized downgraded (no-op)")
