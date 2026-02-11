"""
Unit tests for email tool registration in simple_chat.py.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from app.agents.simple_chat import create_simple_chat_agent


@pytest.mark.asyncio
async def test_email_tool_registered_when_enabled():
    """Test that email tool is registered when enabled in config."""
    instance_config = {
        'instance_name': 'test_agent',
        'tools': {
            'email_summary': {'enabled': True},
            'vector_search': {'enabled': False},
            'directory': {'enabled': False}
        }
    }
    
    with patch('app.agents.simple_chat.logfire') as mock_logfire, \
         patch('app.agents.simple_chat.get_agent_config') as mock_get_config, \
         patch('app.agents.simple_chat.OpenRouterModel') as mock_model, \
         patch('app.agents.simple_chat.create_openrouter_provider_with_cost_tracking') as mock_provider, \
         patch('app.agents.simple_chat.load_config') as mock_load_config, \
         patch('app.agents.simple_chat.PromptBreakdownService'):
        
        # Setup mocks
        mock_get_config.return_value = MagicMock(
            system_prompt="Test prompt",
            config=instance_config
        )
        mock_load_config.return_value = {
            'llm': {'provider': 'openrouter', 'model': 'test-model'}
        }
        mock_provider.return_value = (MagicMock(), "test-model", MagicMock())
        
        # Create agent
        agent, _, _, _ = await create_simple_chat_agent(instance_config=instance_config)
        
        # Verify email tool was registered
        assert any(
            call_args[1].get('tool') == 'send_conversation_summary'
            for call_args in mock_logfire.info.call_args_list
        ), "Email tool registration not logged"
        
        # Verify demo_mode flag
        email_log_calls = [
            call for call in mock_logfire.info.call_args_list
            if call[1].get('tool') == 'send_conversation_summary'
        ]
        assert len(email_log_calls) == 1
        assert email_log_calls[0][1].get('demo_mode') is True


@pytest.mark.asyncio
async def test_email_tool_not_registered_when_disabled():
    """Test that email tool is NOT registered when disabled."""
    instance_config = {
        'instance_name': 'test_agent',
        'tools': {
            'email_summary': {'enabled': False},
            'vector_search': {'enabled': False},
            'directory': {'enabled': False}
        }
    }
    
    with patch('app.agents.simple_chat.logfire') as mock_logfire, \
         patch('app.agents.simple_chat.get_agent_config') as mock_get_config, \
         patch('app.agents.simple_chat.OpenRouterModel') as mock_model, \
         patch('app.agents.simple_chat.create_openrouter_provider_with_cost_tracking') as mock_provider, \
         patch('app.agents.simple_chat.load_config') as mock_load_config, \
         patch('app.agents.simple_chat.PromptBreakdownService'):
        
        # Setup mocks
        mock_get_config.return_value = MagicMock(
            system_prompt="Test prompt",
            config=instance_config
        )
        mock_load_config.return_value = {
            'llm': {'provider': 'openrouter', 'model': 'test-model'}
        }
        mock_provider.return_value = (MagicMock(), "test-model", MagicMock())
        
        # Create agent
        agent, _, _, _ = await create_simple_chat_agent(instance_config=instance_config)
        
        # Verify email tool was NOT registered
        email_log_calls = [
            call for call in mock_logfire.info.call_args_list
            if call[1].get('tool') == 'send_conversation_summary'
        ]
        assert len(email_log_calls) == 0, "Email tool should not be registered when disabled"


@pytest.mark.asyncio
async def test_email_tool_not_registered_by_default():
    """Test that email tool is disabled by default (not in config)."""
    instance_config = {
        'instance_name': 'test_agent',
        'tools': {
            # email_summary not present - should default to disabled
            'vector_search': {'enabled': False},
            'directory': {'enabled': False}
        }
    }
    
    with patch('app.agents.simple_chat.logfire') as mock_logfire, \
         patch('app.agents.simple_chat.get_agent_config') as mock_get_config, \
         patch('app.agents.simple_chat.OpenRouterModel') as mock_model, \
         patch('app.agents.simple_chat.create_openrouter_provider_with_cost_tracking') as mock_provider, \
         patch('app.agents.simple_chat.load_config') as mock_load_config, \
         patch('app.agents.simple_chat.PromptBreakdownService'):
        
        # Setup mocks
        mock_get_config.return_value = MagicMock(
            system_prompt="Test prompt",
            config=instance_config
        )
        mock_load_config.return_value = {
            'llm': {'provider': 'openrouter', 'model': 'test-model'}
        }
        mock_provider.return_value = (MagicMock(), "test-model", MagicMock())
        
        # Create agent
        agent, _, _, _ = await create_simple_chat_agent(instance_config=instance_config)
        
        # Verify email tool was NOT registered (default behavior)
        email_log_calls = [
            call for call in mock_logfire.info.call_args_list
            if call[1].get('tool') == 'send_conversation_summary'
        ]
        assert len(email_log_calls) == 0, "Email tool should be disabled by default"


@pytest.mark.asyncio
async def test_multiple_agents_different_email_configs():
    """Test that different agents can have different email tool configurations."""
    # Agent 1: email enabled
    config1 = {
        'instance_name': 'agent_with_email',
        'tools': {
            'email_summary': {'enabled': True}
        }
    }
    
    # Agent 2: email disabled
    config2 = {
        'instance_name': 'agent_without_email',
        'tools': {
            'email_summary': {'enabled': False}
        }
    }
    
    with patch('app.agents.simple_chat.logfire') as mock_logfire, \
         patch('app.agents.simple_chat.get_agent_config') as mock_get_config, \
         patch('app.agents.simple_chat.OpenRouterModel') as mock_model, \
         patch('app.agents.simple_chat.create_openrouter_provider_with_cost_tracking') as mock_provider, \
         patch('app.agents.simple_chat.load_config') as mock_load_config, \
         patch('app.agents.simple_chat.PromptBreakdownService'):
        
        # Setup mocks
        mock_get_config.return_value = MagicMock(
            system_prompt="Test prompt",
            config=config1
        )
        mock_load_config.return_value = {
            'llm': {'provider': 'openrouter', 'model': 'test-model'}
        }
        mock_provider.return_value = (MagicMock(), "test-model", MagicMock())
        
        # Create agent 1 (with email)
        mock_logfire.reset_mock()
        agent1, _, _, _ = await create_simple_chat_agent(instance_config=config1)
        
        email_logs_1 = [
            call for call in mock_logfire.info.call_args_list
            if call[1].get('tool') == 'send_conversation_summary'
        ]
        assert len(email_logs_1) == 1, "Agent 1 should have email tool registered"
        
        # Create agent 2 (without email)
        mock_logfire.reset_mock()
        mock_get_config.return_value = MagicMock(
            system_prompt="Test prompt",
            config=config2
        )
        agent2, _, _, _ = await create_simple_chat_agent(instance_config=config2)
        
        email_logs_2 = [
            call for call in mock_logfire.info.call_args_list
            if call[1].get('tool') == 'send_conversation_summary'
        ]
        assert len(email_logs_2) == 0, "Agent 2 should NOT have email tool registered"

