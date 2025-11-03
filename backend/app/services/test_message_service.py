"""
Test module for MessageService functionality.

This module provides comprehensive testing for the message service,
including unit tests for all core functionality and integration tests
with the database layer.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import asyncio
import uuid
from datetime import datetime, timezone

from .message_service import MessageService, get_message_service
from ..models.message import Message
from ..database import get_database_service, initialize_database


class TestMessageService:
    """Test suite for MessageService functionality."""
    
    def __init__(self):
        """Initialize test suite."""
        self.service = MessageService()
        self.sample_session_id = None  # Will be created in setup
    
    async def setup_test_session(self):
        """Create a test session for message testing."""
        if self.sample_session_id is None:
            # Create a session manually using direct database access
            from ..models.session import Session
            import uuid
            from datetime import datetime, timezone
            
            db_service = get_database_service()
            async with db_service.get_session() as db_session:
                # Create a test session
                test_session = Session(
                    session_key=f"test-session-{uuid.uuid4().hex[:8]}",
                    email=None,
                    is_anonymous=True,
                    created_at=datetime.now(timezone.utc),
                    last_activity_at=datetime.now(timezone.utc),
                    metadata={"test": True}
                )
                
                db_session.add(test_session)
                await db_session.commit()
                await db_session.refresh(test_session)
                
                self.sample_session_id = test_session.id
                print(f"📋 Created test session ID: {self.sample_session_id}")
    
    async def test_save_message_basic(self):
        """Test basic message saving functionality."""
        message_id = await self.service.save_message(
            session_id=self.sample_session_id,
            role="human",
            content="Hello, this is a test message"
        )
        
        assert isinstance(message_id, uuid.UUID)
        print(f"✅ Message saved with ID: {message_id}")
    
    async def test_save_message_with_metadata(self):
        """Test message saving with metadata."""
        metadata = {
            "source": "test_suite",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_flag": True
        }
        
        message_id = await self.service.save_message(
            session_id=self.sample_session_id,
            role="assistant",
            content="This is a response with metadata",
            metadata=metadata
        )
        
        assert isinstance(message_id, uuid.UUID)
        print(f"✅ Message with metadata saved: {message_id}")
    
    async def test_get_session_messages(self):
        """Test retrieving messages for a session."""
        # Save a few messages first
        messages_to_save = [
            {"role": "human", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "human", "content": "Second message"},
            {"role": "assistant", "content": "Second response"}
        ]
        
        saved_ids = []
        for msg_data in messages_to_save:
            msg_id = await self.service.save_message(
                session_id=self.sample_session_id,
                role=msg_data["role"],
                content=msg_data["content"]
            )
            saved_ids.append(msg_id)
        
        # Retrieve messages
        messages = await self.service.get_session_messages(self.sample_session_id)
        
        assert len(messages) >= len(messages_to_save)
        assert all(msg.session_id == self.sample_session_id for msg in messages)
        print(f"✅ Retrieved {len(messages)} messages for session")
    
    async def test_get_recent_context(self):
        """Test getting recent context for LLM."""
        # Save messages with different roles
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "human", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4"},
            {"role": "human", "content": "What about 3+3?"},
            {"role": "assistant", "content": "3+3 equals 6"}
        ]
        
        for msg_data in test_messages:
            await self.service.save_message(
                session_id=self.sample_session_id,
                role=msg_data["role"],
                content=msg_data["content"]
            )
        
        # Get context
        context = await self.service.get_recent_context(self.sample_session_id, limit=3)
        
        assert len(context) <= 3
        assert all("role" in msg and "content" in msg for msg in context)
        print(f"✅ Retrieved context with {len(context)} messages")
        
        # Test context without system messages
        user_context = await self.service.get_recent_context(
            self.sample_session_id, limit=5, include_system=False
        )
        
        assert all(msg["role"] != "system" for msg in user_context)
        print(f"✅ Retrieved user context without system messages")
    
    async def test_message_count(self):
        """Test message counting functionality."""
        # Initial count should be 0
        initial_count = await self.service.get_message_count(self.sample_session_id)
        
        # Save a few messages
        for i in range(3):
            await self.service.save_message(
                session_id=self.sample_session_id,
                role="human",
                content=f"Test message {i+1}"
            )
        
        # Count should increase
        final_count = await self.service.get_message_count(self.sample_session_id)
        
        assert final_count >= initial_count + 3
        print(f"✅ Message count: {initial_count} -> {final_count}")
    
    async def test_invalid_inputs(self):
        """Test validation of invalid inputs."""
        invalid_session_id = "not-a-uuid"
        
        # Test invalid session ID
        try:
            await self.service.save_message(
                session_id=invalid_session_id,
                role="human",
                content="This should fail"
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid session ID properly rejected")
        
        # Test invalid role
        try:
            await self.service.save_message(
                session_id=uuid.uuid4(),
                role="invalid_role",
                content="This should fail"
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid role properly rejected")
        
        # Test empty content
        try:
            await self.service.save_message(
                session_id=uuid.uuid4(),
                role="human",
                content=""
            )
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Empty content properly rejected")


async def run_tests():
    """Run all message service tests."""
    print("🧪 Starting MessageService Tests...")
    
    # Initialize database for testing
    print("🔌 Initializing database...")
    try:
        await initialize_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    test_instance = TestMessageService()
    
    try:
        # Set up test session first
        await test_instance.setup_test_session()
        
        # Run tests
        await test_instance.test_save_message_basic()
        await test_instance.test_save_message_with_metadata()
        await test_instance.test_get_session_messages()
        await test_instance.test_get_recent_context()
        await test_instance.test_message_count()
        await test_instance.test_invalid_inputs()
        
        print("\n🎉 All MessageService tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_tests())
