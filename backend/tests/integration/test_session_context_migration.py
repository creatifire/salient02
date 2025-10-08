"""
Integration tests for session context migration (nullable account/instance fields).

Tests verify that the migration (5cd8e16e070f) correctly makes sessions.account_id,
sessions.account_slug, and sessions.agent_instance_id nullable while preserving
foreign key constraints.

Progressive Session Context Flow:
1. First request → session created with NULL account/instance
2. User navigates to /accounts/{account}/agents/{instance}/chat
3. Chat endpoint updates session with account_id, account_slug, agent_instance_id
4. Subsequent requests → session loaded with remembered context
"""

import asyncio
import uuid
from datetime import datetime, UTC

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import initialize_database, shutdown_database, get_db_session
from app.main import app


# Suppress async cleanup warnings
pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


@pytest_asyncio.fixture(scope="module")
async def client():
    """Create test client with database initialization."""
    await initialize_database()
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    await shutdown_database()
    await asyncio.sleep(0.1)


@pytest_asyncio.fixture
async def db_session(client):
    """
    Provide clean database session for tests.
    
    Depends on client fixture to ensure database is initialized.
    """
    async for session in get_db_session():
        yield session


class TestSessionFieldsNullable:
    """Test that session account/instance fields are nullable in schema."""
    
    @pytest.mark.asyncio
    async def test_session_fields_nullable(self, db_session):
        """Verify account_id, account_slug, agent_instance_id allow NULL."""
        # Query the database to check column nullability via information_schema
        query = text("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'sessions'
              AND column_name IN ('account_id', 'account_slug', 'agent_instance_id')
        """)
        
        result = await db_session.execute(query)
        rows = result.fetchall()
        
        # Build lookup dict
        nullable_dict = {row[0]: row[1] for row in rows}
        
        # Verify nullable status (is_nullable returns 'YES' or 'NO' from information_schema)
        assert nullable_dict['account_id'] == 'YES', \
            "sessions.account_id should be nullable"
        assert nullable_dict['account_slug'] == 'YES', \
            "sessions.account_slug should be nullable"
        assert nullable_dict['agent_instance_id'] == 'YES', \
            "sessions.agent_instance_id should be nullable"


class TestSessionCreationWithoutContext:
    """Test creating sessions with NULL account/instance context."""
    
    @pytest.mark.asyncio
    async def test_create_session_without_context(self, db_session):
        """Session creation succeeds with NULL values for account/instance."""
        # Use raw SQL to avoid async event loop issues
        query = text("""
            INSERT INTO sessions (id, session_key, account_id, account_slug, agent_instance_id, user_id, is_anonymous, created_at, updated_at)
            VALUES (:id, :session_key, :account_id, :account_slug, :agent_instance_id, :user_id, :is_anonymous, :created_at, :updated_at)
            RETURNING id
        """)
        
        session_id = uuid.uuid4()
        result = await db_session.execute(query, {
            "id": session_id,
            "session_key": f"test_session_{uuid.uuid4().hex[:8]}",
            "account_id": None,  # NULL - no context yet
            "account_slug": None,  # NULL - no context yet
            "agent_instance_id": None,  # NULL - no context yet
            "user_id": None,  # Anonymous session
            "is_anonymous": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })
        await db_session.commit()
        
        # Verify session created successfully by querying it back
        verify_query = text("SELECT account_id, account_slug, agent_instance_id FROM sessions WHERE id = :id")
        result = await db_session.execute(verify_query, {"id": session_id})
        row = result.fetchone()
        
        assert row is not None
        assert row[0] is None  # account_id
        assert row[1] is None  # account_slug
        assert row[2] is None  # agent_instance_id
        
        # Cleanup
        cleanup_query = text("DELETE FROM sessions WHERE id = :id")
        await db_session.execute(cleanup_query, {"id": session_id})
        await db_session.commit()


class TestSessionCreationWithContext:
    """Test creating sessions WITH account/instance context."""
    
    @pytest.mark.asyncio
    async def test_create_session_with_context(self, db_session):
        """Session creation succeeds with valid account/instance."""
        # Get test account and instance using raw SQL to avoid event loop issues
        account_query = text("SELECT id, slug FROM accounts WHERE slug = 'default_account'")
        account_result = await db_session.execute(account_query)
        account_row = account_result.fetchone()
        account_id, account_slug = account_row[0], account_row[1]
        
        instance_query = text("SELECT id FROM agent_instances WHERE instance_slug = 'simple_chat1'")
        instance_result = await db_session.execute(instance_query)
        instance_row = instance_result.fetchone()
        instance_id = instance_row[0]
        
        # Create session WITH context using raw SQL
        query = text("""
            INSERT INTO sessions (id, session_key, account_id, account_slug, agent_instance_id, user_id, is_anonymous, created_at, updated_at)
            VALUES (:id, :session_key, :account_id, :account_slug, :agent_instance_id, :user_id, :is_anonymous, :created_at, :updated_at)
            RETURNING id
        """)
        
        session_id = uuid.uuid4()
        result = await db_session.execute(query, {
            "id": session_id,
            "session_key": f"test_session_{uuid.uuid4().hex[:8]}",
            "account_id": account_id,
            "account_slug": account_slug,
            "agent_instance_id": instance_id,
            "user_id": None,
            "is_anonymous": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })
        await db_session.commit()
        
        # Verify session created successfully with context
        verify_query = text("SELECT account_id, account_slug, agent_instance_id FROM sessions WHERE id = :id")
        result = await db_session.execute(verify_query, {"id": session_id})
        row = result.fetchone()
        
        assert row is not None
        assert row[0] == account_id
        assert row[1] == account_slug
        assert row[2] == instance_id
        
        # Cleanup
        cleanup_query = text("DELETE FROM sessions WHERE id = :id")
        await db_session.execute(cleanup_query, {"id": session_id})
        await db_session.commit()


class TestUpdateSessionContext:
    """Test updating session to add context after creation."""
    
    @pytest.mark.asyncio
    async def test_update_session_context(self, db_session):
        """Can UPDATE session to add account/instance after creation."""
        # Get test account and instance using raw SQL
        account_query = text("SELECT id, slug FROM accounts WHERE slug = 'default_account'")
        account_result = await db_session.execute(account_query)
        account_row = account_result.fetchone()
        account_id, account_slug = account_row[0], account_row[1]
        
        instance_query = text("SELECT id FROM agent_instances WHERE instance_slug = 'simple_chat1'")
        instance_result = await db_session.execute(instance_query)
        instance_row = instance_result.fetchone()
        instance_id = instance_row[0]
        
        # Step 1: Create session WITHOUT context (first request)
        insert_query = text("""
            INSERT INTO sessions (id, session_key, account_id, account_slug, agent_instance_id, user_id, is_anonymous, created_at, updated_at)
            VALUES (:id, :session_key, :account_id, :account_slug, :agent_instance_id, :user_id, :is_anonymous, :created_at, :updated_at)
            RETURNING id
        """)
        
        session_id = uuid.uuid4()
        await db_session.execute(insert_query, {
            "id": session_id,
            "session_key": f"test_session_{uuid.uuid4().hex[:8]}",
            "account_id": None,  # NULL initially
            "account_slug": None,  # NULL initially
            "agent_instance_id": None,  # NULL initially
            "user_id": None,
            "is_anonymous": True,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })
        await db_session.commit()
        
        # Verify initial NULL state
        check_query = text("SELECT account_id, account_slug, agent_instance_id FROM sessions WHERE id = :id")
        result = await db_session.execute(check_query, {"id": session_id})
        row = result.fetchone()
        
        assert row[0] is None  # account_id
        assert row[1] is None  # account_slug
        assert row[2] is None  # agent_instance_id
        
        # Step 2: UPDATE session WITH context (user navigates to agent endpoint)
        update_query = text("""
            UPDATE sessions
            SET account_id = :account_id,
                account_slug = :account_slug,
                agent_instance_id = :agent_instance_id,
                updated_at = :updated_at
            WHERE id = :id
        """)
        
        await db_session.execute(update_query, {
            "id": session_id,
            "account_id": account_id,
            "account_slug": account_slug,
            "agent_instance_id": instance_id,
            "updated_at": datetime.now(UTC)
        })
        await db_session.commit()
        
        # Step 3: Verify session persists context after UPDATE
        result = await db_session.execute(check_query, {"id": session_id})
        row = result.fetchone()
        
        assert row[0] == account_id
        assert row[1] == account_slug
        assert row[2] == instance_id
        
        # Cleanup
        cleanup_query = text("DELETE FROM sessions WHERE id = :id")
        await db_session.execute(cleanup_query, {"id": session_id})
        await db_session.commit()


class TestForeignKeyConstraints:
    """Test that FK constraints are still enforced."""
    
    @pytest.mark.asyncio
    async def test_foreign_keys_still_enforced(self, db_session):
        """Cannot insert invalid UUIDs for account_id/agent_instance_id."""
        # Try to insert session with invalid account_id using raw SQL
        invalid_uuid = uuid.uuid4()
        
        query = text("""
            INSERT INTO sessions (id, session_key, account_id, account_slug, agent_instance_id, user_id, is_anonymous, created_at, updated_at)
            VALUES (:id, :session_key, :account_id, :account_slug, :agent_instance_id, :user_id, :is_anonymous, :created_at, :updated_at)
        """)
        
        # Should raise IntegrityError due to FK constraint violation
        with pytest.raises(IntegrityError) as exc_info:
            await db_session.execute(query, {
                "id": uuid.uuid4(),
                "session_key": f"test_session_{uuid.uuid4().hex[:8]}",
                "account_id": invalid_uuid,  # Invalid FK reference - doesn't exist in accounts table
                "account_slug": "invalid",
                "agent_instance_id": None,
                "user_id": None,
                "is_anonymous": True,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            })
            await db_session.commit()
        
        # Verify it's a foreign key error
        error_message = str(exc_info.value).lower()
        assert "foreign key" in error_message or "fk_sessions_account_id" in error_message
        
        # Rollback failed transaction
        await db_session.rollback()


class TestSessionMiddleware:
    """Test that session middleware creates sessions without errors."""
    
    @pytest.mark.asyncio
    async def test_session_middleware_works(self, client):
        """Session middleware creates session without errors."""
        # Make request to health endpoint (any endpoint will do)
        # Session middleware should create session with NULL context
        response = await client.get("/accounts/default_account/agents/health")
        
        # Should succeed without 500 error (no NotNullViolationError)
        assert response.status_code == 200
        
        # Check response has session cookie
        assert "session_id" in response.cookies or "set-cookie" in response.headers
    
    @pytest.mark.asyncio
    async def test_multiple_requests_same_session(self, client):
        """Multiple requests with same session cookie work correctly."""
        # First request - creates session
        response1 = await client.get("/accounts/default_account/agents/health")
        assert response1.status_code == 200
        
        # Extract session cookie
        cookies = response1.cookies
        
        # Second request - reuses session
        response2 = await client.get(
            "/accounts/acme/agents/health",
            cookies=cookies
        )
        assert response2.status_code == 200
        
        # Both requests should work without errors
        # Session should persist across requests
