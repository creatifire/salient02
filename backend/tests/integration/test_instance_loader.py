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


class TestInstanceDiscovery:
    """Tests for instance discovery and listing functions."""
    
    @pytest.mark.asyncio
    async def test_list_account_instances_default(self, db_session):
        """List instances for default_account - should show 2 instances."""
        from app.agents.instance_loader import list_account_instances
        
        instances = await list_account_instances("default_account", session=db_session)
        
        # Should have 2 instances: simple_chat1, simple_chat2
        assert len(instances) == 2, f"Expected 2 instances, got {len(instances)}"
        
        # Extract slugs for easier testing
        slugs = [inst["instance_slug"] for inst in instances]
        assert "simple_chat1" in slugs, "simple_chat1 should be in list"
        assert "simple_chat2" in slugs, "simple_chat2 should be in list"
        
        # Verify all instances are active and have correct agent_type
        for inst in instances:
            assert inst["status"] == "active", f"Instance {inst['instance_slug']} should be active"
            assert inst["agent_type"] == "simple_chat", f"Instance should be simple_chat type"
            assert "id" in inst, "Instance should have id field"
            assert "display_name" in inst, "Instance should have display_name field"
    
    @pytest.mark.asyncio
    async def test_list_account_instances_acme(self, db_session):
        """List instances for acme account - should show 1 instance."""
        from app.agents.instance_loader import list_account_instances
        
        instances = await list_account_instances("acme", session=db_session)
        
        # Should have 1 instance: acme_chat1
        assert len(instances) == 1, f"Expected 1 instance, got {len(instances)}"
        
        inst = instances[0]
        assert inst["instance_slug"] == "acme_chat1", "Should have acme_chat1"
        assert inst["agent_type"] == "simple_chat", "Should be simple_chat type"
        assert inst["status"] == "active", "Should be active"
        assert inst["display_name"] == "Acme Chat 1", "Should have correct display name"
    
    @pytest.mark.asyncio
    async def test_list_empty_account(self, db_session):
        """Handle listing instances for account with no instances."""
        from app.agents.instance_loader import list_account_instances
        from app.models.account import Account
        
        # Create a temporary account with no instances
        new_account = Account(
            slug="empty_test_account",
            name="Empty Test Account",
            status="active"
        )
        db_session.add(new_account)
        await db_session.commit()
        
        try:
            instances = await list_account_instances("empty_test_account", session=db_session)
            
            # Should return empty list
            assert len(instances) == 0, f"Expected 0 instances, got {len(instances)}"
            assert isinstance(instances, list), "Should return a list"
        
        finally:
            # Cleanup: delete test account
            result = await db_session.execute(
                select(Account).where(Account.slug == "empty_test_account")
            )
            account = result.scalar_one_or_none()
            if account:
                await db_session.delete(account)
                await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_list_filters_inactive(self, db_session):
        """Verify only active instances are listed (inactive filtered out)."""
        from app.agents.instance_loader import list_account_instances
        from app.models.agent_instance import AgentInstanceModel
        from sqlalchemy import update
        
        # Mark simple_chat2 as inactive
        await db_session.execute(
            update(AgentInstanceModel)
            .where(AgentInstanceModel.instance_slug == "simple_chat2")
            .values(status="inactive")
        )
        await db_session.commit()
        
        try:
            instances = await list_account_instances("default_account", session=db_session)
            
            # Should only show simple_chat1 (active)
            assert len(instances) == 1, f"Expected 1 active instance, got {len(instances)}"
            assert instances[0]["instance_slug"] == "simple_chat1", "Should only show active instance"
        
        finally:
            # Restore simple_chat2 to active status
            await db_session.execute(
                update(AgentInstanceModel)
                .where(AgentInstanceModel.instance_slug == "simple_chat2")
                .values(status="active")
            )
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_get_instance_metadata(self, db_session):
        """Get metadata for specific instances."""
        from app.agents.instance_loader import get_instance_metadata
        
        # Test default_account/simple_chat1
        metadata = await get_instance_metadata("default_account", "simple_chat1", session=db_session)
        
        assert metadata["instance_slug"] == "simple_chat1", "Should have correct slug"
        assert metadata["account_slug"] == "default_account", "Should have correct account"
        assert metadata["agent_type"] == "simple_chat", "Should have correct type"
        assert metadata["status"] == "active", "Should be active"
        assert "id" in metadata, "Should have id"
        assert "account_id" in metadata, "Should have account_id"
        assert "created_at" in metadata, "Should have created_at"
        assert "updated_at" in metadata, "Should have updated_at"
        
        # Test acme/acme_chat1
        metadata2 = await get_instance_metadata("acme", "acme_chat1", session=db_session)
        
        assert metadata2["instance_slug"] == "acme_chat1", "Should have correct slug"
        assert metadata2["account_slug"] == "acme", "Should have correct account"
        assert metadata2["display_name"] == "Acme Chat 1", "Should have display name"
    
    @pytest.mark.asyncio
    async def test_list_invalid_account(self, db_session):
        """Verify error when listing instances for invalid account."""
        from app.agents.instance_loader import list_account_instances
        
        with pytest.raises(ValueError) as exc_info:
            await list_account_instances("nonexistent_account", session=db_session)
        
        assert "not found" in str(exc_info.value).lower(), "Should have 'not found' in error"
        assert "nonexistent_account" in str(exc_info.value), "Should mention the account slug"
    
    @pytest.mark.asyncio
    async def test_get_metadata_invalid_account(self, db_session):
        """Verify error when getting metadata for invalid account."""
        from app.agents.instance_loader import get_instance_metadata
        
        with pytest.raises(ValueError) as exc_info:
            await get_instance_metadata("nonexistent_account", "simple_chat1", session=db_session)
        
        assert "not found" in str(exc_info.value).lower(), "Should have 'not found' in error"
    
    @pytest.mark.asyncio
    async def test_get_metadata_invalid_instance(self, db_session):
        """Verify error when getting metadata for invalid instance."""
        from app.agents.instance_loader import get_instance_metadata
        
        with pytest.raises(ValueError) as exc_info:
            await get_instance_metadata("default_account", "nonexistent_instance", session=db_session)
        
        assert "not found" in str(exc_info.value).lower(), "Should have 'not found' in error"
        assert "nonexistent_instance" in str(exc_info.value), "Should mention the instance slug"
    
    @pytest.mark.asyncio
    async def test_get_metadata_inactive_instance(self, db_session):
        """Verify error when getting metadata for inactive instance."""
        from app.agents.instance_loader import get_instance_metadata
        from app.models.agent_instance import AgentInstanceModel
        from sqlalchemy import update
        
        # Mark simple_chat2 as inactive
        await db_session.execute(
            update(AgentInstanceModel)
            .where(AgentInstanceModel.instance_slug == "simple_chat2")
            .values(status="inactive")
        )
        await db_session.commit()
        
        try:
            with pytest.raises(ValueError) as exc_info:
                await get_instance_metadata("default_account", "simple_chat2", session=db_session)
            
            assert "inactive" in str(exc_info.value).lower(), "Should mention inactive status"
        
        finally:
            # Restore simple_chat2 to active status
            await db_session.execute(
                update(AgentInstanceModel)
                .where(AgentInstanceModel.instance_slug == "simple_chat2")
                .values(status="active")
            )
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_instance_isolation(self, db_session):
        """Verify instances are properly isolated by account."""
        from app.agents.instance_loader import list_account_instances
        
        # Get instances for both accounts
        default_instances = await list_account_instances("default_account", session=db_session)
        acme_instances = await list_account_instances("acme", session=db_session)
        
        # Extract slugs
        default_slugs = [inst["instance_slug"] for inst in default_instances]
        acme_slugs = [inst["instance_slug"] for inst in acme_instances]
        
        # Verify no overlap - acme instances shouldn't appear in default
        for slug in acme_slugs:
            assert slug not in default_slugs, f"Acme instance {slug} should not appear in default_account"
        
        # Verify default instances don't appear in acme
        for slug in default_slugs:
            assert slug not in acme_slugs, f"Default instance {slug} should not appear in acme account"
        
        # Verify expected instances are present
        assert "simple_chat1" in default_slugs, "default_account should have simple_chat1"
        assert "simple_chat2" in default_slugs, "default_account should have simple_chat2"
        assert "acme_chat1" in acme_slugs, "acme should have acme_chat1"
