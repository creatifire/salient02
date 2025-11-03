"""rename_and_update_cost_fields_in_llm_requests

Revision ID: d5930048c917
Revises: 5cd8e16e070f
Create Date: 2025-10-11 15:58:10.400471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5930048c917'
down_revision: Union[str, Sequence[str], None] = '5cd8e16e070f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Rename cost fields and increase precision to NUMERIC(12, 8)."""
    
    # Rename columns and change type in one step
    op.alter_column('llm_requests', 'unit_cost_prompt',
                    new_column_name='prompt_cost',
                    type_=sa.NUMERIC(precision=12, scale=8),
                    existing_type=sa.NUMERIC(precision=10, scale=6),
                    existing_nullable=True)
    
    op.alter_column('llm_requests', 'unit_cost_completion',
                    new_column_name='completion_cost',
                    type_=sa.NUMERIC(precision=12, scale=8),
                    existing_type=sa.NUMERIC(precision=10, scale=6),
                    existing_nullable=True)
    
    op.alter_column('llm_requests', 'computed_cost',
                    new_column_name='total_cost',
                    type_=sa.NUMERIC(precision=12, scale=8),
                    existing_type=sa.NUMERIC(precision=10, scale=6),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema: Revert cost field names and precision."""
    
    # Revert column names and types
    op.alter_column('llm_requests', 'prompt_cost',
                    new_column_name='unit_cost_prompt',
                    type_=sa.NUMERIC(precision=10, scale=6),
                    existing_type=sa.NUMERIC(precision=12, scale=8),
                    existing_nullable=True)
    
    op.alter_column('llm_requests', 'completion_cost',
                    new_column_name='unit_cost_completion',
                    type_=sa.NUMERIC(precision=10, scale=6),
                    existing_type=sa.NUMERIC(precision=12, scale=8),
                    existing_nullable=True)
    
    op.alter_column('llm_requests', 'total_cost',
                    new_column_name='computed_cost',
                    type_=sa.NUMERIC(precision=10, scale=6),
                    existing_type=sa.NUMERIC(precision=12, scale=8),
                    existing_nullable=True)
