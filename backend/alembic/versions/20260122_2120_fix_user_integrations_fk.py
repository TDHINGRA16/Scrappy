"""fix user_integrations foreign key to reference user table

Revision ID: 20260122_2120
Revises: 
Create Date: 2026-01-22 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '20260122_2120'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix user_integrations.user_id to reference 'user' table (Better Auth)
    instead of non-existent 'users' table.
    """
    connection = op.get_bind()
    
    # Drop existing FK constraint if any (use raw SQL to handle non-existence gracefully)
    connection.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'user_integrations_user_id_fkey' 
                AND table_name = 'user_integrations'
            ) THEN
                ALTER TABLE user_integrations DROP CONSTRAINT user_integrations_user_id_fkey;
            END IF;
        END $$;
    """))
    
    # Change user_id column type from UUID to VARCHAR if needed
    connection.execute(text("""
        ALTER TABLE user_integrations ALTER COLUMN user_id TYPE VARCHAR USING user_id::VARCHAR;
    """))
    
    # Create foreign key to 'user' table
    connection.execute(text("""
        ALTER TABLE user_integrations 
        ADD CONSTRAINT user_integrations_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE;
    """))


def downgrade() -> None:
    """Revert changes."""
    connection = op.get_bind()
    connection.execute(text("""
        ALTER TABLE user_integrations DROP CONSTRAINT IF EXISTS user_integrations_user_id_fkey;
    """))
    connection.execute(text("""
        ALTER TABLE user_integrations ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
    """))
