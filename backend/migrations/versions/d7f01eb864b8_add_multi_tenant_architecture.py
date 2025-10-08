"""add_multi_tenant_architecture

Revision ID: d7f01eb864b8
Revises: 4360c1de944b
Create Date: 2025-10-08 14:34:40.168007

Multi-tenant architecture implementation:
- TRUNCATE existing data (start fresh)
- Create accounts and agent_instances tables
- Add account/instance columns to sessions, messages, llm_requests
- Seed test accounts (default_account, acme)
- Seed test agent instances (simple_chat1, simple_chat2, acme_chat1)
- Create performance indexes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd7f01eb864b8'
down_revision: Union[str, Sequence[str], None] = '4360c1de944b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to multi-tenant architecture."""
    
    # ==========================================
    # STEP 1: CLEAR EXISTING DATA
    # ==========================================
    # Start fresh - TRUNCATE all existing data (CASCADE to handle FKs)
    op.execute("TRUNCATE TABLE llm_requests CASCADE")
    op.execute("TRUNCATE TABLE messages CASCADE")
    op.execute("TRUNCATE TABLE profiles CASCADE")
    op.execute("TRUNCATE TABLE sessions CASCADE")
    
    # ==========================================
    # STEP 2: CREATE ACCOUNTS TABLE
    # ==========================================
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('subscription_tier', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_accounts_slug')
    )
    
    # ==========================================
    # STEP 3: CREATE AGENT_INSTANCES TABLE
    # ==========================================
    op.create_table(
        'agent_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_slug', sa.String(), nullable=False),
        sa.Column('agent_type', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('account_id', 'instance_slug', name='uq_agent_instances_account_slug')
    )
    
    # ==========================================
    # STEP 4: ADD COLUMNS TO SESSIONS TABLE
    # ==========================================
    op.add_column('sessions', sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('sessions', sa.Column('account_slug', sa.String(), nullable=False))
    op.add_column('sessions', sa.Column('agent_instance_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('sessions', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('sessions', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    
    # Add foreign keys for sessions
    op.create_foreign_key('fk_sessions_account_id', 'sessions', 'accounts', ['account_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_sessions_agent_instance_id', 'sessions', 'agent_instances', ['agent_instance_id'], ['id'], ondelete='CASCADE')
    
    # ==========================================
    # STEP 5: ADD COLUMNS TO MESSAGES TABLE
    # ==========================================
    op.add_column('messages', sa.Column('agent_instance_id', postgresql.UUID(as_uuid=True), nullable=False))
    
    # Add foreign key for messages
    op.create_foreign_key('fk_messages_agent_instance_id', 'messages', 'agent_instances', ['agent_instance_id'], ['id'], ondelete='CASCADE')
    
    # ==========================================
    # STEP 6: ADD COLUMNS TO LLM_REQUESTS TABLE
    # ==========================================
    op.add_column('llm_requests', sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('llm_requests', sa.Column('account_slug', sa.String(), nullable=True))
    op.add_column('llm_requests', sa.Column('agent_instance_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('llm_requests', sa.Column('agent_instance_slug', sa.String(), nullable=True))
    op.add_column('llm_requests', sa.Column('agent_type', sa.String(), nullable=True))
    op.add_column('llm_requests', sa.Column('completion_status', sa.String(), nullable=True))
    
    # Add foreign keys for llm_requests
    op.create_foreign_key('fk_llm_requests_account_id', 'llm_requests', 'accounts', ['account_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_llm_requests_agent_instance_id', 'llm_requests', 'agent_instances', ['agent_instance_id'], ['id'], ondelete='SET NULL')
    
    # ==========================================
    # STEP 7: CREATE INDEXES FOR PERFORMANCE
    # ==========================================
    # Accounts indexes
    op.create_index('ix_accounts_slug', 'accounts', ['slug'], unique=True)
    op.create_index('ix_accounts_status', 'accounts', ['status'])
    
    # Agent instances indexes
    op.create_index('ix_agent_instances_account_id', 'agent_instances', ['account_id'])
    op.create_index('ix_agent_instances_account_slug', 'agent_instances', ['account_id', 'instance_slug'], unique=True)
    op.create_index('ix_agent_instances_status', 'agent_instances', ['status'])
    op.create_index('ix_agent_instances_last_used_at', 'agent_instances', ['last_used_at'])
    
    # Sessions indexes (account/instance queries)
    op.create_index('ix_sessions_account_id', 'sessions', ['account_id'])
    op.create_index('ix_sessions_account_slug', 'sessions', ['account_slug'])
    op.create_index('ix_sessions_agent_instance_id', 'sessions', ['agent_instance_id'])
    op.create_index('ix_sessions_account_activity', 'sessions', ['account_id', 'last_activity_at'])
    
    # Messages indexes (agent instance queries)
    op.create_index('ix_messages_agent_instance_id', 'messages', ['agent_instance_id'])
    op.create_index('ix_messages_agent_created', 'messages', ['agent_instance_id', 'created_at'])
    
    # LLM requests indexes (cost tracking queries)
    op.create_index('ix_llm_requests_account_id', 'llm_requests', ['account_id'])
    op.create_index('ix_llm_requests_account_slug', 'llm_requests', ['account_slug'])
    op.create_index('ix_llm_requests_agent_instance_id', 'llm_requests', ['agent_instance_id'])
    op.create_index('ix_llm_requests_agent_instance_slug', 'llm_requests', ['agent_instance_slug'])
    op.create_index('ix_llm_requests_agent_type', 'llm_requests', ['agent_type'])
    
    # ==========================================
    # STEP 8: SEED TEST ACCOUNTS
    # ==========================================
    # Insert test accounts and get their generated UUIDs
    op.execute("""
        INSERT INTO accounts (slug, name, status, subscription_tier, created_at, updated_at)
        VALUES 
            ('default_account', 'Default Account', 'active', 'free', now(), now()),
            ('acme', 'Acme Corporation', 'active', 'premium', now(), now())
    """)
    
    # ==========================================
    # STEP 9: SEED TEST AGENT INSTANCES
    # ==========================================
    # Insert test agent instances, using subqueries to get account UUIDs
    op.execute("""
        INSERT INTO agent_instances (account_id, instance_slug, agent_type, display_name, status, created_at, updated_at)
        VALUES 
            (
                (SELECT id FROM accounts WHERE slug = 'default_account'),
                'simple_chat1',
                'simple_chat',
                'Simple Chat 1',
                'active',
                now(),
                now()
            ),
            (
                (SELECT id FROM accounts WHERE slug = 'default_account'),
                'simple_chat2',
                'simple_chat',
                'Simple Chat 2',
                'active',
                now(),
                now()
            ),
            (
                (SELECT id FROM accounts WHERE slug = 'acme'),
                'acme_chat1',
                'simple_chat',
                'Acme Chat 1',
                'active',
                now(),
                now()
            )
    """)


def downgrade() -> None:
    """Downgrade schema - remove multi-tenant architecture."""
    
    # Drop indexes
    op.drop_index('ix_llm_requests_agent_type', table_name='llm_requests')
    op.drop_index('ix_llm_requests_agent_instance_slug', table_name='llm_requests')
    op.drop_index('ix_llm_requests_agent_instance_id', table_name='llm_requests')
    op.drop_index('ix_llm_requests_account_slug', table_name='llm_requests')
    op.drop_index('ix_llm_requests_account_id', table_name='llm_requests')
    op.drop_index('ix_messages_agent_created', table_name='messages')
    op.drop_index('ix_messages_agent_instance_id', table_name='messages')
    op.drop_index('ix_sessions_account_activity', table_name='sessions')
    op.drop_index('ix_sessions_agent_instance_id', table_name='sessions')
    op.drop_index('ix_sessions_account_slug', table_name='sessions')
    op.drop_index('ix_sessions_account_id', table_name='sessions')
    op.drop_index('ix_agent_instances_last_used_at', table_name='agent_instances')
    op.drop_index('ix_agent_instances_status', table_name='agent_instances')
    op.drop_index('ix_agent_instances_account_slug', table_name='agent_instances')
    op.drop_index('ix_agent_instances_account_id', table_name='agent_instances')
    op.drop_index('ix_accounts_status', table_name='accounts')
    op.drop_index('ix_accounts_slug', table_name='accounts')
    
    # Drop foreign keys
    op.drop_constraint('fk_llm_requests_agent_instance_id', 'llm_requests', type_='foreignkey')
    op.drop_constraint('fk_llm_requests_account_id', 'llm_requests', type_='foreignkey')
    op.drop_constraint('fk_messages_agent_instance_id', 'messages', type_='foreignkey')
    op.drop_constraint('fk_sessions_agent_instance_id', 'sessions', type_='foreignkey')
    op.drop_constraint('fk_sessions_account_id', 'sessions', type_='foreignkey')
    
    # Drop columns
    op.drop_column('llm_requests', 'completion_status')
    op.drop_column('llm_requests', 'agent_type')
    op.drop_column('llm_requests', 'agent_instance_slug')
    op.drop_column('llm_requests', 'agent_instance_id')
    op.drop_column('llm_requests', 'account_slug')
    op.drop_column('llm_requests', 'account_id')
    op.drop_column('messages', 'agent_instance_id')
    op.drop_column('sessions', 'updated_at')
    op.drop_column('sessions', 'user_id')
    op.drop_column('sessions', 'agent_instance_id')
    op.drop_column('sessions', 'account_slug')
    op.drop_column('sessions', 'account_id')
    
    # Drop tables (CASCADE will handle foreign keys)
    op.drop_table('agent_instances')
    op.drop_table('accounts')
