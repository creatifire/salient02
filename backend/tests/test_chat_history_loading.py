"""
Test script for chat history loading functionality.

This script tests the chat history loading feature implemented in 
Epic 0004-004-001-02 - CHUNK - Chat history loading.

Tests covered:
- Loading existing messages when session resumes
- Empty history handling
- Message limit enforcement (50 messages)
- Role filtering (excluding system messages from UI)
- Message formatting for template rendering
"""

import asyncio
import uuid
from datetime import datetime, timezone

# Import test dependencies
import sys
from pathlib import Path

# Add backend app to path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import _load_chat_history_for_session
from app.services.message_service import get_message_service
from app.database import get_database_service, initialize_database
from app.models.session import Session
from app.models.message import Message


class ChatHistoryLoadingTest:
    """Test suite for chat history loading functionality."""
    
    def __init__(self):
        """Initialize test suite."""
        self.test_session_id = None
        
    async def setup_test_session(self):
        """Create a test session with sample messages."""
        print("🔧 Setting up test session...")
        
        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            # Create test session
            test_session = Session(
                session_key=f"test-history-{uuid.uuid4().hex[:8]}",
                email=None,
                is_anonymous=True,
                created_at=datetime.now(timezone.utc),
                last_activity_at=datetime.now(timezone.utc),
                metadata={"test": True, "purpose": "chat_history_loading"}
            )
            
            db_session.add(test_session)
            await db_session.commit()
            await db_session.refresh(test_session)
            
            self.test_session_id = test_session.id
            print(f"✅ Created test session: {self.test_session_id}")
            
            # Add sample messages
            await self._create_sample_messages(db_session, test_session.id)
    
    async def _create_sample_messages(self, db_session, session_id):
        """Create sample messages for testing."""
        sample_messages = [
            {"role": "system", "content": "You are a helpful sales assistant."},
            {"role": "human", "content": "Hello, what products do you offer?"},
            {"role": "assistant", "content": "We offer SmartFresh storage solutions for agricultural products. Our main products include..."},
            {"role": "human", "content": "Can you tell me more about SmartFresh?"},
            {"role": "assistant", "content": "SmartFresh technology helps extend the freshness of fruits and vegetables by controlling their respiration rate..."},
            {"role": "system", "content": "User showed interest in SmartFresh products."},
            {"role": "human", "content": "What are the pricing options?"},
            {"role": "assistant", "content": "Our pricing varies based on storage capacity and features. Let me connect you with our sales team for a custom quote..."},
        ]
        
        for msg_data in sample_messages:
            message = Message(
                session_id=session_id,
                role=msg_data["role"],
                content=msg_data["content"],
                meta={"test": True},
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(message)
        
        await db_session.commit()
        print(f"✅ Created {len(sample_messages)} sample messages")
    
    async def test_empty_session_history(self):
        """Test chat history loading for session with no messages."""
        print("\n🧪 Testing empty session history...")
        
        # Create empty session
        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            empty_session = Session(
                session_key=f"empty-{uuid.uuid4().hex[:8]}",
                email=None,
                is_anonymous=True,
                created_at=datetime.now(timezone.utc),
                last_activity_at=datetime.now(timezone.utc),
                metadata={"test": True}
            )
            
            db_session.add(empty_session)
            await db_session.commit()
            await db_session.refresh(empty_session)
            
            # Test loading empty history
            history = await _load_chat_history_for_session(empty_session.id)
            
            assert isinstance(history, list), "History should be a list"
            assert len(history) == 0, "Empty session should return empty history"
            print("✅ Empty session history handled correctly")
    
    async def test_chat_history_loading(self):
        """Test main chat history loading functionality."""
        print("\n🧪 Testing chat history loading...")
        
        if not self.test_session_id:
            await self.setup_test_session()
        
        # Load chat history
        history = await _load_chat_history_for_session(self.test_session_id)
        
        # Verify basic structure
        assert isinstance(history, list), "History should be a list"
        assert len(history) > 0, "Should have loaded messages"
        
        # Verify system messages are filtered out
        system_messages = [msg for msg in history if msg.get("original_role") == "system"]
        assert len(system_messages) == 0, "System messages should be filtered from UI display"
        
        # Verify message structure
        for msg in history:
            assert "role" in msg, "Message should have role field"
            assert "content" in msg, "Message should have content field"
            assert "timestamp" in msg, "Message should have timestamp field"
            assert "message_id" in msg, "Message should have message_id field"
            assert msg["role"] in ["user", "bot"], f"Role should be user or bot, got: {msg['role']}"
        
        # Verify conversation flow (human -> assistant mapping)
        user_messages = [msg for msg in history if msg["role"] == "user"]
        bot_messages = [msg for msg in history if msg["role"] == "bot"]
        
        assert len(user_messages) > 0, "Should have user messages"
        assert len(bot_messages) > 0, "Should have bot messages"
        
        print(f"✅ Loaded {len(history)} messages ({len(user_messages)} user, {len(bot_messages)} bot)")
        
        # Print sample for visual verification
        print("\n📋 Sample message structure:")
        if history:
            sample_msg = history[0]
            for key, value in sample_msg.items():
                print(f"  {key}: {repr(value)}")
    
    async def test_message_limit(self):
        """Test that message loading respects the 50-message limit."""
        print("\n🧪 Testing message limit enforcement...")
        
        # Create session with many messages
        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            bulk_session = Session(
                session_key=f"bulk-{uuid.uuid4().hex[:8]}",
                email=None,
                is_anonymous=True,
                created_at=datetime.now(timezone.utc),
                last_activity_at=datetime.now(timezone.utc),
                metadata={"test": True}
            )
            
            db_session.add(bulk_session)
            await db_session.commit()
            await db_session.refresh(bulk_session)
            
            # Create 60 messages (exceeds 50 limit)
            for i in range(60):
                role = "human" if i % 2 == 0 else "assistant"
                message = Message(
                    session_id=bulk_session.id,
                    role=role,
                    content=f"Test message {i+1}",
                    meta={"test": True, "sequence": i+1},
                    created_at=datetime.now(timezone.utc)
                )
                db_session.add(message)
            
            await db_session.commit()
            
            # Load history and verify limit
            history = await _load_chat_history_for_session(bulk_session.id)
            
            assert len(history) <= 50, f"History should be limited to 50 messages, got {len(history)}"
            print(f"✅ Message limit enforced: {len(history)} messages loaded (max 50)")
    
    async def test_invalid_session(self):
        """Test error handling for invalid session ID."""
        print("\n🧪 Testing invalid session handling...")
        
        # Test with non-existent session ID
        fake_session_id = uuid.uuid4()
        history = await _load_chat_history_for_session(fake_session_id)
        
        assert isinstance(history, list), "Should return list even for invalid session"
        assert len(history) == 0, "Invalid session should return empty history"
        print("✅ Invalid session handled gracefully")
    
    async def cleanup(self):
        """Clean up test data."""
        print("\n🧹 Cleaning up test data...")
        
        if self.test_session_id:
            db_service = get_database_service()
            async with db_service.get_session() as db_session:
                # Delete test messages
                from sqlalchemy import delete
                await db_session.execute(
                    delete(Message).where(Message.session_id == self.test_session_id)
                )
                
                # Delete test session
                await db_session.execute(
                    delete(Session).where(Session.id == self.test_session_id)
                )
                
                await db_session.commit()
                print("✅ Test data cleaned up")


async def run_tests():
    """Run all chat history loading tests."""
    print("🚀 Starting Chat History Loading Tests")
    print("="*50)
    
    try:
        # Initialize database
        await initialize_database()
        
        # Create test instance
        test_suite = ChatHistoryLoadingTest()
        
        # Run tests
        await test_suite.test_empty_session_history()
        await test_suite.setup_test_session()
        await test_suite.test_chat_history_loading()
        await test_suite.test_message_limit()
        await test_suite.test_invalid_session()
        
        # Cleanup
        await test_suite.cleanup()
        
        print("\n" + "="*50)
        print("✅ All tests passed! Chat history loading is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_tests())
    
    if success:
        print("\n🎉 Chat history loading implementation is ready!")
        print("✅ CHUNK 0004-004-001-02 - Chat history loading: COMPLETED")
    else:
        print("\n⚠️ Some tests failed. Please review the implementation.")
