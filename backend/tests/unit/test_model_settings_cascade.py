"""
Tests for model settings cascade implementation.

Tests for CHUNK 0017-004-003-01: Model settings cascade implementation
Verifies generic cascade infrastructure, model settings cascade, and monitoring integration.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


class TestGenericCascadeInfrastructure:
    """Test generic cascade infrastructure."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generic_cascade_infrastructure(self):
        """
        Verify reusable get_agent_parameter function works for any parameter.

        CHUNK 0017-004-003-01 AUTOMATED-TEST 1:
        Verify reusable get_agent_parameter function works for any parameter.
        """
        from app.agents.config_loader import get_agent_parameter

        # Test with agent config success
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.agents.cascade_monitor.logger') as mock_logger:
                # Setup agent config mock with nested structure
                mock_agent_config = MagicMock()
                mock_agent_config.model_settings = {"temperature": 0.5}
                mock_agent_config.tools = {"vector_search": {"enabled": True}}
                mock_get_config.return_value = mock_agent_config

                # Test model parameter
                result = await get_agent_parameter("test_agent", "model_settings.temperature", 0.7)
                assert result == 0.5

                # Test tool parameter
                result = await get_agent_parameter("test_agent", "tools.vector_search.enabled", False)
                assert result is True

                # Verify audit logging was called
                assert mock_logger.debug.called or mock_logger.info.called or mock_logger.warning.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generic_cascade_global_fallback(self):
        """
        Test generic cascade with global config fallback.

        CHUNK 0017-004-003-01 AUTOMATED-TEST (Additional):
        Test generic cascade global config fallback with custom paths.
        """
        from app.agents.config_loader import get_agent_parameter

        # Mock agent config to fail, global config to succeed
        with patch('app.agents.config_loader.get_agent_config') as mock_get_agent_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup mocks: agent config missing parameter, global config has it
                    mock_agent_config = MagicMock()
                    mock_agent_config.model_settings = {}  # Missing temperature
                    mock_get_agent_config.return_value = mock_agent_config
                    
                    mock_load_config.return_value = {"llm": {"temperature": 0.3}}

                    # Test with custom global path
                    result = await get_agent_parameter(
                        "test_agent", 
                        "model_settings.temperature", 
                        0.7,
                        global_path="llm.temperature"
                    )
                    assert result == 0.3

    @pytest.mark.unit
    @pytest.mark.asyncio 
    async def test_generic_cascade_hardcoded_fallback(self):
        """
        Test generic cascade with hardcoded fallback.

        CHUNK 0017-004-003-01 AUTOMATED-TEST (Additional):
        Test generic cascade hardcoded fallback when all sources fail.
        """
        from app.agents.config_loader import get_agent_parameter

        # Mock both agent and global config to fail
        with patch('app.agents.config_loader.get_agent_config') as mock_get_agent_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup mocks to fail
                    mock_get_agent_config.side_effect = Exception("Agent config not found")
                    mock_load_config.side_effect = Exception("Global config not found")

                    # Test fallback
                    result = await get_agent_parameter("test_agent", "model_settings.temperature", 0.8)
                    assert result == 0.8

                    # Verify fallback usage was logged
                    warning_calls = mock_logger.warning.call_args_list
                    fallback_warning = None
                    for call in warning_calls:
                        if call[0] and isinstance(call[0][0], dict):
                            log_data = call[0][0]
                            if log_data.get("event") == "cascade_fallback_usage":
                                fallback_warning = log_data
                                break
                    
                    assert fallback_warning is not None
                    assert fallback_warning["parameter"] == "model_settings.temperature"


class TestModelSettingsCascade:
    """Test model settings cascade functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_settings_cascade_priority(self):
        """
        Agent model overrides global model.

        CHUNK 0017-004-003-01 AUTOMATED-TEST 2:
        Agent model overrides global model.
        """
        from app.agents.config_loader import get_agent_model_settings

        # Mock agent config with model settings
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup agent config with model settings
                    mock_agent_config = MagicMock()
                    mock_agent_config.model_settings = {
                        "model": "agent-specific-model",
                        "temperature": 0.5,
                        "max_tokens": 3000
                    }
                    mock_get_config.return_value = mock_agent_config
                    
                    # Setup global config (should be overridden)
                    mock_load_config.return_value = {
                        "llm": {
                            "model": "global-model",
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    }

                    # Call function
                    result = await get_agent_model_settings("test_agent")

                    # Verify agent config takes priority
                    assert result["model"] == "agent-specific-model"
                    assert result["temperature"] == 0.5
                    assert result["max_tokens"] == 3000

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_settings_cascade_fallback(self):
        """
        Global model used when agent missing.

        CHUNK 0017-004-003-01 AUTOMATED-TEST 3:
        Global model used when agent missing.
        """
        from app.agents.config_loader import get_agent_model_settings

        # Mock agent config to fail, global config to succeed
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup mocks: agent config fails
                    mock_get_config.side_effect = Exception("Agent config not found")
                    
                    # Setup global config
                    mock_load_config.return_value = {
                        "llm": {
                            "model": "global-fallback-model",
                            "temperature": 0.3,
                            "max_tokens": 2000
                        }
                    }

                    # Call function
                    result = await get_agent_model_settings("test_agent")

                    # Verify global config is used
                    assert result["model"] == "global-fallback-model"
                    assert result["temperature"] == 0.3
                    assert result["max_tokens"] == 2000

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_settings_parameter_inheritance(self):
        """
        Individual parameters cascade independently with mixed inheritance.

        CHUNK 0017-004-003-01 AUTOMATED-TEST 4:
        Individual parameters cascade independently with mixed inheritance.
        """
        from app.agents.config_loader import get_agent_model_settings

        # Mock mixed inheritance scenario
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup agent config with partial model settings
                    mock_agent_config = MagicMock()
                    mock_agent_config.model_settings = {
                        "model": "agent-model",  # Agent-specific
                        # temperature: missing - should inherit from global
                        "max_tokens": 4000       # Agent-specific
                    }
                    mock_get_config.return_value = mock_agent_config
                    
                    # Setup global config
                    mock_load_config.return_value = {
                        "llm": {
                            "model": "global-model",      # Should be overridden
                            "temperature": 0.4,           # Should be used (mixed inheritance)
                            "max_tokens": 1500            # Should be overridden
                        }
                    }

                    # Call function
                    result = await get_agent_model_settings("test_agent")

                    # Verify mixed inheritance
                    assert result["model"] == "agent-model"        # From agent config
                    assert result["temperature"] == 0.4           # From global config
                    assert result["max_tokens"] == 4000           # From agent config

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_settings_monitoring_integration(self):
        """
        Verify CascadeAuditTrail integration for model parameters.

        CHUNK 0017-004-003-01 AUTOMATED-TEST 5:
        Verify CascadeAuditTrail integration for model parameters.
        """
        from app.agents.config_loader import get_agent_model_settings

        # Mock successful agent config
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.agents.cascade_monitor.logger') as mock_logger:
                # Setup agent config
                mock_agent_config = MagicMock()
                mock_agent_config.model_settings = {
                    "model": "monitored-model",
                    "temperature": 0.6,
                    "max_tokens": 2500
                }
                mock_get_config.return_value = mock_agent_config

                # Call function
                result = await get_agent_model_settings("test_agent")

                # Verify result
                assert result["model"] == "monitored-model"

                # Verify comprehensive audit logging was called for each parameter
                log_calls = mock_logger.debug.call_args_list + mock_logger.info.call_args_list + mock_logger.warning.call_args_list
                
                # Should have audit logs for model, temperature, and max_tokens
                audit_logs = []
                for call in log_calls:
                    if call[0] and isinstance(call[0][0], dict):
                        log_data = call[0][0]
                        if log_data.get("event") == "cascade_decision_audit":
                            audit_logs.append(log_data)
                
                # Should have 3 audit logs (one for each parameter)
                assert len(audit_logs) == 3
                
                # Verify each parameter was logged
                logged_parameters = [log["parameter"] for log in audit_logs]
                assert "model_settings.model" in logged_parameters
                assert "model_settings.temperature" in logged_parameters
                assert "model_settings.max_tokens" in logged_parameters


class TestHistoryLimitRefactoring:
    """Test that get_agent_history_limit uses generic infrastructure."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_history_limit_uses_generic_infrastructure(self):
        """
        Verify get_agent_history_limit uses generic cascade infrastructure.

        CHUNK 0017-004-003-01 AUTOMATED-TEST (Additional):
        Verify history_limit refactoring to use generic infrastructure.
        """
        from app.agents.config_loader import get_agent_history_limit

        # Mock agent config with history_limit
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.agents.cascade_monitor.logger') as mock_logger:
                # Setup agent config
                mock_agent_config = MagicMock()
                mock_agent_config.context_management = {"history_limit": 75}
                mock_get_config.return_value = mock_agent_config

                # Call function
                result = await get_agent_history_limit("test_agent")

                # Verify result
                assert result == 75

                # Verify audit logging was called (proof of generic infrastructure usage)
                log_calls = mock_logger.debug.call_args_list + mock_logger.info.call_args_list + mock_logger.warning.call_args_list
                audit_log = None
                for call in log_calls:
                    if call[0] and isinstance(call[0][0], dict):
                        log_data = call[0][0]
                        if log_data.get("event") == "cascade_decision_audit" and log_data.get("parameter") == "context_management.history_limit":
                            audit_log = log_data
                            break
                
                assert audit_log is not None
                assert audit_log["successful_source"] == "agent_config"
                assert audit_log["final_value"] == 75


class TestSimpleChatIntegration:
    """Test integration with simple_chat.py."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_simple_chat_uses_centralized_model_cascade(self):
        """
        Verify simple_chat.py uses centralized model settings cascade.

        CHUNK 0017-004-003-01 AUTOMATED-TEST (Additional):
        Verify simple_chat integration with centralized cascade.
        """
        from app.agents.simple_chat import simple_chat

        # Mock all dependencies
        with patch('app.agents.config_loader.get_agent_model_settings') as mock_get_model_settings:
            with patch('app.agents.config_loader.get_agent_history_limit') as mock_get_history_limit:
                with patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create:
                    with patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent:
                        with patch('app.agents.simple_chat.load_conversation_history') as mock_load_history:
                            with patch('app.services.agent_session.get_session_stats') as mock_get_stats:
                                # Setup mocks
                                mock_get_model_settings.return_value = {
                                    "model": "test-cascade-model",
                                    "temperature": 0.5,
                                    "max_tokens": 2000
                                }
                                mock_get_history_limit.return_value = 50
                                
                                mock_session_deps = MagicMock()
                                mock_session_create.return_value = mock_session_deps
                                
                                mock_agent = AsyncMock()
                                mock_result = MagicMock()
                                mock_result.output = "Test response"
                                mock_usage = MagicMock()
                                mock_usage.input_tokens = 10
                                mock_usage.output_tokens = 20
                                mock_usage.total_tokens = 30
                                mock_result.usage.return_value = mock_usage
                                mock_result.new_messages.return_value = []
                                mock_agent.run.return_value = mock_result
                                mock_get_chat_agent.return_value = mock_agent
                                
                                mock_load_history.return_value = []
                                mock_get_stats.return_value = {}

                                # Call simple_chat
                                session_id = str(uuid4())
                                result = await simple_chat("test message", session_id)

                                # Verify centralized model cascade was called
                                mock_get_model_settings.assert_called_with("simple_chat")
                                
                                # Verify result
                                assert "response" in result
                                assert result["response"] == "Test response"
