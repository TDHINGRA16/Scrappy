"""Fix user_integrations.user_id type to UUID

Revision ID: fix_user_id_type_uuid
Revises: add_user_places_dedup_index
Create Date: 2026-01-23 15:36:00

This migration fixes the type mismatch between user.id (UUID) and 
user_integrations.user_id (VARCHAR) by converting user_id back to UUID.
"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'fix_user_id_type_uuid'
down_revision = 'add_user_places_dedup_index'
branch_labels = None
depends_on = None


def upgrade():
    """Convert user_integrations.user_id from VARCHAR to UUID."""
    connection = op.get_bind()
    
    # Drop the existing foreign key constraint
    connection.execute(text("""
        ALTER TABLE user_integrations 
        DROP CONSTRAINT IF EXISTS user_integrations_user_id_fkey;
    """))
    
    # Convert user_id column from VARCHAR to UUID
    # This assumes existing data is valid UUID strings
    connection.execute(text("""
        ALTER TABLE user_integrations 
        ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
    """))
    
    # Recreate the foreign key constraint with correct types
    connection.execute(text("""
        ALTER TABLE user_integrations 
        ADD CONSTRAINT user_integrations_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;
    """))
    
    print("✅ Fixed user_integrations.user_id type to UUID")


def downgrade():
    """Revert back to VARCHAR (not recommended)."""
    connection = op.get_bind()
    
    connection.execute(text("""
        ALTER TABLE user_integrations 
        DROP CONSTRAINT IF EXISTS user_integrations_user_id_fkey;
    """))
    
    connection.execute(text("""
        ALTER TABLE user_integrations 
        ALTER COLUMN user_id TYPE VARCHAR USING user_id::VARCHAR;
    """))
    
    connection.execute(text("""
        ALTER TABLE user_integrations 
        ADD CONSTRAINT user_integrations_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;
    """))
    
    print("🔻 Reverted user_integrations.user_id back to VARCHAR")
