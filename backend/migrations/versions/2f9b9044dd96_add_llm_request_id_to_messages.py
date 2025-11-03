"""add_llm_request_id_to_messages

Revision ID: 2f9b9044dd96
Revises: d5930048c917
Create Date: 2025-10-18 19:05:27.062636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f9b9044dd96'
down_revision: Union[str, Sequence[str], None] = 'd5930048c917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add llm_request_id to messages table for cost attribution and debugging."""
    # Add llm_request_id column (nullable FK to llm_requests)
    op.add_column(
        'messages',
        sa.Column('llm_request_id', sa.UUID(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_messages_llm_request_id',
        'messages',
        'llm_requests',
        ['llm_request_id'],
        ['id'],
        ondelete='SET NULL'  # If LLM request deleted, set messages.llm_request_id to NULL
    )
    
    # Add index for fast lookups (common query: find messages by llm_request_id)
    op.create_index(
        'idx_messages_llm_request_id',
        'messages',
        ['llm_request_id']
    )


def downgrade() -> None:
    """Remove llm_request_id from messages table."""
    # Drop index first
    op.drop_index('idx_messages_llm_request_id', table_name='messages')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_messages_llm_request_id', 'messages', type_='foreignkey')
    
    # Drop column
    op.drop_column('messages', 'llm_request_id')
