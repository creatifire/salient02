"""
Unit tests for MessageService enhancements (CHUNK-0026-010-002).

Tests the new save_message_pair() and extract_tool_calls() methods
added to consolidate duplicate message-saving logic from simple_chat.py.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.services.message_service import MessageService


class TestExtractToolCalls:
    """Test suite for extract_tool_calls() static method."""
    
    def test_extract_tool_calls_with_valid_result(self):
        """Test extracting tool calls from a valid Pydantic AI result."""
        # Create mock ToolCallPart
        from pydantic_ai.messages import ToolCallPart
        
        mock_tool_part = Mock(spec=ToolCallPart)
        mock_tool_part.tool_name = "search_directory"
        mock_tool_part.args = {"query": "cardiology", "limit": 10}
        
        # Create mock message with parts
        mock_message = Mock()
        mock_message.parts = [mock_tool_part]
        
        # Create mock result
        mock_result = Mock()
        mock_result.all_messages = Mock(return_value=[mock_message])
        
        tool_calls = MessageService.extract_tool_calls(mock_result)
        
        assert len(tool_calls) == 1
        assert tool_calls[0]["tool_name"] == "search_directory"
        assert tool_calls[0]["args"] == {"query": "cardiology", "limit": 10}
    
    def test_extract_tool_calls_with_multiple_tools(self):
        """Test extracting multiple tool calls from result."""
        from pydantic_ai.messages import ToolCallPart
        
        # Create mock tool parts
        mock_tool1 = Mock(spec=ToolCallPart)
        mock_tool1.tool_name = "search_directory"
        mock_tool1.args = {"query": "cardiology"}
        
        mock_tool2 = Mock(spec=ToolCallPart)
        mock_tool2.tool_name = "vector_search"
        mock_tool2.args = {"query": "heart disease"}
        
        # Create mock messages
        mock_message1 = Mock()
        mock_message1.parts = [mock_tool1]
        
        mock_message2 = Mock()
        mock_message2.parts = [mock_tool2]
        
        # Create mock result
        mock_result = Mock()
        mock_result.all_messages = Mock(return_value=[mock_message1, mock_message2])
        
        tool_calls = MessageService.extract_tool_calls(mock_result)
        
        assert len(tool_calls) == 2
        assert tool_calls[0]["tool_name"] == "search_directory"
        assert tool_calls[1]["tool_name"] == "vector_search"
    
    def test_extract_tool_calls_no_tools(self):
        """Test extraction when result has no tool calls."""
        # Create mock message with no tool parts
        mock_text_part = Mock(spec=['content'])  # Not a ToolCallPart
        mock_message = Mock()
        mock_message.parts = [mock_text_part]
        
        mock_result = Mock()
        mock_result.all_messages = Mock(return_value=[mock_message])
        
        tool_calls = MessageService.extract_tool_calls(mock_result)
        
        assert tool_calls == []
    
    def test_extract_tool_calls_none_result(self):
        """Test extraction when result is None."""
        tool_calls = MessageService.extract_tool_calls(None)
        assert tool_calls == []
    
    def test_extract_tool_calls_no_messages(self):
        """Test extraction when result has no messages."""
        mock_result = Mock()
        mock_result.all_messages = Mock(return_value=[])
        
        tool_calls = MessageService.extract_tool_calls(mock_result)
        assert tool_calls == []
    
    def test_extract_tool_calls_no_all_messages_method(self):
        """Test extraction when result lacks all_messages() method."""
        mock_result = Mock(spec=['output'])  # No all_messages method
        
        tool_calls = MessageService.extract_tool_calls(mock_result)
        assert tool_calls == []
    
    def test_extract_tool_calls_exception_handling(self):
        """Test that extraction errors are caught and logged."""
        mock_result = Mock()
        mock_result.all_messages = Mock(side_effect=Exception("Unexpected error"))
        
        # Should not raise, should return empty list
        tool_calls = MessageService.extract_tool_calls(mock_result)
        assert tool_calls == []


class TestSaveMessagePair:
    """Test suite for save_message_pair() method."""
    
    @pytest.mark.asyncio
    async def test_save_message_pair_success(self):
        """Test successful atomic save of message pair."""
        service = MessageService()
        
        # Test data
        session_id = uuid4()
        agent_instance_id = uuid4()
        llm_request_id = uuid4()
        user_message = "What is cardiology?"
        assistant_message = "Cardiology is the study of the heart."
        
        # Mock database service and session
        mock_db_service = Mock()
        mock_session = AsyncMock()
        
        # Mock message objects that will be "created"
        mock_user_msg = Mock()
        mock_user_msg.id = uuid4()
        mock_assistant_msg = Mock()
        mock_assistant_msg.id = uuid4()
        
        # Setup session context manager
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.get_session = Mock(return_value=mock_session)
        
        with patch('app.services.message_service.get_database_service', return_value=mock_db_service):
            with patch('app.services.message_service.Message') as MockMessage:
                # Configure Message constructor to return our mocks
                MockMessage.side_effect = [mock_user_msg, mock_assistant_msg]
                
                user_id, assistant_id = await service.save_message_pair(
                    session_id=session_id,
                    agent_instance_id=agent_instance_id,
                    llm_request_id=llm_request_id,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    result=None
                )
        
        # Verify both messages were added
        assert mock_session.add.call_count == 2
        
        # Verify commit and refresh called
        mock_session.commit.assert_called_once()
        assert mock_session.refresh.call_count == 2
        
        # Verify returned IDs
        assert user_id == mock_user_msg.id
        assert assistant_id == mock_assistant_msg.id
    
    @pytest.mark.asyncio
    async def test_save_message_pair_with_tool_calls(self):
        """Test message pair save with tool call extraction."""
        from pydantic_ai.messages import ToolCallPart
        
        service = MessageService()
        
        # Create mock result with tool calls
        mock_tool_part = Mock(spec=ToolCallPart)
        mock_tool_part.tool_name = "search_directory"
        mock_tool_part.args = {"query": "cardiology"}
        
        mock_message = Mock()
        mock_message.parts = [mock_tool_part]
        
        mock_result = Mock()
        mock_result.all_messages = Mock(return_value=[mock_message])
        
        # Test data
        session_id = uuid4()
        agent_instance_id = uuid4()
        
        # Mock database service
        mock_db_service = Mock()
        mock_session = AsyncMock()
        mock_user_msg = Mock(id=uuid4())
        mock_assistant_msg = Mock(id=uuid4())
        
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.get_session = Mock(return_value=mock_session)
        
        with patch('app.services.message_service.get_database_service', return_value=mock_db_service):
            with patch('app.services.message_service.Message') as MockMessage:
                MockMessage.side_effect = [mock_user_msg, mock_assistant_msg]
                
                user_id, assistant_id = await service.save_message_pair(
                    session_id=session_id,
                    agent_instance_id=agent_instance_id,
                    llm_request_id=None,
                    user_message="Find cardiology",
                    assistant_message="Here is the cardiology department.",
                    result=mock_result
                )
        
        # Verify Message constructor was called twice
        assert MockMessage.call_count == 2
        
        # Verify assistant message has tool_calls metadata
        assistant_call = MockMessage.call_args_list[1]
        assert assistant_call[1]['meta'] is not None
        assert 'tool_calls' in assistant_call[1]['meta']
        assert len(assistant_call[1]['meta']['tool_calls']) == 1
    
    @pytest.mark.asyncio
    async def test_save_message_pair_invalid_session_id(self):
        """Test validation error for invalid session_id."""
        service = MessageService()
        
        with pytest.raises(ValueError, match="Invalid session_id format"):
            await service.save_message_pair(
                session_id="invalid-uuid",
                agent_instance_id=uuid4(),
                llm_request_id=None,
                user_message="Test",
                assistant_message="Response",
                result=None
            )
    
    @pytest.mark.asyncio
    async def test_save_message_pair_invalid_agent_instance_id(self):
        """Test validation error for invalid agent_instance_id."""
        service = MessageService()
        
        with pytest.raises(ValueError, match="Invalid agent_instance_id format"):
            await service.save_message_pair(
                session_id=uuid4(),
                agent_instance_id="invalid-uuid",
                llm_request_id=None,
                user_message="Test",
                assistant_message="Response",
                result=None
            )
    
    @pytest.mark.asyncio
    async def test_save_message_pair_empty_user_message(self):
        """Test validation error for empty user message."""
        service = MessageService()
        
        with pytest.raises(ValueError, match="User message content cannot be empty"):
            await service.save_message_pair(
                session_id=uuid4(),
                agent_instance_id=uuid4(),
                llm_request_id=None,
                user_message="   ",  # Empty after strip
                assistant_message="Response",
                result=None
            )
    
    @pytest.mark.asyncio
    async def test_save_message_pair_empty_assistant_message(self):
        """Test validation error for empty assistant message."""
        service = MessageService()
        
        with pytest.raises(ValueError, match="Assistant message content cannot be empty"):
            await service.save_message_pair(
                session_id=uuid4(),
                agent_instance_id=uuid4(),
                llm_request_id=None,
                user_message="Test",
                assistant_message="",
                result=None
            )
    
    @pytest.mark.asyncio
    async def test_save_message_pair_string_uuid_conversion(self):
        """Test that string UUIDs are properly converted."""
        service = MessageService()
        
        session_id = str(uuid4())
        agent_instance_id = str(uuid4())
        llm_request_id = str(uuid4())
        
        mock_db_service = Mock()
        mock_session = AsyncMock()
        mock_user_msg = Mock(id=uuid4())
        mock_assistant_msg = Mock(id=uuid4())
        
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.get_session = Mock(return_value=mock_session)
        
        with patch('app.services.message_service.get_database_service', return_value=mock_db_service):
            with patch('app.services.message_service.Message') as MockMessage:
                MockMessage.side_effect = [mock_user_msg, mock_assistant_msg]
                
                user_id, assistant_id = await service.save_message_pair(
                    session_id=session_id,
                    agent_instance_id=agent_instance_id,
                    llm_request_id=llm_request_id,
                    user_message="Test",
                    assistant_message="Response",
                    result=None
                )
        
        # Verify successful execution (no ValueError raised)
        assert user_id == mock_user_msg.id
        assert assistant_id == mock_assistant_msg.id
    
    @pytest.mark.asyncio
    async def test_save_message_pair_transaction_rollback_on_error(self):
        """Test that transaction is rolled back on error."""
        service = MessageService()
        
        mock_db_service = Mock()
        mock_session = AsyncMock()
        
        # Simulate commit failure
        mock_session.commit.side_effect = Exception("Database error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_service.get_session = Mock(return_value=mock_session)
        
        with patch('app.services.message_service.get_database_service', return_value=mock_db_service):
            with pytest.raises(Exception, match="Database error"):
                await service.save_message_pair(
                    session_id=uuid4(),
                    agent_instance_id=uuid4(),
                    llm_request_id=None,
                    user_message="Test",
                    assistant_message="Response",
                    result=None
                )
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()

