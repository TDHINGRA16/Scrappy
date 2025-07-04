"""add_unique_constraint_for_deduplication

Revision ID: 0c8b3cd35538
Revises: 9a8da4104e65
Create Date: 2025-06-23 23:39:20.676350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c8b3cd35538'
down_revision: Union[str, None] = '9a8da4104e65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to prevent duplicate scrape results."""
    # First, clean up existing duplicates
    op.execute("""
        DELETE FROM scrape_results
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM scrape_results
            GROUP BY job_id, name, address
        )
    """)
    
    # Add a composite unique constraint on job_id, name, and address
    op.create_unique_constraint(
        'uq_scrape_results_job_name_address',
        'scrape_results',
        ['job_id', 'name', 'address']
    )


def downgrade() -> None:
    """Remove the unique constraint."""
    op.drop_constraint(
        'uq_scrape_results_job_name_address',
        'scrape_results',
        type_='unique'
    )
