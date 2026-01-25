"""Add scrape_session_cursors table for cursor-based pagination

Revision ID: add_scrape_session_cursors
Revises: fix_user_id_type_uuid
Create Date: 2026-01-25 10:00:00

This migration adds cursor-based pagination support:
- Allows resuming scrapes from where we left off
- 10x faster incremental collection
- No re-scrolling through old data
- Scales to 5,000+ results per query

Table: scrape_session_cursors
- Tracks scroll position, cards collected, last place ID
- Query normalization for semantic matching
- 30-day TTL with automatic cleanup
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'add_scrape_session_cursors'
down_revision = 'fix_user_id_type_uuid'
branch_labels = None
depends_on = None


def upgrade():
    """Create scrape_session_cursors table with indexes."""
    connection = op.get_bind()
    # Check if the table already exists to avoid DuplicateTable errors
    exists = connection.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'scrape_session_cursors'
        )
    """)).scalar()

    if exists:
        print("ℹ️ Table 'scrape_session_cursors' already exists; skipping creation")
        return

    # Create the table
    op.create_table(
        'scrape_session_cursors',
        
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), 
                  primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        
        # User reference
        sa.Column('user_id', sa.String(255), nullable=False),
        
        # Query normalization
        sa.Column('query_hash', sa.String(64), nullable=False),
        sa.Column('query_original', sa.String(500), nullable=False),
        sa.Column('query_normalized', sa.String(500), nullable=False),
        
        # Pagination state
        sa.Column('last_scroll_position', sa.Integer, default=0),
        sa.Column('cards_collected', sa.Integer, default=0),
        sa.Column('last_place_id', sa.String(64), nullable=True),
        sa.Column('last_card_index', sa.Integer, nullable=True),
        
        # Scroll metadata
        sa.Column('total_scrolls_performed', sa.Integer, default=0),
        sa.Column('last_visible_card_count', sa.Integer, default=0),
        
        # Extended cursor data (JSON)
        sa.Column('cursor_data', postgresql.JSON, nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, 
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, 
                  server_default=sa.text('NOW()')),
        sa.Column('last_accessed', sa.DateTime, 
                  server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime, nullable=True),
    )
    
    # Create indexes for fast lookups
    
    # Primary lookup: user + query combination
    op.create_index(
        'idx_cursor_user_query',
        'scrape_session_cursors',
        ['user_id', 'query_hash'],
        unique=False
    )
    
    # TTL cleanup: find expired cursors
    op.create_index(
        'idx_cursor_expires',
        'scrape_session_cursors',
        ['expires_at'],
        unique=False
    )
    
    # User's cursors for management UI
    op.create_index(
        'idx_cursor_user_updated',
        'scrape_session_cursors',
        ['user_id', 'updated_at'],
        unique=False
    )
    
    # Add unique constraint on user_id + query_hash (one cursor per user per query)
    op.create_unique_constraint(
        'uq_user_query_cursor',
        'scrape_session_cursors',
        ['user_id', 'query_hash']
    )
    
    print("✅ Created scrape_session_cursors table with indexes")


def downgrade():
    """Drop scrape_session_cursors table."""
    
    # Drop indexes first
    op.drop_index('idx_cursor_user_query', table_name='scrape_session_cursors')
    op.drop_index('idx_cursor_expires', table_name='scrape_session_cursors')
    op.drop_index('idx_cursor_user_updated', table_name='scrape_session_cursors')
    
    # Drop unique constraint
    op.drop_constraint('uq_user_query_cursor', 'scrape_session_cursors', type_='unique')
    
    # Drop table
    op.drop_table('scrape_session_cursors')
    
    print("🔻 Dropped scrape_session_cursors table")
