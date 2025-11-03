# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""add_fts_to_directory_entries

Revision ID: e9e83012d6b4
Revises: 944490dcfaaa
Create Date: 2025-10-28 20:41:47.901754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9e83012d6b4'
down_revision: Union[str, Sequence[str], None] = '944490dcfaaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add full-text search support to directory_entries."""
    
    # Add search_vector tsvector column (nullable, will be populated by trigger)
    # Weight A (highest): name field
    # Weight B (medium): tags array
    # Weight C (lowest): entry_data JSONB content
    op.execute("""
        ALTER TABLE directory_entries 
        ADD COLUMN search_vector tsvector
    """)
    
    # Create trigger function to maintain search_vector
    # Note: STABLE volatility because to_tsvector() depends on text search configuration
    op.execute("""
        CREATE OR REPLACE FUNCTION directory_entries_search_vector_trigger() 
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(array_to_string(NEW.tags, ' '), '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.entry_data::text, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to auto-update search_vector on INSERT/UPDATE
    op.execute("""
        CREATE TRIGGER directory_entries_search_vector_update
        BEFORE INSERT OR UPDATE OF name, tags, entry_data
        ON directory_entries
        FOR EACH ROW
        EXECUTE FUNCTION directory_entries_search_vector_trigger();
    """)
    
    # Populate search_vector for existing rows
    op.execute("""
        UPDATE directory_entries
        SET search_vector = 
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(array_to_string(tags, ' '), '')), 'B') ||
            setweight(to_tsvector('english', coalesce(entry_data::text, '')), 'C')
    """)
    
    # Create GIN index for fast full-text search queries
    op.create_index(
        'idx_directory_entries_fts',
        'directory_entries',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Add column comment for documentation
    op.execute("""
        COMMENT ON COLUMN directory_entries.search_vector IS 
        'Full-text search vector (name=A, tags=B, entry_data=C)'
    """)


def downgrade() -> None:
    """Downgrade schema - Remove full-text search support."""
    
    # Drop the GIN index first
    op.drop_index('idx_directory_entries_fts', table_name='directory_entries')
    
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS directory_entries_search_vector_update ON directory_entries")
    
    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS directory_entries_search_vector_trigger()")
    
    # Drop the search_vector column
    op.execute("ALTER TABLE directory_entries DROP COLUMN IF EXISTS search_vector")
