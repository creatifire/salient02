# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""add_directory_tables

Revision ID: 944490dcfaaa
Revises: 48d95232d581
Create Date: 2025-10-21 13:57:14.299495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers, used by Alembic.
revision: str = '944490dcfaaa'
down_revision: Union[str, Sequence[str], None] = '48d95232d581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add directory tables for multi-purpose directory service."""
    
    # Create directory_lists table
    op.create_table(
        'directory_lists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('list_name', sa.String(), nullable=False),
        sa.Column('list_description', sa.Text(), nullable=True),
        sa.Column('entry_type', sa.String(), nullable=False),
        sa.Column('schema_file', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.UniqueConstraint('account_id', 'list_name', name='uq_directory_lists_account_list')
    )
    
    # Create indexes for directory_lists
    op.create_index('idx_directory_lists_account_id', 'directory_lists', ['account_id'])
    op.create_index('idx_directory_lists_entry_type', 'directory_lists', ['entry_type'])
    
    # Add table comment
    op.execute("""
        COMMENT ON TABLE directory_lists IS 
        'Multi-purpose directory collections per account (doctors, drugs, products, services, etc.)'
    """)
    op.execute("""
        COMMENT ON COLUMN directory_lists.entry_type IS 
        'References schema in backend/config/directory_schemas/{entry_type}.yaml'
    """)
    
    # Create directory_entries table
    op.create_table(
        'directory_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('directory_list_id', UUID(as_uuid=True), sa.ForeignKey('directory_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('tags', ARRAY(sa.String()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('contact_info', JSONB(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('entry_data', JSONB(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    
    # Create indexes for directory_entries
    op.create_index('idx_directory_entries_list_id', 'directory_entries', ['directory_list_id'])
    op.create_index('idx_directory_entries_name', 'directory_entries', ['name'])
    op.create_index('idx_directory_entries_tags', 'directory_entries', ['tags'], postgresql_using='gin')
    op.create_index('idx_directory_entries_entry_data', 'directory_entries', ['entry_data'], postgresql_using='gin')
    
    # Add table comments
    op.execute("""
        COMMENT ON TABLE directory_entries IS 
        'Generic directory entries - doctors, drugs, products, consultants, services, etc.'
    """)
    op.execute("""
        COMMENT ON COLUMN directory_entries.tags IS 
        'Flexible array - languages for people, categories for products, drug classes for pharmaceuticals'
    """)
    op.execute("""
        COMMENT ON COLUMN directory_entries.entry_data IS 
        'JSONB structure defined by schema_file in directory_lists table'
    """)


def downgrade() -> None:
    """Downgrade schema - Remove directory tables."""
    
    # Drop indexes first
    op.drop_index('idx_directory_entries_entry_data', table_name='directory_entries')
    op.drop_index('idx_directory_entries_tags', table_name='directory_entries')
    op.drop_index('idx_directory_entries_name', table_name='directory_entries')
    op.drop_index('idx_directory_entries_list_id', table_name='directory_entries')
    
    op.drop_index('idx_directory_lists_entry_type', table_name='directory_lists')
    op.drop_index('idx_directory_lists_account_id', table_name='directory_lists')
    
    # Drop tables (CASCADE will handle FK constraints)
    op.drop_table('directory_entries')
    op.drop_table('directory_lists')
