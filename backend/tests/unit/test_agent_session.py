"""
Unit Tests for Agent Session Service - TASK 0017-003-005

Tests the agent session service functions in isolation without external dependencies.
Focuses on message conversion logic, stats calculation, and error handling.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from app.services.agent_session import load_agent_conversation, get_session_stats
from app.models.message import Message
from pydantic_ai.messages import ModelRequest, ModelResponse


class TestLoadAgentConversation:
    """Unit tests for load_agent_conversation function - CHUNK 0017-003-005-01"""
    
    @pytest.fixture
    def mock_message_service(self):
        """Mock message service for isolated testing."""
        service = Mock()
        service.get_session_messages = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_db_messages(self):
        """Sample database messages for testing conversion."""
        session_id = uuid.uuid4()
        return [
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="human",
                content="Hello, can you help me?",
                created_at=datetime.now(timezone.utc),
                meta={"source": "test"}
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="assistant", 
                content="Of course! How can I assist you?",
                created_at=datetime.now(timezone.utc),
                meta={"source": "test"}
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="system",
                content="System initialization message",
                created_at=datetime.now(timezone.utc),
                meta={"source": "system"}
            )
        ]
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_load_agent_conversation_empty_session(self, mock_get_service):
        """Test loading conversation from empty session returns empty list."""
        mock_service = Mock()
        mock_service.get_session_messages = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service
        
        session_id = str(uuid.uuid4())
        result = await load_agent_conversation(session_id)
        
        assert result == []
        mock_service.get_session_messages.assert_called_once_with(
            session_id=uuid.UUID(session_id),
            limit=50
        )
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_load_agent_conversation_message_conversion(self, mock_get_service, sample_db_messages):
        """Test proper conversion of DB messages to Pydantic AI format."""
        mock_service = Mock()
        mock_service.get_session_messages = AsyncMock(return_value=sample_db_messages)
        mock_get_service.return_value = mock_service
        
        session_id = str(uuid.uuid4())
        result = await load_agent_conversation(session_id)
        
        # Should have 2 messages (human + assistant, system message skipped)
        assert len(result) == 2
        
        # First message should be ModelRequest (human)
        assert isinstance(result[0], ModelRequest)
        assert result[0].parts[0].content == "Hello, can you help me?"
        
        # Second message should be ModelResponse (assistant)
        assert isinstance(result[1], ModelResponse)
        assert result[1].parts[0].content == "Of course! How can I assist you?"
        assert result[1].model_name == "agent-session"
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service') 
    async def test_load_agent_conversation_user_role_mapping(self, mock_get_service):
        """Test that both 'human' and 'user' roles map to ModelRequest."""
        session_id = uuid.uuid4()
        db_messages = [
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="user",  # Different role variant
                content="User message",
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        mock_service = Mock()
        mock_service.get_session_messages = AsyncMock(return_value=db_messages)
        mock_get_service.return_value = mock_service
        
        result = await load_agent_conversation(str(session_id))
        
        assert len(result) == 1
        assert isinstance(result[0], ModelRequest)
        assert result[0].parts[0].content == "User message"
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_load_agent_conversation_invalid_session_id(self, mock_get_service):
        """Test handling of invalid session ID formats."""
        mock_service = Mock()
        mock_service.get_session_messages = AsyncMock(side_effect=ValueError("Invalid UUID"))
        mock_get_service.return_value = mock_service
        
        # Should handle invalid session ID gracefully
        with pytest.raises(ValueError):
            await load_agent_conversation("invalid-uuid")


class TestGetSessionStats:
    """Unit tests for get_session_stats function - CHUNK 0017-003-005-03"""
    
    @pytest.fixture
    def mock_message_service(self):
        """Mock message service for stats testing."""
        service = Mock()
        service.get_message_count = AsyncMock()
        service.get_session_messages = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_messages_for_stats(self):
        """Sample messages with various roles and sources."""
        session_id = uuid.uuid4()
        return [
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="human",
                content="First human message",
                meta={"source": "simple_chat"}
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="assistant",
                content="First assistant response",
                meta={"source": "simple_chat"}
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="human",
                content="Second human message",
                meta={"source": "legacy_endpoint"}
            ),
            Message(
                id=uuid.uuid4(),
                session_id=session_id,
                role="assistant",
                content="Second assistant response", 
                meta={"source": "legacy_endpoint"}
            )
        ]
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_get_session_stats_empty_session(self, mock_get_service):
        """Test stats calculation for empty session."""
        mock_service = Mock()
        mock_service.get_message_count = AsyncMock(return_value=0)
        mock_service.get_session_messages = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service
        
        session_id = str(uuid.uuid4())
        stats = await get_session_stats(session_id)
        
        assert stats['total_messages'] == 0
        assert stats['session_id'] == session_id
        assert stats['cross_endpoint_continuity'] == False
        assert stats['message_breakdown'] == {}
        assert stats['analytics']['session_health'] == 'empty'
        assert stats['analytics']['has_conversation'] == False
        assert stats['analytics']['conversation_turns'] == 0
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_get_session_stats_with_conversation(self, mock_get_service, sample_messages_for_stats):
        """Test comprehensive stats calculation with multi-source conversation."""
        mock_service = Mock()
        mock_service.get_message_count = AsyncMock(return_value=4)
        mock_service.get_session_messages = AsyncMock(return_value=sample_messages_for_stats)
        mock_get_service.return_value = mock_service
        
        session_id = str(uuid.uuid4())
        stats = await get_session_stats(session_id)
        
        # Basic stats
        assert stats['total_messages'] == 4
        assert stats['cross_endpoint_continuity'] == True
        
        # Message breakdown
        assert stats['message_breakdown']['human'] == 2
        assert stats['message_breakdown']['assistant'] == 2
        
        # Cross-endpoint detection
        assert stats['recent_activity']['cross_endpoint_evidence'] == True
        assert 'simple_chat' in stats['recent_activity']['sources_detected']
        assert 'legacy_endpoint' in stats['recent_activity']['sources_detected']
        
        # Analytics
        assert stats['analytics']['has_conversation'] == True
        assert stats['analytics']['conversation_turns'] == 2  # min(human=2, assistant=2)
        assert stats['analytics']['session_health'] == 'active'
        assert stats['analytics']['bridging_capable'] == True
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_get_session_stats_unbalanced_conversation(self, mock_get_service):
        """Test stats with unbalanced human/assistant messages."""
        session_id = uuid.uuid4()
        # More human messages than assistant responses
        unbalanced_messages = [
            Message(id=uuid.uuid4(), session_id=session_id, role="human", content="Msg 1"),
            Message(id=uuid.uuid4(), session_id=session_id, role="human", content="Msg 2"), 
            Message(id=uuid.uuid4(), session_id=session_id, role="human", content="Msg 3"),
            Message(id=uuid.uuid4(), session_id=session_id, role="assistant", content="Response 1")
        ]
        
        mock_service = Mock()
        mock_service.get_message_count = AsyncMock(return_value=4)
        mock_service.get_session_messages = AsyncMock(return_value=unbalanced_messages)
        mock_get_service.return_value = mock_service
        
        stats = await get_session_stats(str(session_id))
        
        assert stats['message_breakdown']['human'] == 3
        assert stats['message_breakdown']['assistant'] == 1
        assert stats['analytics']['conversation_turns'] == 1  # min(3, 1)
        assert stats['analytics']['has_conversation'] == True  # Both human and assistant present
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.get_message_service')
    async def test_get_session_stats_no_metadata_sources(self, mock_get_service):
        """Test stats calculation when messages have no metadata sources."""
        session_id = uuid.uuid4()
        messages_no_meta = [
            Message(id=uuid.uuid4(), session_id=session_id, role="human", content="Msg", meta=None),
            Message(id=uuid.uuid4(), session_id=session_id, role="assistant", content="Response", meta={})
        ]
        
        mock_service = Mock()
        mock_service.get_message_count = AsyncMock(return_value=2)
        mock_service.get_session_messages = AsyncMock(return_value=messages_no_meta)
        mock_get_service.return_value = mock_service
        
        stats = await get_session_stats(str(session_id))
        
        assert stats['recent_activity']['sources_detected'] == []
        assert stats['recent_activity']['cross_endpoint_evidence'] == False
        assert stats['analytics']['has_conversation'] == True


if __name__ == "__main__":
    # Run tests: pytest backend/tests/unit/test_agent_session.py -v
    pytest.main([__file__, "-v"])
