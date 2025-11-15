"""add_assembled_prompt_to_llm_requests

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2025-11-15 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add assembled_prompt TEXT column to llm_requests table for complete system prompt debugging."""
    
    # Add assembled_prompt column
    op.add_column('llm_requests', 
                  sa.Column('assembled_prompt', 
                           sa.Text(), 
                           nullable=True,
                           comment='Complete system prompt as sent to LLM (after all module concatenation)'))
    
    # Add partial index for performance (only index non-null values)
    op.create_index(
        'idx_llm_requests_assembled_prompt_not_null',
        'llm_requests',
        ['id'],
        postgresql_where=sa.text('assembled_prompt IS NOT NULL')
    )


def downgrade() -> None:
    """Remove assembled_prompt column and its index from llm_requests table."""
    
    op.drop_index('idx_llm_requests_assembled_prompt_not_null', table_name='llm_requests')
    op.drop_column('llm_requests', 'assembled_prompt')

