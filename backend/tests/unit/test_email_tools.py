"""
Unit tests for email_tools module (Demo implementation).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from app.agents.tools.email_tools import send_conversation_summary
from app.agents.base.dependencies import SessionDependencies
from pydantic_ai import RunContext


@pytest.fixture
def mock_session_deps():
    """Create mock SessionDependencies for testing."""
    deps = MagicMock(spec=SessionDependencies)
    deps.session_id = "test-session-123"
    return deps


@pytest.fixture
def mock_run_context(mock_session_deps):
    """Create mock RunContext with SessionDependencies."""
    ctx = MagicMock(spec=RunContext)
    ctx.deps = mock_session_deps
    return ctx


@pytest.mark.asyncio
async def test_email_tool_logs_request(mock_run_context):
    """Test that email tool logs request to Logfire."""
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        result = await send_conversation_summary(
            ctx=mock_run_context,
            email_address="test@example.com",
            summary_notes="Test summary notes"
        )
        
        # Verify Logfire logging was called
        mock_logfire.info.assert_called_once()
        call_args = mock_logfire.info.call_args
        
        # Check event name
        assert call_args[0][0] == 'email.summary.demo'
        
        # Check logged parameters
        assert call_args[1]['session_id'] == "test-session-123"
        assert call_args[1]['email'] == "test@example.com"
        assert call_args[1]['notes'] == "Test summary notes"
        assert call_args[1]['demo_mode'] is True
        assert 'timestamp' in call_args[1]
        assert 'message' in call_args[1]


@pytest.mark.asyncio
async def test_email_tool_returns_confirmation(mock_run_context):
    """Test that email tool returns professional confirmation message."""
    with patch('app.agents.tools.email_tools.logfire'):
        result = await send_conversation_summary(
            ctx=mock_run_context,
            email_address="user@example.com"
        )
        
        # Check confirmation message format
        assert "✓" in result
        assert "queued" in result.lower()
        assert "user@example.com" in result
        assert "inbox" in result.lower()
        assert "summary" in result.lower()


@pytest.mark.asyncio
async def test_email_validation(mock_run_context):
    """Test email format validation."""
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        # Test invalid email (no @)
        result = await send_conversation_summary(
            ctx=mock_run_context,
            email_address="invalid-email"
        )
        
        # Should return error message, not confirmation
        assert "valid email address" in result
        assert "Could you please provide" in result
        
        # Should NOT log to Logfire
        mock_logfire.info.assert_not_called()


@pytest.mark.asyncio
async def test_email_tool_with_notes(mock_run_context):
    """Test email tool with summary_notes parameter."""
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        result = await send_conversation_summary(
            ctx=mock_run_context,
            email_address="patient@hospital.com",
            summary_notes="cardiology discussion and Dr. Smith contact info"
        )
        
        # Verify notes are logged
        call_args = mock_logfire.info.call_args
        assert call_args[1]['notes'] == "cardiology discussion and Dr. Smith contact info"
        
        # Verify confirmation returned
        assert "✓" in result
        assert "patient@hospital.com" in result


@pytest.mark.asyncio
async def test_email_tool_without_notes(mock_run_context):
    """Test email tool with default empty notes."""
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        result = await send_conversation_summary(
            ctx=mock_run_context,
            email_address="user@domain.com"
            # summary_notes not provided (uses default "")
        )
        
        # Verify empty notes are logged
        call_args = mock_logfire.info.call_args
        assert call_args[1]['notes'] == ""
        
        # Verify confirmation returned
        assert "✓" in result


@pytest.mark.asyncio
async def test_invalid_email_format(mock_run_context):
    """Test validation error message for various invalid formats."""
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        # Test empty email
        result1 = await send_conversation_summary(
            ctx=mock_run_context,
            email_address=""
        )
        assert "valid email address" in result1
        
        # Test None-like email (space only)
        result2 = await send_conversation_summary(
            ctx=mock_run_context,
            email_address="   "
        )
        assert "valid email address" in result2
        
        # Verify no logging for invalid emails
        mock_logfire.info.assert_not_called()


@pytest.mark.asyncio
async def test_email_tool_session_id_tracking(mock_run_context):
    """Test that session ID is properly tracked in logs."""
    mock_run_context.deps.session_id = "unique-session-456"
    
    with patch('app.agents.tools.email_tools.logfire') as mock_logfire:
        await send_conversation_summary(
            ctx=mock_run_context,
            email_address="test@example.com"
        )
        
        # Verify correct session ID logged
        call_args = mock_logfire.info.call_args
        assert call_args[1]['session_id'] == "unique-session-456"

