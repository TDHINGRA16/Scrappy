"""Fix user_integrations.user_id type to UUID

Revision ID: fix_user_id_type_uuid
Revises: 20260122_2200
Create Date: 2026-01-23 15:36:00

This migration fixes the type mismatch between user.id (UUID) and 
user_integrations.user_id (VARCHAR) by converting user_id back to UUID.
"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'fix_user_id_type_uuid'
down_revision = '20260122_2200'
branch_labels = None
depends_on = None


def upgrade():
    """Convert user_integrations.user_id from VARCHAR to UUID."""
    connection = op.get_bind()
    # Check the actual type of users.id to decide if conversion is safe
    try:
        res = connection.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'user' AND column_name = 'id'
        """)).fetchone()
        user_id_type = res[0] if res else None
    except Exception:
        user_id_type = None

    # If users.id is already UUID, proceed with conversion
    if user_id_type and user_id_type.lower() == 'uuid':
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
    else:
        # users.id is not UUID (likely BetterAuth string IDs). Skip conversion.
        print("ℹ️ Skipping conversion: users.id is not UUID (no action taken)")


def downgrade():
    """Revert back to VARCHAR (not recommended)."""
    connection = op.get_bind()
    # Only attempt to revert if user.id is UUID (otherwise no-op)
    try:
        res = connection.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'user' AND column_name = 'id'
        """)).fetchone()
        user_id_type = res[0] if res else None
    except Exception:
        user_id_type = None

    if user_id_type and user_id_type.lower() == 'uuid':
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
    else:
        print("ℹ️ Downgrade skipped: users.id is not UUID (no action taken)")
