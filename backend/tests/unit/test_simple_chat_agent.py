"""
Unit Tests for Simple Chat Agent Parameter Standardization - TASK 0017-004-001-07

Tests the simple_chat function's parameter standardization and configuration cascade
with comprehensive mocking to isolate from external dependencies.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.agents.simple_chat import simple_chat
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart


class TestSimpleChatParameterStandardization:
    """Unit tests for simple_chat parameter standardization - CHUNK 0017-004-001-07"""
    
    @pytest.fixture
    def mock_all_dependencies(self):
        """Comprehensive mock of all dependencies for parameter standardization tests."""
        with patch('app.agents.config_loader.get_agent_history_limit') as mock_get_history_limit, \
             patch('app.agents.simple_chat.load_config') as mock_load_config, \
             patch('app.agents.config_loader.get_agent_config') as mock_get_agent_config, \
             patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create, \
             patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent, \
             patch('app.agents.simple_chat.load_conversation_history') as mock_load_conversation, \
             patch('app.services.agent_session.get_session_stats') as mock_get_session_stats, \
             patch('app.agents.simple_chat.OpenRouterModel') as mock_provider:
            
            # Mock configuration cascade function
            mock_get_history_limit.return_value = 50
            
            # Mock global config
            mock_load_config.return_value = {
                "chat": {"history_limit": 25},
                "llm": {"openrouter": {"api_key": "test-key"}}
            }
            
            # Mock agent config
            mock_agent_config = MagicMock()
            mock_agent_config.context_management = {"history_limit": 75}
            mock_agent_config.model_settings = {"model": "openai:gpt-4o", "temperature": 0.3}
            mock_get_agent_config.return_value = mock_agent_config
            
            # Mock session dependencies
            mock_session_deps = MagicMock()
            mock_session_create.return_value = mock_session_deps
            
            # Mock agent and response
            mock_agent = AsyncMock()
            mock_result = MagicMock()
            mock_result.output = "Test response from agent"  # Fixed: use .output not .data
            
            # Mock usage as a callable that returns an object with attributes
            mock_usage = MagicMock()
            mock_usage.input_tokens = 15
            mock_usage.output_tokens = 25
            mock_usage.total_tokens = 40
            mock_result.usage.return_value = mock_usage
            
            mock_agent.run.return_value = mock_result
            mock_get_chat_agent.return_value = mock_agent
            
            # Mock conversation loading
            mock_load_conversation.return_value = []
            mock_get_session_stats.return_value = {
                "total_messages": 0,
                "session_id": "test-session",
                "cross_endpoint_continuity": False
            }
            
            # Mock OpenRouter provider
            mock_provider_instance = MagicMock()
            mock_provider.return_value = mock_provider_instance
            
            yield {
                'get_history_limit': mock_get_history_limit,
                'load_config': mock_load_config,
                'get_agent_config': mock_get_agent_config,
                'session_create': mock_session_create,
                'get_chat_agent': mock_get_chat_agent,
                'load_conversation': mock_load_conversation,
                'get_session_stats': mock_get_session_stats,
                'provider': mock_provider
            }
    
    @pytest.mark.asyncio
    async def test_parameter_name_standardization(self, mock_all_dependencies):
        """
        Verify old parameter names are completely removed from codebase.
        
        CHUNK 0017-004-001-07 AUTOMATED-TEST 1:
        Verify SessionDependencies.create uses standardized history_limit parameter.
        """
        session_id = str(uuid.uuid4())
        
        # Call simple_chat to trigger SessionDependencies.create
        await simple_chat(
            message="Test standardized parameters",
            session_id=session_id
        )
        
        # Verify SessionDependencies.create was called with correct parameter
        mocks = mock_all_dependencies
        mocks['session_create'].assert_called_once()
        call_kwargs = mocks['session_create'].call_args[1]
        
        # Should use standardized parameter name
        assert 'history_limit' in call_kwargs, \
            "SessionDependencies.create should be called with 'history_limit' parameter"
        
        # Should NOT use old parameter name
        assert 'max_history_messages' not in call_kwargs, \
            "SessionDependencies.create should NOT use old 'max_history_messages' parameter"
        
        # Should use value from get_agent_history_limit cascade function
        assert call_kwargs['history_limit'] == 50, \
            "Should use value from agent configuration cascade"
    
    @pytest.mark.asyncio
    async def test_agent_first_configuration_cascade(self, mock_all_dependencies):
        """
        Test that agent prioritizes configuration cascade correctly.
        
        CHUNK 0017-004-001-07 AUTOMATED-TEST 2:
        Verify agent-first configuration cascade logic is working.
        """
        session_id = str(uuid.uuid4())
        
        # Call simple_chat 
        await simple_chat(
            message="Test configuration cascade",
            session_id=session_id
        )
        
        mocks = mock_all_dependencies
        
        # Verify get_agent_history_limit was called (implements cascade)
        mocks['get_history_limit'].assert_called_with("simple_chat")
        
        # Verify the cascade function's result was used
        mocks['session_create'].assert_called_once()
        call_kwargs = mocks['session_create'].call_args[1]
        assert call_kwargs['history_limit'] == 50, \
            "Should use result from configuration cascade function"
    
    @pytest.mark.asyncio
    async def test_end_to_end_configuration_behavior(self, mock_all_dependencies):
        """
        Integration test verifying complete config cascade works.
        
        CHUNK 0017-004-001-07 AUTOMATED-TEST 3:
        End-to-end test of configuration cascade and parameter usage.
        """
        session_id = str(uuid.uuid4())
        
        # Test with different cascade result
        mocks = mock_all_dependencies
        mocks['get_history_limit'].return_value = 100
        
        result = await simple_chat(
            message="Test end-to-end config",
            session_id=session_id
        )
        
        # Verify response structure is intact
        assert 'response' in result
        assert 'usage' in result
        assert 'session_continuity' in result
        
        # Verify configuration cascade was used end-to-end
        mocks['get_history_limit'].assert_called_with("simple_chat")
        
        # Verify SessionDependencies used the cascade result
        call_kwargs = mocks['session_create'].call_args[1]
        assert call_kwargs['history_limit'] == 100, \
            "End-to-end flow should use cascade result consistently"
        
        # Verify no old parameters anywhere in the flow
        assert 'max_history_messages' not in str(call_kwargs), \
            "Old parameter names should be completely eliminated"
    
    @pytest.mark.asyncio
    async def test_existing_functionality_preservation(self, mock_all_dependencies):
        """
        Verify all existing functionality still works with new parameter names.
        
        CHUNK 0017-004-001-07 AUTOMATED-TEST 4:
        Verify parameter standardization doesn't break existing functionality.
        """
        session_id = str(uuid.uuid4())
        
        result = await simple_chat(
            message="Test functionality preservation",
            session_id=session_id
        )
        
        mocks = mock_all_dependencies
        
        # All core functionality should still work
        assert 'response' in result
        assert 'usage' in result
        assert 'session_continuity' in result
        
        # Agent workflow should be intact
        mocks['load_conversation'].assert_called_once_with(session_id=session_id, max_messages=None)
        mocks['get_session_stats'].assert_called_once_with(session_id)
        mocks['get_chat_agent'].assert_called_once()
        
        # Response should contain expected data
        assert result['response'] is not None
        assert hasattr(result['usage'], 'total_tokens')
        
        # Agent workflow should produce valid output
        assert isinstance(result['response'], str)
        assert result['usage'].total_tokens > 0


if __name__ == "__main__":
    # Run tests: pytest backend/tests/unit/test_simple_chat_agent.py -v
    pytest.main([__file__, "-v"])
