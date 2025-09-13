"""
Integration Tests for Agent Conversation Loading - TASK 0017-003-005

Tests complete workflows with real database connections, agent integration,
and cross-endpoint conversation continuity functionality.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
import time

from app.database import initialize_database, get_database_service
from app.models.session import Session
from app.models.message import Message
from app.services.agent_session import load_agent_conversation, get_session_stats
from app.services.message_service import get_message_service
from app.agents.simple_chat import simple_chat
from pydantic_ai.messages import ModelRequest, ModelResponse


@pytest.mark.integration
class TestAgentConversationLoadingIntegration:
    """Integration tests for complete agent conversation loading workflow."""
    
    @pytest.fixture(scope="function")
    async def setup_database(self):
        """Initialize database for integration testing."""
        await initialize_database()
        yield
        # Cleanup handled by test database isolation
    
    @pytest.fixture
    async def test_session(self, setup_database):
        """Create a test session for conversation testing."""
        db_service = get_database_service()
        async with db_service.get_session() as db_session:
            test_session = Session(
                session_key=f"test-agent-conversation-{uuid.uuid4().hex[:8]}",
                email=None,
                is_anonymous=True,
                created_at=datetime.now(timezone.utc),
                last_activity_at=datetime.now(timezone.utc),
                metadata={"test": "agent_conversation_loading"}
            )
            
            db_session.add(test_session)
            await db_session.commit()
            await db_session.refresh(test_session)
            
            yield str(test_session.id)
    
    @pytest.mark.asyncio
    async def test_load_agent_conversation_with_db(self, test_session):
        """CHUNK 0017-003-005-01: Test full workflow with real database messages."""
        session_id = test_session
        message_service = get_message_service()
        
        # Add test messages to database
        test_messages = [
            {"role": "human", "content": "Hello from integration test", "source": "pytest"},
            {"role": "assistant", "content": "Response from integration test", "source": "pytest"},
            {"role": "human", "content": "Follow up question", "source": "pytest"},
            {"role": "assistant", "content": "Follow up answer", "source": "pytest"}
        ]
        
        saved_ids = []
        for msg_data in test_messages:
            msg_id = await message_service.save_message(
                session_id=uuid.UUID(session_id),
                role=msg_data["role"],
                content=msg_data["content"],
                metadata={"source": msg_data["source"], "test": "integration"}
            )
            saved_ids.append(msg_id)
        
        # Test loading conversation
        conversation = await load_agent_conversation(session_id)
        
        # Verify conversation loading
        assert len(conversation) == 4
        assert isinstance(conversation[0], ModelRequest)
        assert isinstance(conversation[1], ModelResponse)
        assert conversation[0].parts[0].content == "Hello from integration test"
        assert conversation[1].parts[0].content == "Response from integration test"
        
        # Verify chronological ordering
        assert conversation[2].parts[0].content == "Follow up question"
        assert conversation[3].parts[0].content == "Follow up answer"
    
    @pytest.mark.asyncio
    async def test_simple_chat_cross_endpoint_continuity(self, test_session):
        """CHUNK 0017-003-005-02: Test cross-endpoint conversation flow."""
        session_id = test_session
        message_service = get_message_service()
        
        # Simulate messages from legacy endpoint
        legacy_user_msg = await message_service.save_message(
            session_id=uuid.UUID(session_id),
            role="human",
            content="I started this conversation on the legacy endpoint",
            metadata={"source": "legacy_endpoint", "test": "cross_endpoint"}
        )
        
        legacy_assistant_msg = await message_service.save_message(
            session_id=uuid.UUID(session_id),
            role="assistant", 
            content="This is a response from the legacy system",
            metadata={"source": "legacy_endpoint", "test": "cross_endpoint"}
        )
        
        # Now use simple_chat - should automatically load history
        response = await simple_chat(
            message="Can you remember what we discussed earlier?",
            session_id=session_id
        )
        
        # Verify response contains expected keys
        assert 'response' in response
        assert 'usage' in response
        assert 'session_continuity' in response
        
        # Verify session continuity stats
        continuity = response['session_continuity']
        assert continuity['total_messages'] >= 2  # At least the legacy messages
        assert continuity['cross_endpoint_continuity'] == True
        assert continuity['analytics']['has_conversation'] == True
        
        # Check for cross-endpoint evidence in detailed stats
        if 'recent_activity' in continuity:
            assert 'legacy_endpoint' in continuity['recent_activity']['sources_detected']
            assert continuity['recent_activity']['cross_endpoint_evidence'] == True
    
    @pytest.mark.asyncio
    async def test_session_analytics_end_to_end(self, test_session):
        """CHUNK 0017-003-005-03: Test analytics with real multi-source conversations."""
        session_id = test_session
        message_service = get_message_service()
        
        # Add messages from multiple sources
        multi_source_messages = [
            {"role": "human", "content": "Message from simple chat", "source": "simple_chat"},
            {"role": "assistant", "content": "Response to simple chat", "source": "simple_chat"},
            {"role": "human", "content": "Message from legacy", "source": "legacy_endpoint"},
            {"role": "assistant", "content": "Response to legacy", "source": "legacy_endpoint"},
            {"role": "system", "content": "System message", "source": "system_init"}
        ]
        
        for msg_data in multi_source_messages:
            await message_service.save_message(
                session_id=uuid.UUID(session_id),
                role=msg_data["role"],
                content=msg_data["content"],
                metadata={"source": msg_data["source"], "test": "analytics"}
            )
        
        # Test comprehensive analytics
        stats = await get_session_stats(session_id)
        
        # Verify comprehensive analytics structure
        assert stats['total_messages'] == 5
        assert stats['cross_endpoint_continuity'] == True
        
        # Verify message breakdown
        assert stats['message_breakdown']['human'] == 2
        assert stats['message_breakdown']['assistant'] == 2
        assert stats['message_breakdown']['system'] == 1
        
        # Verify cross-endpoint detection
        assert stats['recent_activity']['cross_endpoint_evidence'] == True
        sources = stats['recent_activity']['sources_detected']
        assert 'simple_chat' in sources
        assert 'legacy_endpoint' in sources
        assert 'system_init' in sources
        
        # Verify analytics metrics
        assert stats['analytics']['has_conversation'] == True
        assert stats['analytics']['conversation_turns'] == 2
        assert stats['analytics']['session_health'] == 'active'
        assert stats['analytics']['bridging_capable'] == True
    
    @pytest.mark.asyncio
    async def test_agent_conversation_loading_workflow(self, test_session):
        """Feature-level: Complete conversation loading and continuity workflow."""
        session_id = test_session
        message_service = get_message_service()
        
        # Phase 1: Start conversation on legacy endpoint
        await message_service.save_message(
            session_id=uuid.UUID(session_id),
            role="human",
            content="Start conversation on legacy",
            metadata={"source": "legacy_endpoint"}
        )
        
        await message_service.save_message(
            session_id=uuid.UUID(session_id),
            role="assistant",
            content="Legacy response",
            metadata={"source": "legacy_endpoint"}
        )
        
        # Phase 2: Continue on simple chat agent - should load history
        agent_response = await simple_chat(
            message="Continue conversation on agent endpoint",
            session_id=session_id
        )
        
        # Verify agent has access to full conversation context
        assert agent_response['session_continuity']['total_messages'] >= 2
        assert agent_response['session_continuity']['analytics']['has_conversation'] == True
        
        # Phase 3: Verify conversation history loading
        loaded_history = await load_agent_conversation(session_id)
        assert len(loaded_history) >= 2  # At minimum the original messages
        
        # Phase 4: Add more messages and verify continuity
        await message_service.save_message(
            session_id=uuid.UUID(session_id),
            role="human", 
            content="Final test message",
            metadata={"source": "final_test"}
        )
        
        final_stats = await get_session_stats(session_id)
        assert final_stats['recent_activity']['cross_endpoint_evidence'] == True
        assert len(final_stats['recent_activity']['sources_detected']) >= 2
    
    @pytest.mark.asyncio
    async def test_conversation_loading_performance(self, test_session):
        """Performance test: Ensure history loading doesn't impact response times significantly."""
        session_id = test_session
        message_service = get_message_service()
        
        # Add many messages to test performance impact
        for i in range(20):  # Within default limit of 50
            await message_service.save_message(
                session_id=uuid.UUID(session_id),
                role="human" if i % 2 == 0 else "assistant",
                content=f"Performance test message {i}",
                metadata={"source": "performance_test"}
            )
        
        # Measure loading time
        start_time = time.time()
        conversation = await load_agent_conversation(session_id)
        load_time = time.time() - start_time
        
        # Verify performance (should be under 1 second for 20 messages)
        assert load_time < 1.0, f"Loading took too long: {load_time:.3f}s"
        assert len(conversation) == 20
        
        # Measure stats calculation time
        start_time = time.time()
        stats = await get_session_stats(session_id)
        stats_time = time.time() - start_time
        
        assert stats_time < 0.5, f"Stats calculation took too long: {stats_time:.3f}s"
        assert stats['total_messages'] == 20
    
    @pytest.mark.asyncio
    async def test_conversation_loading_edge_cases(self, test_session):
        """Error handling: Test edge cases and error scenarios."""
        # Test invalid session ID
        with pytest.raises(ValueError):
            await load_agent_conversation("invalid-uuid-format")
        
        # Test non-existent session
        nonexistent_session = str(uuid.uuid4())
        empty_conversation = await load_agent_conversation(nonexistent_session)
        assert empty_conversation == []
        
        empty_stats = await get_session_stats(nonexistent_session)
        assert empty_stats['total_messages'] == 0
        assert empty_stats['cross_endpoint_continuity'] == False
        
        # Test session with malformed messages (missing content)
        session_id = test_session
        message_service = get_message_service()
        
        # Add a message with empty content (should be handled gracefully)
        await message_service.save_message(
            session_id=uuid.UUID(session_id),
            role="human",
            content="",  # Empty content
            metadata={"source": "edge_case_test"}
        )
        
        # Should handle gracefully
        conversation = await load_agent_conversation(session_id)
        stats = await get_session_stats(session_id)
        
        # Verify system handles edge cases without crashing
        assert isinstance(conversation, list)
        assert isinstance(stats, dict)
        assert 'total_messages' in stats


if __name__ == "__main__":
    # Run tests: pytest backend/tests/integration/test_agent_conversation_loading.py -v
    pytest.main([__file__, "-v"])
