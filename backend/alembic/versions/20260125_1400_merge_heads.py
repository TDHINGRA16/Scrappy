"""Merge migration to resolve multiple heads

Revision ID: 20260125_1400_merge_heads
Revises: add_user_place_query_normalized, add_scrape_session_cursors
Create Date: 2026-01-25 14:00:00

This migration merges two divergent heads introduced by a stub
migration and the real feature migration. It performs no schema
changes; its sole purpose is to unify the Alembic revision graph.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260125_1400_merge_heads'
down_revision = (
    'add_user_place_query_normalized',
    'add_scrape_session_cursors',
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No schema changes; merge two heads into a single linear history."""
    print("ℹ️ Merge migration applied: unified Alembic heads")


def downgrade() -> None:
    """No-op downgrade for merge migration."""
    print("ℹ️ Merge migration downgraded (no schema changes)")
