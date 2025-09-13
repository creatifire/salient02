"""
Unit Tests for Simple Chat Agent Integration - TASK 0017-003-005

Tests the simple_chat function's history loading logic and integration
with agent session service in isolation from external dependencies.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from app.agents.simple_chat import simple_chat
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart


class TestSimpleChatAgentIntegration:
    """Unit tests for simple_chat agent integration - CHUNK 0017-003-005-02"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies for isolated testing."""
        with patch('app.agents.simple_chat.load_config') as mock_config, \
             patch('app.agents.simple_chat.get_agent_config') as mock_agent_config, \
             patch('app.agents.simple_chat.SessionDependencies') as mock_session_deps, \
             patch('app.agents.simple_chat.get_chat_agent') as mock_get_agent, \
             patch('app.agents.simple_chat.OpenRouterProvider') as mock_provider:
            
            # Configure mocks
            mock_config.return_value = {
                "chat": {"history_limit": 20},
                "llm": {
                    "model": "test-model",
                    "api_key": "test-key"
                }
            }
            
            mock_agent_config.return_value = Mock(
                model_settings={"max_tokens": 1000, "temperature": 0.7}
            )
            
            mock_session_deps_instance = Mock()
            mock_session_deps.create = AsyncMock(return_value=mock_session_deps_instance)
            
            # Mock successful agent response
            mock_agent = Mock()
            mock_result = Mock()
            mock_result.output = "Test agent response"
            mock_usage = Mock()
            mock_usage.input_tokens = 10
            mock_usage.output_tokens = 20
            mock_usage.total_tokens = 30
            mock_usage.requests = 1
            mock_usage.cost = 0.001
            mock_result.usage.return_value = mock_usage
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_get_agent.return_value = mock_agent
            
            # Mock OpenRouter provider
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Mocked response"))]
            mock_response.usage = Mock(
                prompt_tokens=15,
                completion_tokens=25,
                total_tokens=40,
                cost=0.002
            )
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_provider_instance = Mock(client=mock_client)
            mock_provider.return_value = mock_provider_instance
            
            yield {
                'config': mock_config,
                'agent_config': mock_agent_config,
                'session_deps': mock_session_deps,
                'agent': mock_agent,
                'provider': mock_provider
            }
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history in Pydantic AI format."""
        return [
            ModelRequest(parts=[UserPromptPart(
                content="Previous user message",
                timestamp=datetime.now(timezone.utc)
            )]),
            ModelResponse(
                parts=[TextPart(content="Previous assistant response")],
                usage=None,
                model_name="agent-session",
                timestamp=datetime.now(timezone.utc)
            )
        ]
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.load_agent_conversation')
    @patch('app.services.agent_session.get_session_stats')
    async def test_simple_chat_auto_load_history(self, mock_get_stats, mock_load_conversation, mock_dependencies, sample_conversation_history):
        """Test that simple_chat automatically loads history when message_history=None."""
        
        # Mock the conversation loading
        mock_load_conversation.return_value = sample_conversation_history
        mock_get_stats.return_value = {
            "total_messages": 2,
            "session_id": "test-session",
            "cross_endpoint_continuity": True
        }
        
        session_id = str(uuid.uuid4())
        
        # Call simple_chat without providing message_history
        result = await simple_chat(
            message="New test message",
            session_id=session_id,
            message_history=None  # Should trigger auto-loading
        )
        
        # Verify conversation loading was called
        mock_load_conversation.assert_called_once_with(session_id)
        
        # Verify response structure
        assert 'response' in result
        assert 'usage' in result
        assert 'session_continuity' in result
        assert result['session_continuity']['cross_endpoint_continuity'] == True
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.load_agent_conversation')
    @patch('app.services.agent_session.get_session_stats') 
    async def test_simple_chat_with_provided_history(self, mock_get_stats, mock_load_conversation, mock_dependencies, sample_conversation_history):
        """Test that simple_chat doesn't auto-load when message_history is provided."""
        
        mock_get_stats.return_value = {
            "total_messages": 2,
            "session_id": "test-session", 
            "cross_endpoint_continuity": True
        }
        
        session_id = str(uuid.uuid4())
        
        # Call simple_chat with explicit message_history
        result = await simple_chat(
            message="Test message",
            session_id=session_id,
            message_history=sample_conversation_history  # Explicit history provided
        )
        
        # Verify conversation loading was NOT called
        mock_load_conversation.assert_not_called()
        
        # Verify response structure
        assert 'response' in result
        assert 'session_continuity' in result
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.load_agent_conversation')
    @patch('app.services.agent_session.get_session_stats')
    async def test_simple_chat_empty_history_handling(self, mock_get_stats, mock_load_conversation, mock_dependencies):
        """Test handling when no conversation history is found."""
        
        # Mock empty conversation history
        mock_load_conversation.return_value = []
        mock_get_stats.return_value = {
            "total_messages": 0,
            "session_id": "test-session",
            "cross_endpoint_continuity": False
        }
        
        session_id = str(uuid.uuid4())
        
        result = await simple_chat(
            message="First message in session",
            session_id=session_id
        )
        
        # Should handle empty history gracefully
        mock_load_conversation.assert_called_once_with(session_id)
        assert 'response' in result
        assert result['session_continuity']['cross_endpoint_continuity'] == False
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.load_agent_conversation')
    @patch('app.services.agent_session.get_session_stats')
    @patch('loguru.logger')
    async def test_simple_chat_session_bridging_logging(self, mock_logger, mock_get_stats, mock_load_conversation, mock_dependencies, sample_conversation_history):
        """Test that session bridging events are logged for analytics."""
        
        mock_load_conversation.return_value = sample_conversation_history
        mock_get_stats.return_value = {
            "total_messages": 2,
            "session_id": "test-session",
            "cross_endpoint_continuity": True
        }
        
        session_id = str(uuid.uuid4())
        
        await simple_chat(
            message="Test message",
            session_id=session_id
        )
        
        # Verify session bridging was logged
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args
        log_data = log_call_args[0][0]
        
        assert log_data['event'] == 'agent_session_bridging'
        assert log_data['session_id'] == session_id
        assert log_data['loaded_messages'] == 2
        assert log_data['cross_endpoint_continuity'] == True
        assert log_data['agent_type'] == 'simple_chat'
        assert log_data['bridging_method'] == 'agent_session_service'
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.load_agent_conversation')
    @patch('app.services.agent_session.get_session_stats')
    async def test_simple_chat_cost_tracking_preserved(self, mock_get_stats, mock_load_conversation, mock_dependencies):
        """Test that cost tracking functionality is preserved with history loading."""
        
        mock_load_conversation.return_value = []
        mock_get_stats.return_value = {
            "total_messages": 0,
            "session_id": "test-session",
            "cross_endpoint_continuity": False
        }
        
        session_id = str(uuid.uuid4())
        
        result = await simple_chat(
            message="Test cost tracking",
            session_id=session_id
        )
        
        # Verify cost tracking data is included
        assert 'cost_tracking' in result
        assert 'llm_request_id' in result
        
        # Verify cost tracking structure (from mocked response)
        cost_tracking = result.get('cost_tracking', {})
        assert 'real_cost' in cost_tracking
        assert 'method' in cost_tracking
    
    @pytest.mark.asyncio
    @patch('app.services.agent_session.load_agent_conversation')
    async def test_simple_chat_conversation_loading_error_handling(self, mock_load_conversation, mock_dependencies):
        """Test error handling when conversation loading fails."""
        
        # Mock conversation loading failure
        mock_load_conversation.side_effect = Exception("Database connection error")
        
        session_id = str(uuid.uuid4())
        
        # Should handle loading errors gracefully
        with pytest.raises(Exception):
            await simple_chat(
                message="Test error handling",
                session_id=session_id
            )
        
        # Verify conversation loading was attempted
        mock_load_conversation.assert_called_once_with(session_id)


if __name__ == "__main__":
    # Run tests: pytest backend/tests/unit/test_simple_chat_agent.py -v
    pytest.main([__file__, "-v"])
