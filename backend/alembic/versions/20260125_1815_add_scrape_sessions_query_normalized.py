"""Add query_normalized column to scrape_sessions

Revision ID: 20260125_1815_add_scrape_sessions_query_normalized
Revises: 20260125_1400_merge_heads
Create Date: 2026-01-25 18:15:00

This migration adds the `query_normalized` column to `scrape_sessions`
and an index for faster lookups. It is safe to run multiple times
because it checks for existing column/index before creating them.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '20260125_1815'
down_revision = '20260125_1400_merge_heads'
branch_labels = None
depends_on = None


def _column_exists(connection, table_name: str, column_name: str) -> bool:
    res = connection.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = :table AND column_name = :col
            )
        """),
        {"table": table_name, "col": column_name},
    ).scalar()
    return bool(res)


def _index_exists(connection, index_name: str) -> bool:
    res = connection.execute(
        text("SELECT EXISTS (SELECT 1 FROM pg_class WHERE relname = :idx)"),
        {"idx": index_name},
    ).scalar()
    return bool(res)


def upgrade():
    conn = op.get_bind()

    # Add column if missing
    if not _column_exists(conn, 'scrape_sessions', 'query_normalized'):
        op.add_column('scrape_sessions', sa.Column('query_normalized', sa.String(500), nullable=True))
        print("✅ Added column `query_normalized` to `scrape_sessions`")
    else:
        print("ℹ️ Column `query_normalized` already exists on `scrape_sessions`")

    # Create index if missing
    idx_name = 'idx_scrape_sessions_query_normalized'
    if not _index_exists(conn, idx_name):
        op.create_index(idx_name, 'scrape_sessions', ['query_normalized'], unique=False)
        print(f"✅ Created index {idx_name}")
    else:
        print(f"ℹ️ Index {idx_name} already exists")


def downgrade():
    conn = op.get_bind()

    idx_name = 'idx_scrape_sessions_query_normalized'
    if _index_exists(conn, idx_name):
        try:
            op.drop_index(idx_name, table_name='scrape_sessions')
            print(f"🔻 Dropped index {idx_name}")
        except Exception:
            pass

    if _column_exists(conn, 'scrape_sessions', 'query_normalized'):
        try:
            op.drop_column('scrape_sessions', 'query_normalized')
            print("🔻 Dropped column `query_normalized` from `scrape_sessions`")
        except Exception:
            pass
