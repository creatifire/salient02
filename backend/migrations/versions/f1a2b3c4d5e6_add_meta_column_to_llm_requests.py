"""add_meta_column_to_llm_requests

Revision ID: f1a2b3c4d5e6
Revises: e9e83012d6b4
Create Date: 2025-11-13 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e9e83012d6b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add meta JSONB column to llm_requests table for prompt breakdown and debugging metadata."""
    
    op.add_column('llm_requests', 
                  sa.Column('meta', 
                           postgresql.JSONB(astext_type=sa.Text()), 
                           nullable=True,
                           comment='Extensible metadata including prompt breakdown for debugging'))


def downgrade() -> None:
    """Remove meta column from llm_requests table."""
    
    op.drop_column('llm_requests', 'meta')

