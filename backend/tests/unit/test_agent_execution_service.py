"""
Unit tests for AgentExecutionService (CHUNK-0026-010-003).

Tests the new setup_execution_context() and execute_agent() methods
that consolidate agent setup and execution logic from simple_chat.py.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.services.agent_execution_service import AgentExecutionService
from pydantic_ai.messages import ModelRequest, ModelResponse, SystemPromptPart, UserPromptPart


class TestSetupExecutionContext:
    """Test suite for setup_execution_context() method."""
    
    @pytest.mark.asyncio
    async def test_setup_execution_context_basic(self):
        """Test basic context setup with minimal parameters."""
        service = AgentExecutionService()
        
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Mock all the dependencies
        mock_deps = AsyncMock()
        mock_agent = Mock()
        mock_history = []
        
        with patch('app.agents.config_loader.get_agent_history_limit', AsyncMock(return_value=20)):
            with patch('app.agents.base.dependencies.SessionDependencies.create', AsyncMock(return_value=mock_deps)):
                with patch('app.agents.config_loader.get_agent_model_settings', AsyncMock(return_value={})):
                    with patch('app.agents.simple_chat.load_conversation_history', AsyncMock(return_value=mock_history)):
                        with patch('app.agents.simple_chat.get_chat_agent', AsyncMock(return_value=(mock_agent, {}, "system prompt", []))):
                            with patch('app.config.load_config', return_value={"model_settings": {"model": "test-model"}}):
                                
                                agent, deps, breakdown, prompt, tools, history, model = \
                                    await service.setup_execution_context(session_id=session_id)
        
        # Verify return values
        assert agent == mock_agent
        assert deps == mock_deps
        assert prompt == "system prompt"
        assert history == mock_history
        assert model == "test-model"
    
    @pytest.mark.asyncio
    async def test_setup_execution_context_with_account_id(self):
        """Test context setup with account_id properly converted."""
        service = AgentExecutionService()
        
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        account_id = uuid4()
        
        mock_deps = Mock()
        mock_agent = Mock()
        
        with patch('app.agents.config_loader.get_agent_history_limit', AsyncMock(return_value=20)):
            with patch('app.agents.base.dependencies.SessionDependencies.create', AsyncMock(return_value=mock_deps)):
                with patch('app.agents.config_loader.get_agent_model_settings', AsyncMock(return_value={})):
                    with patch('app.agents.simple_chat.load_conversation_history', AsyncMock(return_value=[])):
                        with patch('app.agents.simple_chat.get_chat_agent', AsyncMock(return_value=(mock_agent, {}, "prompt", []))):
                            with patch('app.config.load_config', return_value={"model_settings": {"model": "test"}}):
                                
                                agent, deps, *rest = await service.setup_execution_context(
                                    session_id=session_id,
                                    account_id=account_id
                                )
        
        # Verify account_id was set on session_deps
        assert deps.account_id == account_id
    
    @pytest.mark.asyncio
    async def test_setup_execution_context_injects_system_prompt(self):
        """Test that system prompt is injected into message history."""
        service = AgentExecutionService()
        
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create message history without system prompt
        user_part = UserPromptPart(content="Hello")
        first_msg = ModelRequest(parts=[user_part])
        mock_history = [first_msg]
        
        mock_deps = Mock()
        mock_agent = Mock()
        system_prompt_text = "You are a helpful assistant"
        
        with patch('app.agents.config_loader.get_agent_history_limit', AsyncMock(return_value=20)):
            with patch('app.agents.base.dependencies.SessionDependencies.create', AsyncMock(return_value=mock_deps)):
                with patch('app.agents.config_loader.get_agent_model_settings', AsyncMock(return_value={})):
                    with patch('app.agents.simple_chat.load_conversation_history', AsyncMock(return_value=mock_history)):
                        with patch('app.agents.simple_chat.get_chat_agent', AsyncMock(return_value=(mock_agent, {}, system_prompt_text, []))):
                            with patch('app.config.load_config', return_value={"model_settings": {"model": "test"}}):
                                
                                agent, deps, breakdown, prompt, tools, history, model = \
                                    await service.setup_execution_context(session_id=session_id)
        
        # Verify system prompt was injected
        assert len(history) == 1
        assert isinstance(history[0], ModelRequest)
        assert len(history[0].parts) == 2  # SystemPromptPart + UserPromptPart
        assert isinstance(history[0].parts[0], SystemPromptPart)
        assert history[0].parts[0].content == system_prompt_text
    
    @pytest.mark.asyncio
    async def test_setup_execution_context_skips_duplicate_system_prompt(self):
        """Test that system prompt is not injected if already present."""
        service = AgentExecutionService()
        
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create message history with system prompt already present
        system_part = SystemPromptPart(content="Existing prompt")
        user_part = UserPromptPart(content="Hello")
        first_msg = ModelRequest(parts=[system_part, user_part])
        mock_history = [first_msg]
        
        mock_deps = Mock()
        mock_agent = Mock()
        
        with patch('app.agents.config_loader.get_agent_history_limit', AsyncMock(return_value=20)):
            with patch('app.agents.base.dependencies.SessionDependencies.create', AsyncMock(return_value=mock_deps)):
                with patch('app.agents.config_loader.get_agent_model_settings', AsyncMock(return_value={})):
                    with patch('app.agents.simple_chat.load_conversation_history', AsyncMock(return_value=mock_history)):
                        with patch('app.agents.simple_chat.get_chat_agent', AsyncMock(return_value=(mock_agent, {}, "new prompt", []))):
                            with patch('app.config.load_config', return_value={"model_settings": {"model": "test"}}):
                                
                                agent, deps, breakdown, prompt, tools, history, model = \
                                    await service.setup_execution_context(session_id=session_id)
        
        # Verify system prompt was NOT duplicated
        assert len(history) == 1
        assert len(history[0].parts) == 2  # Still just 2 parts
        assert history[0].parts[0].content == "Existing prompt"  # Original preserved
    
    @pytest.mark.asyncio
    async def test_setup_execution_context_with_instance_config(self):
        """Test context setup with instance-specific configuration."""
        service = AgentExecutionService()
        
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        instance_config = {"model_settings": {"model": "custom-model"}}
        
        mock_deps = Mock()
        mock_agent = Mock()
        
        with patch('app.agents.config_loader.get_agent_history_limit', AsyncMock(return_value=20)):
            with patch('app.agents.base.dependencies.SessionDependencies.create', AsyncMock(return_value=mock_deps)):
                with patch('app.agents.config_loader.get_agent_model_settings', AsyncMock(return_value={})):
                    with patch('app.agents.simple_chat.load_conversation_history', AsyncMock(return_value=[])):
                        with patch('app.agents.simple_chat.get_chat_agent', AsyncMock(return_value=(mock_agent, {}, "prompt", []))):
                            
                            agent, deps, breakdown, prompt, tools, history, model = \
                                await service.setup_execution_context(
                                    session_id=session_id,
                                    instance_config=instance_config
                                )
        
        # Verify instance_config was passed to session_deps
        assert deps.agent_config == instance_config
        # Verify model was extracted from instance_config
        assert model == "custom-model"


class TestExecuteAgent:
    """Test suite for execute_agent() method."""
    
    @pytest.mark.asyncio
    async def test_execute_agent_non_streaming(self):
        """Test non-streaming agent execution."""
        service = AgentExecutionService()
        
        # Mock agent and dependencies
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.output = "Test response"
        mock_agent.run = AsyncMock(return_value=mock_result)
        
        mock_deps = Mock()
        mock_history = []
        session_id = "test-session"
        
        result, latency_ms = await service.execute_agent(
            agent=mock_agent,
            message="Hello",
            session_deps=mock_deps,
            message_history=mock_history,
            session_id=session_id,
            streaming=False
        )
        
        # Verify agent.run was called
        mock_agent.run.assert_called_once_with(
            "Hello",
            deps=mock_deps,
            message_history=mock_history
        )
        
        # Verify result and timing
        assert result == mock_result
        assert isinstance(latency_ms, int)
        assert latency_ms >= 0
    
    @pytest.mark.asyncio
    async def test_execute_agent_streaming(self):
        """Test streaming agent execution."""
        service = AgentExecutionService()
        
        # Mock agent and dependencies
        mock_agent = Mock()
        mock_stream = Mock()
        mock_agent.run_stream = Mock(return_value=mock_stream)
        
        mock_deps = Mock()
        mock_history = []
        session_id = "test-session"
        
        stream, latency_ms = await service.execute_agent(
            agent=mock_agent,
            message="Hello",
            session_deps=mock_deps,
            message_history=mock_history,
            session_id=session_id,
            streaming=True
        )
        
        # Verify agent.run_stream was called
        mock_agent.run_stream.assert_called_once_with(
            "Hello",
            deps=mock_deps,
            message_history=mock_history
        )
        
        # Verify stream and timing
        assert stream == mock_stream
        assert isinstance(latency_ms, int)
        assert latency_ms >= 0
    
    @pytest.mark.asyncio
    async def test_execute_agent_with_error(self):
        """Test agent execution error handling."""
        service = AgentExecutionService()
        
        # Mock agent that raises an error
        mock_agent = Mock()
        mock_agent.run = AsyncMock(side_effect=Exception("Test error"))
        
        mock_deps = Mock()
        mock_history = []
        session_id = "test-session"
        
        with pytest.raises(Exception, match="Test error"):
            await service.execute_agent(
                agent=mock_agent,
                message="Hello",
                session_deps=mock_deps,
                message_history=mock_history,
                session_id=session_id,
                streaming=False
            )
    
    @pytest.mark.asyncio
    async def test_execute_agent_measures_timing(self):
        """Test that execution timing is accurately measured."""
        service = AgentExecutionService()
        
        # Mock agent with delayed execution
        mock_agent = Mock()
        async def delayed_run(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.01)  # 10ms delay
            return Mock(output="Response")
        mock_agent.run = delayed_run
        
        mock_deps = Mock()
        mock_history = []
        session_id = "test-session"
        
        result, latency_ms = await service.execute_agent(
            agent=mock_agent,
            message="Hello",
            session_deps=mock_deps,
            message_history=mock_history,
            session_id=session_id,
            streaming=False
        )
        
        # Verify timing captured (should be at least 10ms)
        assert latency_ms >= 10


class TestGetAgentExecutionService:
    """Test suite for get_agent_execution_service() function."""
    
    def test_get_agent_execution_service_singleton(self):
        """Test that get_agent_execution_service returns singleton."""
        from app.services.agent_execution_service import get_agent_execution_service
        
        service1 = get_agent_execution_service()
        service2 = get_agent_execution_service()
        
        # Verify same instance
        assert service1 is service2
        assert isinstance(service1, AgentExecutionService)

