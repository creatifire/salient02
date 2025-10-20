"""add_agent_instance_slug_to_sessions

Add denormalized agent_instance_slug to sessions table for fast analytics.

Enables queries like "sessions per agent" without JOINs to agent_instances table.
Follows same pattern as llm_requests table (FK + denormalized slug).

Revision ID: 48d95232d581
Revises: 2f9b9044dd96
Create Date: 2025-10-20 15:28:25.984345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48d95232d581'
down_revision: Union[str, Sequence[str], None] = '2f9b9044dd96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add agent_instance_slug column and indexes to sessions table."""
    
    # Add agent_instance_slug column (nullable - will populate on next session use)
    op.add_column(
        'sessions',
        sa.Column('agent_instance_slug', sa.Text(), nullable=True, comment='Denormalized for fast analytics - avoids JOINs to agent_instances')
    )
    
    # Create standalone index for simple agent-based queries
    op.create_index(
        'idx_sessions_agent_instance_slug',
        'sessions',
        ['agent_instance_slug'],
        unique=False
    )
    
    # Create composite index for account + agent queries (most common analytics pattern)
    op.create_index(
        'idx_sessions_account_agent',
        'sessions',
        ['account_slug', 'agent_instance_slug'],
        unique=False
    )


def downgrade() -> None:
    """Remove agent_instance_slug column and indexes from sessions table."""
    
    # Drop indexes first (must drop before column)
    op.drop_index('idx_sessions_account_agent', table_name='sessions')
    op.drop_index('idx_sessions_agent_instance_slug', table_name='sessions')
    
    # Drop column
    op.drop_column('sessions', 'agent_instance_slug')
