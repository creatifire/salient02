"""make_sessions_account_instance_nullable

Make sessions.account_id, sessions.account_slug, and sessions.agent_instance_id 
nullable to support progressive session context flow.

Progressive Session Context Flow:
1. First request → Session middleware creates session with NULL account/instance
2. User navigates to /accounts/{account}/agents/{instance}/chat
3. Chat endpoint updates session with account_id, account_slug, agent_instance_id
4. Subsequent requests → Session loaded with remembered context

Rationale:
- Session middleware runs BEFORE URL path parameters are known
- Cannot populate account/instance context at session creation time
- Making fields nullable enables clean architectural flow
- Foreign key constraints remain in place for referential integrity

Revision ID: 5cd8e16e070f
Revises: d7f01eb864b8
Create Date: 2025-10-08 17:53:24.368470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cd8e16e070f'
down_revision: Union[str, Sequence[str], None] = 'd7f01eb864b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Make session account/instance fields nullable for progressive context flow.
    
    Changes:
    - sessions.account_id: NOT NULL → NULLABLE
    - sessions.account_slug: NOT NULL → NULLABLE  
    - sessions.agent_instance_id: NOT NULL → NULLABLE
    
    Foreign key constraints remain in place.
    """
    # Make account_id nullable (session starts without account context)
    op.alter_column('sessions', 'account_id',
                    existing_type=sa.UUID(),
                    nullable=True)
    
    # Make account_slug nullable (denormalized field, follows account_id)
    op.alter_column('sessions', 'account_slug',
                    existing_type=sa.String(),
                    nullable=True)
    
    # Make agent_instance_id nullable (session starts without instance context)
    op.alter_column('sessions', 'agent_instance_id',
                    existing_type=sa.UUID(),
                    nullable=True)


def downgrade() -> None:
    """
    Restore NOT NULL constraints on session account/instance fields.
    
    WARNING: This will fail if any sessions exist with NULL values.
    Only run this downgrade if all sessions have been cleaned up.
    """
    # Restore NOT NULL constraint on agent_instance_id
    op.alter_column('sessions', 'agent_instance_id',
                    existing_type=sa.UUID(),
                    nullable=False)
    
    # Restore NOT NULL constraint on account_slug
    op.alter_column('sessions', 'account_slug',
                    existing_type=sa.String(),
                    nullable=False)
    
    # Restore NOT NULL constraint on account_id
    op.alter_column('sessions', 'account_id',
                    existing_type=sa.UUID(),
                    nullable=False)
