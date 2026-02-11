"""
End-to-end integration tests for email summary tool.

These tests verify the complete email tool flow:
1. Tool is registered in agent
2. Agent responds to email requests
3. Tool is called and logs events
4. Proper error handling for invalid emails
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.agents.simple_chat import create_simple_chat_agent, simple_chat
from app.agents.base.dependencies import SessionDependencies


@pytest.mark.asyncio
async def test_email_tool_e2e_basic_flow():
    """Test end-to-end flow: user requests email summary."""
    
    # Create Wind River agent config with email enabled
    instance_config = {
        'account': 'windriver',
        'instance_name': 'windriver_info_chat1',
        'tools': {
            'email_summary': {'enabled': True},
            'vector_search': {'enabled': False},
            'directory': {'enabled': False}
        }
    }
    
    session_id = str(uuid4())
    
    with patch('app.agents.simple_chat.logfire') as mock_logfire, \
         patch('app.agents.simple_chat.get_agent_config') as mock_get_config, \
         patch('app.agents.simple_chat.load_config') as mock_load_config, \
         patch('app.agents.simple_chat.PromptBreakdownService'), \
         patch('app.agents.simple_chat.create_openrouter_provider_with_cost_tracking') as mock_provider, \
         patch('app.agents.tools.email_tools.logfire') as mock_email_logfire:
        
        # Setup mocks
        mock_get_config.return_value = MagicMock(
            system_prompt="You are a helpful assistant. Use send_conversation_summary() when user requests email.",
            config=instance_config
        )
        mock_load_config.return_value = {
            'llm': {'provider': 'openrouter', 'model': 'test-model'}
        }
        
        # Mock the provider
        mock_client = MagicMock()
        mock_provider.return_value = (mock_client, "test-model", MagicMock())
        
        # Create agent
        agent, _, _, tools = await create_simple_chat_agent(instance_config=instance_config)
        
        # Verify email tool is in tools list
        tool_names = [t.__name__ for t in tools]
        assert 'send_conversation_summary' in tool_names, \
            f"Email tool not registered. Available tools: {tool_names}"
        
        # Verify tool registration was logged
        email_registration_logs = [
            call for call in mock_logfire.info.call_args_list
            if call[1].get('tool') == 'send_conversation_summary'
        ]
        assert len(email_registration_logs) > 0, "Tool registration not logged"


@pytest.mark.asyncio
async def test_email_tool_e2e_with_valid_email():
    """Test that tool correctly processes valid email address."""
    
    session_id = str(uuid4())
    
    # Create session dependencies
    session_deps = MagicMock(spec=SessionDependencies)
    session_deps.session_id = session_id
    
    # Create run context
    from pydantic_ai import RunContext
    ctx = MagicMock(spec=RunContext)
    ctx.deps = session_deps
    
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        from app.agents.tools.email_tools import send_conversation_summary
        
        # Call tool with valid email
        result = await send_conversation_summary(
            ctx=ctx,
            email_address="test@example.com",
            summary_notes="Test conversation summary"
        )
        
        # Verify confirmation message returned
        assert "✓" in result
        assert "test@example.com" in result
        assert "queued" in result.lower()
        
        # Verify logging
        mock_logfire.info.assert_called_once()
        log_call = mock_logfire.info.call_args
        
        assert log_call[0][0] == 'email.summary.demo'
        assert log_call[1]['session_id'] == session_id
        assert log_call[1]['email'] == "test@example.com"
        assert log_call[1]['notes'] == "Test conversation summary"
        assert log_call[1]['demo_mode'] is True


@pytest.mark.asyncio
async def test_email_tool_e2e_with_invalid_email():
    """Test that tool correctly handles invalid email address."""
    
    session_id = str(uuid4())
    
    # Create session dependencies
    session_deps = MagicMock(spec=SessionDependencies)
    session_deps.session_id = session_id
    
    # Create run context
    from pydantic_ai import RunContext
    ctx = MagicMock(spec=RunContext)
    ctx.deps = session_deps
    
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        from app.agents.tools.email_tools import send_conversation_summary
        
        # Call tool with invalid email (no @)
        result = await send_conversation_summary(
            ctx=ctx,
            email_address="invalid-email",
            summary_notes=""
        )
        
        # Verify error message returned
        assert "valid email address" in result
        assert "Could you please provide" in result
        
        # Verify NO logging occurred (invalid email)
        mock_logfire.info.assert_not_called()


@pytest.mark.asyncio
async def test_email_tool_disabled_by_default():
    """Test that email tool is not registered when not explicitly enabled."""
    
    # Create config WITHOUT email_summary enabled
    instance_config = {
        'account': 'default_account',
        'instance_name': 'simple_chat1',
        'tools': {
            'vector_search': {'enabled': False},
            'directory': {'enabled': False}
            # email_summary not present
        }
    }
    
    with patch('app.agents.simple_chat.logfire') as mock_logfire, \
         patch('app.agents.simple_chat.get_agent_config') as mock_get_config, \
         patch('app.agents.simple_chat.load_config') as mock_load_config, \
         patch('app.agents.simple_chat.PromptBreakdownService'), \
         patch('app.agents.simple_chat.create_openrouter_provider_with_cost_tracking') as mock_provider:
        
        # Setup mocks
        mock_get_config.return_value = MagicMock(
            system_prompt="Test prompt",
            config=instance_config
        )
        mock_load_config.return_value = {
            'llm': {'provider': 'openrouter', 'model': 'test-model'}
        }
        mock_client = MagicMock()
        mock_provider.return_value = (mock_client, "test-model", MagicMock())
        
        # Create agent
        agent, _, _, tools = await create_simple_chat_agent(instance_config=instance_config)
        
        # Verify email tool is NOT in tools list
        tool_names = [t.__name__ for t in tools]
        assert 'send_conversation_summary' not in tool_names, \
            "Email tool should not be registered when not enabled"


@pytest.mark.asyncio
async def test_email_tool_logs_demo_mode():
    """Test that all email tool calls log demo_mode=True."""
    
    session_id = str(uuid4())
    
    # Create session dependencies
    session_deps = MagicMock(spec=SessionDependencies)
    session_deps.session_id = session_id
    
    # Create run context
    from pydantic_ai import RunContext
    ctx = MagicMock(spec=RunContext)
    ctx.deps = session_deps
    
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        from app.agents.tools.email_tools import send_conversation_summary
        
        # Call tool
        await send_conversation_summary(
            ctx=ctx,
            email_address="demo@example.com",
            summary_notes="Demo test"
        )
        
        # Verify demo_mode flag is True
        log_call = mock_logfire.info.call_args
        assert log_call[1]['demo_mode'] is True, \
            "Email tool should always log demo_mode=True for demo implementation"


@pytest.mark.asyncio
async def test_wind_river_agent_has_email_tool():
    """Test that Wind River agent specifically has email tool enabled."""
    
    # This test verifies the actual Wind River config
    # Load the real config from file
    from pathlib import Path
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / "config" / "agent_configs" / "windriver" / "windriver_info_chat1" / "config.yaml"
    
    if not config_path.exists():
        pytest.skip(f"Wind River config not found at {config_path}")
    
    with open(config_path) as f:
        wind_river_config = yaml.safe_load(f)
    
    # Verify email_summary is enabled
    tools_config = wind_river_config.get('tools', {})
    email_config = tools_config.get('email_summary', {})
    
    assert email_config.get('enabled', False) is True, \
        "Wind River agent should have email_summary tool enabled in config"

