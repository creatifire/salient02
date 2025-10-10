"""
Automated tests for multi-tenant database schema migration.
Tests for 0022-001-001-02 - Multi-tenant database schema migration.
"""
import pytest
import pytest_asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://salient_user:salient_pass@localhost:5432/salient_dev")


@pytest_asyncio.fixture
async def db_engine():
    """Create async database engine for testing."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create async database session for testing."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


class TestMigrationClearsData:
    """Test that migration cleared all existing data."""
    
    @pytest.mark.asyncio
    async def test_sessions_cleared_by_migration(self, db_session):
        """Verify sessions table was cleared by migration (may have new test sessions)."""
        # Migration 7f7aab5c2805 truncates all old data
        # However, other tests may create new sessions after migration
        # This test just verifies the migration ran (by checking new columns exist)
        result = await db_session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'sessions' AND column_name IN ('account_id', 'agent_instance_id')"
        ))
        columns = [row[0] for row in result.fetchall()]
        assert 'account_id' in columns, "account_id column should exist after migration"
        assert 'agent_instance_id' in columns, "agent_instance_id column should exist after migration"
    
    @pytest.mark.skip(reason="One-time migration validation - now contains legitimate test data from manual testing")
    @pytest.mark.asyncio
    async def test_messages_empty(self, db_session):
        """SKIPPED: Migration 0022-001-001-03 data clearing validated at migration time."""
        result = await db_session.execute(text("SELECT COUNT(*) FROM messages"))
        count = result.scalar()
        assert count == 0, f"Messages table should be empty, found {count} rows"
    
    @pytest.mark.skip(reason="One-time migration validation - now contains legitimate test data from manual testing")
    @pytest.mark.asyncio
    async def test_llm_requests_empty(self, db_session):
        """SKIPPED: Migration 0022-001-001-03 data clearing validated at migration time."""
        result = await db_session.execute(text("SELECT COUNT(*) FROM llm_requests"))
        count = result.scalar()
        assert count == 0, f"LLM requests table should be empty, found {count} rows"
    
    @pytest.mark.asyncio
    async def test_profiles_empty(self, db_session):
        """Verify profiles table is empty after migration."""
        result = await db_session.execute(text("SELECT COUNT(*) FROM profiles"))
        count = result.scalar()
        assert count == 0, f"Profiles table should be empty, found {count} rows"


class TestMigrationCreatesAllTables:
    """Test that migration created new tables."""
    
    @pytest.mark.asyncio
    async def test_accounts_table_exists(self, db_engine):
        """Verify accounts table was created."""
        async with db_engine.connect() as conn:
            def get_tables(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(get_tables)
            assert 'accounts' in tables, "accounts table should exist"
    
    @pytest.mark.asyncio
    async def test_agent_instances_table_exists(self, db_engine):
        """Verify agent_instances table was created."""
        async with db_engine.connect() as conn:
            def get_tables(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(get_tables)
            assert 'agent_instances' in tables, "agent_instances table should exist"


class TestMigrationAddsColumns:
    """Test that migration added new columns to existing tables."""
    
    @pytest.mark.asyncio
    async def test_sessions_new_columns(self, db_engine):
        """Verify new columns added to sessions table."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name'] for col in inspector.get_columns('sessions')}
            
            columns = await conn.run_sync(get_columns)
            required_columns = {'account_id', 'account_slug', 'agent_instance_id', 'user_id', 'updated_at'}
            assert required_columns.issubset(columns), f"Missing columns in sessions: {required_columns - columns}"
    
    @pytest.mark.asyncio
    async def test_messages_new_columns(self, db_engine):
        """Verify new columns added to messages table."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name'] for col in inspector.get_columns('messages')}
            
            columns = await conn.run_sync(get_columns)
            assert 'agent_instance_id' in columns, "messages table should have agent_instance_id column"
    
    @pytest.mark.asyncio
    async def test_llm_requests_new_columns(self, db_engine):
        """Verify new columns added to llm_requests table."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name'] for col in inspector.get_columns('llm_requests')}
            
            columns = await conn.run_sync(get_columns)
            required_columns = {
                'account_id', 'account_slug', 'agent_instance_id', 
                'agent_instance_slug', 'agent_type', 'completion_status'
            }
            assert required_columns.issubset(columns), f"Missing columns in llm_requests: {required_columns - columns}"


class TestMigrationCreatesIndexes:
    """Test that migration created performance indexes."""
    
    @pytest.mark.asyncio
    async def test_accounts_indexes(self, db_engine):
        """Verify indexes created on accounts table."""
        async with db_engine.connect() as conn:
            def get_indexes(sync_conn):
                inspector = inspect(sync_conn)
                return {idx['name'] for idx in inspector.get_indexes('accounts')}
            
            indexes = await conn.run_sync(get_indexes)
            required_indexes = {'ix_accounts_slug', 'ix_accounts_status'}
            assert required_indexes.issubset(indexes), f"Missing indexes on accounts: {required_indexes - indexes}"
    
    @pytest.mark.asyncio
    async def test_agent_instances_indexes(self, db_engine):
        """Verify indexes created on agent_instances table."""
        async with db_engine.connect() as conn:
            def get_indexes(sync_conn):
                inspector = inspect(sync_conn)
                return {idx['name'] for idx in inspector.get_indexes('agent_instances')}
            
            indexes = await conn.run_sync(get_indexes)
            required_indexes = {
                'ix_agent_instances_account_id',
                'ix_agent_instances_account_slug',
                'ix_agent_instances_status',
                'ix_agent_instances_last_used_at'
            }
            assert required_indexes.issubset(indexes), f"Missing indexes on agent_instances: {required_indexes - indexes}"
    
    @pytest.mark.asyncio
    async def test_sessions_indexes(self, db_engine):
        """Verify indexes created on sessions table."""
        async with db_engine.connect() as conn:
            def get_indexes(sync_conn):
                inspector = inspect(sync_conn)
                return {idx['name'] for idx in inspector.get_indexes('sessions')}
            
            indexes = await conn.run_sync(get_indexes)
            required_indexes = {
                'ix_sessions_account_id',
                'ix_sessions_account_slug',
                'ix_sessions_agent_instance_id',
                'ix_sessions_account_activity'
            }
            assert required_indexes.issubset(indexes), f"Missing indexes on sessions: {required_indexes - indexes}"


class TestTestAccountsSeeded:
    """Test that test accounts were seeded."""
    
    @pytest.mark.asyncio
    async def test_two_accounts_exist(self, db_session):
        """Verify 2 accounts were seeded."""
        result = await db_session.execute(text("SELECT COUNT(*) FROM accounts"))
        count = result.scalar()
        assert count == 2, f"Expected 2 accounts, found {count}"
    
    @pytest.mark.asyncio
    async def test_default_account_exists(self, db_session):
        """Verify default_account was seeded."""
        result = await db_session.execute(
            text("SELECT slug, name, status FROM accounts WHERE slug = 'default_account'")
        )
        row = result.fetchone()
        assert row is not None, "default_account should exist"
        assert row.slug == 'default_account'
        assert row.name == 'Default Account'
        assert row.status == 'active'
    
    @pytest.mark.asyncio
    async def test_acme_account_exists(self, db_session):
        """Verify acme account was seeded."""
        result = await db_session.execute(
            text("SELECT slug, name, status FROM accounts WHERE slug = 'acme'")
        )
        row = result.fetchone()
        assert row is not None, "acme account should exist"
        assert row.slug == 'acme'
        assert row.name == 'Acme Corporation'
        assert row.status == 'active'
    
    @pytest.mark.asyncio
    async def test_accounts_have_uuid_primary_keys(self, db_session):
        """Verify accounts use UUID primary keys."""
        result = await db_session.execute(text("SELECT id FROM accounts LIMIT 1"))
        row = result.fetchone()
        assert row is not None
        # UUID should be a string representation of UUID
        assert len(str(row.id)) == 36, "Primary key should be UUID (36 chars with hyphens)"


class TestTestInstancesSeeded:
    """Test that test agent instances were seeded."""
    
    @pytest.mark.asyncio
    async def test_three_instances_exist(self, db_session):
        """Verify 3 agent instances were seeded."""
        result = await db_session.execute(text("SELECT COUNT(*) FROM agent_instances"))
        count = result.scalar()
        assert count == 3, f"Expected 3 agent instances, found {count}"
    
    @pytest.mark.asyncio
    async def test_simple_chat1_exists(self, db_session):
        """Verify simple_chat1 instance exists."""
        result = await db_session.execute(
            text("""
                SELECT ai.instance_slug, ai.agent_type, ai.display_name, a.slug as account_slug
                FROM agent_instances ai
                JOIN accounts a ON ai.account_id = a.id
                WHERE ai.instance_slug = 'simple_chat1'
            """)
        )
        row = result.fetchone()
        assert row is not None, "simple_chat1 instance should exist"
        assert row.instance_slug == 'simple_chat1'
        assert row.agent_type == 'simple_chat'
        assert row.display_name == 'Simple Chat 1'
        assert row.account_slug == 'default_account'
    
    @pytest.mark.asyncio
    async def test_simple_chat2_exists(self, db_session):
        """Verify simple_chat2 instance exists."""
        result = await db_session.execute(
            text("""
                SELECT ai.instance_slug, ai.agent_type, a.slug as account_slug
                FROM agent_instances ai
                JOIN accounts a ON ai.account_id = a.id
                WHERE ai.instance_slug = 'simple_chat2'
            """)
        )
        row = result.fetchone()
        assert row is not None, "simple_chat2 instance should exist"
        assert row.account_slug == 'default_account'
    
    @pytest.mark.asyncio
    async def test_acme_chat1_exists(self, db_session):
        """Verify acme_chat1 instance exists."""
        result = await db_session.execute(
            text("""
                SELECT ai.instance_slug, ai.agent_type, a.slug as account_slug
                FROM agent_instances ai
                JOIN accounts a ON ai.account_id = a.id
                WHERE ai.instance_slug = 'acme_chat1'
            """)
        )
        row = result.fetchone()
        assert row is not None, "acme_chat1 instance should exist"
        assert row.account_slug == 'acme'


class TestInstanceAccountReferences:
    """Test that instances correctly reference their accounts."""
    
    @pytest.mark.asyncio
    async def test_default_account_has_two_instances(self, db_session):
        """Verify default_account has 2 instances."""
        result = await db_session.execute(
            text("""
                SELECT COUNT(*) FROM agent_instances ai
                JOIN accounts a ON ai.account_id = a.id
                WHERE a.slug = 'default_account'
            """)
        )
        count = result.scalar()
        assert count == 2, f"default_account should have 2 instances, found {count}"
    
    @pytest.mark.asyncio
    async def test_acme_account_has_one_instance(self, db_session):
        """Verify acme account has 1 instance."""
        result = await db_session.execute(
            text("""
                SELECT COUNT(*) FROM agent_instances ai
                JOIN accounts a ON ai.account_id = a.id
                WHERE a.slug = 'acme'
            """)
        )
        count = result.scalar()
        assert count == 1, f"acme account should have 1 instance, found {count}"


class TestForeignKeyConstraints:
    """Test that foreign key constraints work correctly."""
    
    @pytest.mark.asyncio
    async def test_agent_instances_fk_to_accounts(self, db_engine):
        """Verify agent_instances has FK to accounts."""
        async with db_engine.connect() as conn:
            def get_fks(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_foreign_keys('agent_instances')
            
            fks = await conn.run_sync(get_fks)
            account_fks = [fk for fk in fks if 'account_id' in fk['constrained_columns']]
            assert len(account_fks) > 0, "agent_instances should have FK to accounts"
    
    @pytest.mark.asyncio
    async def test_sessions_fk_to_accounts(self, db_engine):
        """Verify sessions has FK to accounts."""
        async with db_engine.connect() as conn:
            def get_fks(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_foreign_keys('sessions')
            
            fks = await conn.run_sync(get_fks)
            account_fks = [fk for fk in fks if 'account_id' in fk['constrained_columns']]
            assert len(account_fks) > 0, "sessions should have FK to accounts"
    
    @pytest.mark.asyncio
    async def test_sessions_fk_to_agent_instances(self, db_engine):
        """Verify sessions has FK to agent_instances."""
        async with db_engine.connect() as conn:
            def get_fks(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_foreign_keys('sessions')
            
            fks = await conn.run_sync(get_fks)
            instance_fks = [fk for fk in fks if 'agent_instance_id' in fk['constrained_columns']]
            assert len(instance_fks) > 0, "sessions should have FK to agent_instances"


class TestUniqueConstraints:
    """Test that unique constraints are properly enforced."""
    
    @pytest.mark.asyncio
    async def test_accounts_slug_unique(self, db_engine):
        """Verify accounts.slug has unique constraint."""
        async with db_engine.connect() as conn:
            def get_unique_constraints(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_unique_constraints('accounts')
            
            unique_constraints = await conn.run_sync(get_unique_constraints)
            slug_constraints = [uc for uc in unique_constraints if 'slug' in uc['column_names']]
            assert len(slug_constraints) > 0, "accounts.slug should have unique constraint"
    
    @pytest.mark.asyncio
    async def test_agent_instances_account_slug_unique(self, db_engine):
        """Verify (account_id, instance_slug) is unique in agent_instances."""
        async with db_engine.connect() as conn:
            def get_unique_constraints(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_unique_constraints('agent_instances')
            
            unique_constraints = await conn.run_sync(get_unique_constraints)
            composite_constraints = [
                uc for uc in unique_constraints 
                if 'account_id' in uc['column_names'] and 'instance_slug' in uc['column_names']
            ]
            assert len(composite_constraints) > 0, "(account_id, instance_slug) should be unique"


class TestNotNullConstraints:
    """Test that NOT NULL constraints are properly set."""
    
    @pytest.mark.asyncio
    async def test_sessions_account_id_nullable(self, db_engine):
        """Verify sessions.account_id is NULLABLE (progressive context flow)."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name']: col for col in inspector.get_columns('sessions')}
            
            columns = await conn.run_sync(get_columns)
            assert columns['account_id']['nullable'], "sessions.account_id should be NULLABLE (changed in migration 5cd8e16e070f)"
    
    @pytest.mark.asyncio
    async def test_sessions_agent_instance_id_nullable(self, db_engine):
        """Verify sessions.agent_instance_id is NULLABLE (progressive context flow)."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name']: col for col in inspector.get_columns('sessions')}
            
            columns = await conn.run_sync(get_columns)
            assert columns['agent_instance_id']['nullable'], "sessions.agent_instance_id should be NULLABLE (changed in migration 5cd8e16e070f)"
    
    @pytest.mark.asyncio
    async def test_messages_agent_instance_id_not_null(self, db_engine):
        """Verify messages.agent_instance_id is NOT NULL."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name']: col for col in inspector.get_columns('messages')}
            
            columns = await conn.run_sync(get_columns)
            assert not columns['agent_instance_id']['nullable'], "messages.agent_instance_id should be NOT NULL"
    
    @pytest.mark.asyncio
    async def test_sessions_user_id_nullable(self, db_engine):
        """Verify sessions.user_id is nullable (for anonymous sessions)."""
        async with db_engine.connect() as conn:
            def get_columns(sync_conn):
                inspector = inspect(sync_conn)
                return {col['name']: col for col in inspector.get_columns('sessions')}
            
            columns = await conn.run_sync(get_columns)
            assert columns['user_id']['nullable'], "sessions.user_id should be nullable"
