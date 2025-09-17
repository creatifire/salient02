"""
Unit tests for simple_chat.py agent configuration standardization.

Tests for CHUNK 0017-004-001-04: Update simple_chat.py agent implementation
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call


@pytest.mark.unit
@pytest.mark.asyncio 
async def test_agent_reads_from_agent_config_first():
    """
    Test that agent prioritizes agent-specific config over global config.
    
    CHUNK 0017-004-001-04 AUTOMATED-TEST 1:
    Verify agent uses agent-specific history_limit when available.
    """
    # This test will verify the configuration cascade works properly
    # by mocking the get_agent_config to return agent-specific config
    # and ensuring the SessionDependencies.create is called with the right value
    
    from app.agents.simple_chat import simple_chat
    
    # Mock agent config with specific history_limit
    mock_agent_config = MagicMock()
    mock_agent_config.context_management = {"history_limit": 75}
    mock_agent_config.model_settings = MagicMock()
    
    # Mock global config with different history_limit
    mock_global_config = {
        "chat": {"history_limit": 25},  # Different value to test precedence
        "llm": {}  # No OpenRouter to avoid complexity
    }
    
    with patch('app.agents.config_loader.get_agent_config', return_value=mock_agent_config) as mock_get_agent:
        with patch('app.agents.simple_chat.load_config', return_value=mock_global_config):
            with patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create:
                with patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent:
                    with patch('app.agents.simple_chat.load_conversation_history', return_value=[]):
                        # Mock the agent and its run method
                        mock_agent = AsyncMock()
                        mock_result = MagicMock()
                        mock_result.data = "Test response"
                        mock_result.usage.return_value = {"total_tokens": 100}
                        mock_agent.run.return_value = mock_result
                        mock_get_chat_agent.return_value = mock_agent
                        
                        # Mock session dependencies
                        mock_session_deps = MagicMock()
                        mock_session_create.return_value = mock_session_deps
                        
                        # Mock get_session_stats to avoid UUID conversion issues
                        with patch('app.services.agent_session.get_session_stats', return_value={}):
                            # Test the agent function with valid UUID
                            result = await simple_chat("test message", "f011fff1-11f9-4b76-8ee9-f23a15d76b74")
                        
                        # Verify agent config was called (optimized: called once for both history_limit and model settings)
                        assert mock_get_agent.call_count >= 1, f"get_agent_config should be called at least once, was called {mock_get_agent.call_count} times"
                        
                        # Verify SessionDependencies was created with agent-specific history_limit
                        mock_session_create.assert_called_once()
                        call_args = mock_session_create.call_args
                        
                        # Now it should use agent config value (75) not global config value (25)
                        assert call_args[1]['history_limit'] == 75, \
                            f"SessionDependencies should use agent-specific history_limit (75), got {call_args[1]['history_limit']}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_agent_uses_history_limit_parameter():
    """
    Test that agent uses standardized history_limit parameter throughout.
    
    CHUNK 0017-004-001-04 AUTOMATED-TEST 2:
    Verify agent uses history_limit parameter (not old max_history_messages).
    """
    from app.agents.simple_chat import simple_chat
    
    # Mock agent config with history_limit
    mock_agent_config = MagicMock()
    mock_agent_config.context_management = {"history_limit": 40}
    mock_agent_config.model_settings = MagicMock()
    
    mock_global_config = {
        "chat": {"history_limit": 20},
        "llm": {}  # No OpenRouter
    }
    
    with patch('app.agents.config_loader.get_agent_config', return_value=mock_agent_config):
        with patch('app.agents.simple_chat.load_config', return_value=mock_global_config):
            with patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create:
                with patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent:
                    with patch('app.agents.simple_chat.load_conversation_history', return_value=[]):
                        # Mock agent
                        mock_agent = AsyncMock()
                        mock_result = MagicMock()
                        mock_result.data = "Test response" 
                        mock_result.usage.return_value = {"total_tokens": 50}
                        mock_agent.run.return_value = mock_result
                        mock_get_chat_agent.return_value = mock_agent
                        
                        # Mock session dependencies  
                        mock_session_deps = MagicMock()
                        mock_session_create.return_value = mock_session_deps
                        
                        # Mock get_session_stats to avoid UUID conversion issues
                        with patch('app.services.agent_session.get_session_stats', return_value={}):
                            # Call the agent with valid UUID
                            result = await simple_chat("test", "f011fff1-11f9-4b76-8ee9-f23a15d76b75")
                        
                        # Verify SessionDependencies.create was called with history_limit parameter
                        mock_session_create.assert_called_once()
                        call_kwargs = mock_session_create.call_args[1]
                        
                        assert 'history_limit' in call_kwargs, \
                            "SessionDependencies.create should be called with 'history_limit' parameter"
                        
                        assert 'max_history_messages' not in call_kwargs, \
                            "SessionDependencies.create should NOT use old 'max_history_messages' parameter"
                        
                        # Should use agent config value
                        assert call_kwargs['history_limit'] == 40, \
                            f"Should use agent-specific history_limit value from agent config (40), got {call_kwargs['history_limit']}"