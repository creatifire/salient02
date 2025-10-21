"""
Basic test module for SessionService to verify functionality.

This is a simple test to validate that the session service works correctly
with database operations. For production, this should be moved to a proper
tests/ directory with pytest fixtures.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import asyncio
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_database_service, initialize_database, shutdown_database
from ..models.session import Session
from .session_service import SessionService, SessionError


async def test_session_service() -> None:
    """
    Test basic session service functionality.
    
    This test verifies:
    - Session creation with secure key generation
    - Session lookup by session key
    - Activity timestamp updates
    - Email updates and anonymous flag handling
    - Session activity checking
    """
    print("🧪 Starting session service tests...")
    
    # Initialize database service
    await initialize_database()
    db_service = get_database_service()
    
    try:
        async with db_service.get_session() as session:
            service = SessionService(session)
            
            # Test 1: Create new session
            print("\n📝 Test 1: Creating new session...")
            new_session = await service.create_session()
            
            assert new_session.id is not None
            assert new_session.session_key is not None
            assert len(new_session.session_key) == 32
            assert new_session.is_anonymous is True
            assert new_session.email is None
            assert new_session.created_at is not None
            assert new_session.last_activity_at is not None
            
            print(f"✅ Session created: {new_session.session_key[:8]}...")
            
            # Test 2: Retrieve session by key
            print("\n🔍 Test 2: Retrieving session by key...")
            retrieved_session = await service.get_session_by_key(new_session.session_key)
            
            assert retrieved_session is not None
            assert retrieved_session.id == new_session.id
            assert retrieved_session.session_key == new_session.session_key
            
            print(f"✅ Session retrieved successfully")
            
            # Test 3: Update last activity
            print("\n⏰ Test 3: Updating last activity...")
            original_activity = new_session.last_activity_at
            await asyncio.sleep(0.1)  # Small delay to ensure different timestamp
            
            updated = await service.update_last_activity(new_session.id)
            assert updated is True
            
            # Verify activity was updated
            updated_session = await service.get_session_by_key(new_session.session_key)
            assert updated_session.last_activity_at > original_activity
            
            print(f"✅ Activity updated successfully")
            
            # Test 4: Update session email
            print("\n📧 Test 4: Updating session email...")
            test_email = "test@example.com"
            email_updated = await service.update_session_email(new_session.id, test_email)
            assert email_updated is True
            
            # Verify email and anonymous status
            email_session = await service.get_session_by_key(new_session.session_key)
            assert email_session.email == test_email
            assert email_session.is_anonymous is False
            
            print(f"✅ Email updated successfully")
            
            # Test 5: Session activity check
            print("\n🔄 Test 5: Checking session activity...")
            
            # Active session should return True
            is_active = await service.is_session_active(email_session)
            assert is_active is True
            
            # Test with custom inactivity timeout (very short for testing)
            is_active_short = await service.is_session_active(email_session, inactivity_minutes=0)
            assert is_active_short is False  # Should be expired immediately
            
            print(f"✅ Activity checking works correctly")
            
            # Test 6: Cookie configuration
            print("\n🍪 Test 6: Getting cookie configuration...")
            cookie_config = service.get_cookie_config()
            
            assert "key" in cookie_config
            assert "max_age" in cookie_config
            assert "secure" in cookie_config
            assert "httponly" in cookie_config
            assert "samesite" in cookie_config
            
            print(f"✅ Cookie config retrieved: {cookie_config['key']}")
            
            # Test 7: Session not found scenario
            print("\n❌ Test 7: Testing session not found...")
            nonexistent_session = await service.get_session_by_key("nonexistent_key")
            assert nonexistent_session is None
            
            print(f"✅ Correctly handled nonexistent session")
            
            print("\n🎉 All session service tests passed!")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise
    finally:
        # Clean up database service
        await shutdown_database()


async def test_session_service_with_email() -> None:
    """Test session creation with email from the start."""
    print("\n🧪 Testing session creation with email...")
    
    await initialize_database()
    db_service = get_database_service()
    
    try:
        async with db_service.get_session() as session:
            service = SessionService(session)
            
            # Create session with email
            email = "initial@example.com"
            metadata = {"source": "direct_signup"}
            
            new_session = await service.create_session(
                email=email, 
                metadata=metadata
            )
            
            assert new_session.email == email
            assert new_session.is_anonymous is False
            assert new_session.meta == metadata
            
            print(f"✅ Session with email created successfully")
            
    finally:
        await shutdown_database()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_session_service())
    asyncio.run(test_session_service_with_email())
