"""
Automated tests for agent instance loader.
Tests for 0022-001-001-03 - Agent instance loader implementation.
"""
import pytest
import pytest_asyncio
from pathlib import Path
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

from app.agents.instance_loader import load_agent_instance, AgentInstance, _get_config_path

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


class TestLoadAgentInstanceSuccess:
    """Test successful instance loading."""
    
    @pytest.mark.asyncio
    async def test_load_default_account_simple_chat1(self, db_session):
        """Load default_account/simple_chat1 successfully."""
        instance = await load_agent_instance("default_account", "simple_chat1", session=db_session)
        
        assert isinstance(instance, AgentInstance)
        assert instance.account_slug == "default_account"
        assert instance.instance_slug == "simple_chat1"
        assert instance.agent_type == "simple_chat"
        assert instance.display_name == "Simple Chat 1"
        assert instance.status == "active"
        assert isinstance(instance.id, UUID)
        assert isinstance(instance.account_id, UUID)
        assert isinstance(instance.config, dict)
        assert "model_settings" in instance.config
        assert instance.system_prompt is not None
    
    @pytest.mark.asyncio
    async def test_load_multiple_instances_same_account(self, db_session):
        """Load simple_chat1 and simple_chat2 from default_account."""
        instance1 = await load_agent_instance("default_account", "simple_chat1", session=db_session)
        instance2 = await load_agent_instance("default_account", "simple_chat2", session=db_session)
        
        # Both should be from same account
        assert instance1.account_id == instance2.account_id
        assert instance1.account_slug == instance2.account_slug == "default_account"
        
        # But different instances
        assert instance1.id != instance2.id
        assert instance1.instance_slug == "simple_chat1"
        assert instance2.instance_slug == "simple_chat2"
    
    @pytest.mark.asyncio
    async def test_load_instance_different_account(self, db_session):
        """Load acme/acme_chat1 successfully."""
        instance = await load_agent_instance("acme", "acme_chat1", session=db_session)
        
        assert instance.account_slug == "acme"
        assert instance.instance_slug == "acme_chat1"
        assert instance.agent_type == "simple_chat"
        assert instance.display_name == "Acme Chat 1"
        assert instance.status == "active"
        
        # Verify config is different from default_account instances
        assert instance.config is not None
        # acme_chat1 has temperature 0.5 (different from default 0.3)
        assert instance.config["model_settings"]["temperature"] == 0.5


class TestLoadAgentInstanceUpdatesTimestamp:
    """Test that loading updates last_used_at timestamp."""
    
    @pytest.mark.asyncio
    async def test_load_updates_last_used_at(self, db_session):
        """Verify last_used_at is updated when instance is loaded."""
        # Get initial timestamp
        query = text("""
            SELECT last_used_at FROM agent_instances ai
            JOIN accounts a ON ai.account_id = a.id
            WHERE a.slug = 'default_account' AND ai.instance_slug = 'simple_chat1'
        """)
        result = await db_session.execute(query)
        initial_timestamp = result.scalar()
        
        # Load instance (should update timestamp)
        instance = await load_agent_instance("default_account", "simple_chat1", session=db_session)
        
        # Get new timestamp
        result = await db_session.execute(query)
        new_timestamp = result.scalar()
        
        # Timestamp should be updated
        if initial_timestamp is None:
            # First time loading, should now have a timestamp
            assert new_timestamp is not None
        else:
            # Timestamp should be newer (or equal if very fast)
            assert new_timestamp >= initial_timestamp
        
        # Instance should have the updated timestamp
        assert instance.last_used_at is not None


class TestLoadAgentInstanceErrors:
    """Test error handling for invalid inputs."""
    
    @pytest.mark.asyncio
    async def test_load_invalid_account(self, db_session):
        """ValueError for invalid account."""
        with pytest.raises(ValueError, match="Agent instance not found"):
            await load_agent_instance("nonexistent_account", "simple_chat1", session=db_session)
    
    @pytest.mark.asyncio
    async def test_load_invalid_instance(self, db_session):
        """ValueError for invalid instance."""
        with pytest.raises(ValueError, match="Agent instance not found"):
            await load_agent_instance("default_account", "nonexistent_instance", session=db_session)
    
    @pytest.mark.asyncio
    async def test_load_inactive_instance(self, db_session):
        """ValueError for inactive instance."""
        # First, mark an instance as inactive
        query = text("""
            UPDATE agent_instances
            SET status = 'inactive'
            WHERE id = (
                SELECT ai.id FROM agent_instances ai
                JOIN accounts a ON ai.account_id = a.id
                WHERE a.slug = 'default_account' AND ai.instance_slug = 'simple_chat2'
            )
        """)
        await db_session.execute(query)
        await db_session.commit()
        
        try:
            # Try to load inactive instance
            with pytest.raises(ValueError, match="is not active"):
                await load_agent_instance("default_account", "simple_chat2", session=db_session)
        finally:
            # Restore status for other tests
            query = text("""
                UPDATE agent_instances
                SET status = 'active'
                WHERE id = (
                    SELECT ai.id FROM agent_instances ai
                    JOIN accounts a ON ai.account_id = a.id
                    WHERE a.slug = 'default_account' AND ai.instance_slug = 'simple_chat2'
                )
            """)
            await db_session.execute(query)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_load_missing_config(self, db_session):
        """FileNotFoundError for missing config file."""
        # Create a temporary database entry with no config file
        query = text("""
            INSERT INTO agent_instances (account_id, instance_slug, agent_type, display_name, status)
            VALUES (
                (SELECT id FROM accounts WHERE slug = 'default_account'),
                'test_missing_config',
                'simple_chat',
                'Test Missing Config',
                'active'
            )
        """)
        await db_session.execute(query)
        await db_session.commit()
        
        try:
            # Try to load instance with missing config
            with pytest.raises(FileNotFoundError, match="Config file not found"):
                await load_agent_instance("default_account", "test_missing_config", session=db_session)
        finally:
            # Clean up
            query = text("""
                DELETE FROM agent_instances
                WHERE instance_slug = 'test_missing_config'
            """)
            await db_session.execute(query)
            await db_session.commit()


class TestAgentInstanceDataclass:
    """Test AgentInstance dataclass structure."""
    
    @pytest.mark.asyncio
    async def test_dataclass_validation(self, db_session):
        """Dataclass is properly structured."""
        instance = await load_agent_instance("default_account", "simple_chat1", session=db_session)
        
        # Check all required fields exist
        assert hasattr(instance, 'id')
        assert hasattr(instance, 'account_id')
        assert hasattr(instance, 'account_slug')
        assert hasattr(instance, 'instance_slug')
        assert hasattr(instance, 'agent_type')
        assert hasattr(instance, 'display_name')
        assert hasattr(instance, 'status')
        assert hasattr(instance, 'last_used_at')
        assert hasattr(instance, 'config')
        assert hasattr(instance, 'system_prompt')
        
        # Check field types
        assert isinstance(instance.id, UUID)
        assert isinstance(instance.account_id, UUID)
        assert isinstance(instance.account_slug, str)
        assert isinstance(instance.instance_slug, str)
        assert isinstance(instance.agent_type, str)
        assert isinstance(instance.display_name, str)
        assert isinstance(instance.status, str)
        assert isinstance(instance.config, dict)
        assert isinstance(instance.system_prompt, (str, type(None)))


class TestConfigPathFromAppYaml:
    """Test that config path is read from app.yaml."""
    
    def test_config_path_construction(self):
        """Verify config path is correctly constructed."""
        path = _get_config_path("default_account", "simple_chat1")
        
        assert isinstance(path, Path)
        assert "default_account" in str(path)
        assert "simple_chat1" in str(path)
        assert "config.yaml" in str(path)
        assert path.name == "config.yaml"
    
    def test_config_path_exists_for_test_instances(self):
        """Verify config files exist for all test instances."""
        paths = [
            _get_config_path("default_account", "simple_chat1"),
            _get_config_path("default_account", "simple_chat2"),
            _get_config_path("acme", "acme_chat1"),
        ]
        
        for path in paths:
            assert path.exists(), f"Config file should exist: {path}"
