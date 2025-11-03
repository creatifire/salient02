"""
Cascade consolidation tests for simple_chat.py.

Tests for CHUNK 0017-004-002-02: Consolidate cascade usage in simple_chat.py
Verifies that simple_chat.py uses centralized cascade functions consistently.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4


class TestCascadeConsolidation:
    """Test cascade consolidation in simple_chat.py."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_simple_chat_uses_centralized_cascade(self):
        """
        Verify simple_chat uses get_agent_history_limit for all history limit needs.

        CHUNK 0017-004-002-02 AUTOMATED-TEST 1:
        Verify simple_chat uses get_agent_history_limit consistently.
        """
        from app.agents.simple_chat import simple_chat

        # Mock the centralized cascade function
        with patch('app.agents.config_loader.get_agent_history_limit') as mock_get_limit:
            with patch('app.agents.simple_chat.get_agent_config') as mock_get_config:
                with patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create:
                    with patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent:
                        with patch('app.agents.simple_chat.load_conversation_history') as mock_load_history:
                            with patch('app.services.agent_session.get_session_stats') as mock_get_stats:
                                # Setup mocks
                                mock_get_limit.return_value = 75
                                mock_agent_config = MagicMock()
                                mock_agent_config.model_settings = {"model": "test-model"}
                                mock_get_config.return_value = mock_agent_config
                                
                                mock_session_deps = MagicMock()
                                mock_session_create.return_value = mock_session_deps
                                
                                mock_agent = AsyncMock()
                                mock_result = MagicMock()
                                mock_result.output = "Test response"
                                mock_result.usage.return_value = MagicMock(input_tokens=10, output_tokens=20, total_tokens=30)
                                mock_result.new_messages.return_value = []
                                mock_agent.run.return_value = mock_result
                                mock_get_chat_agent.return_value = mock_agent
                                
                                mock_load_history.return_value = []
                                mock_get_stats.return_value = {}

                                # Call simple_chat
                                session_id = str(uuid4())
                                result = await simple_chat("test message", session_id)

                                # Verify get_agent_history_limit was called for SessionDependencies creation
                                mock_get_limit.assert_called_with("simple_chat")
                                
                                # Verify SessionDependencies.create was called with cascade result
                                mock_session_create.assert_called_once()
                                call_kwargs = mock_session_create.call_args[1]
                                assert call_kwargs['history_limit'] == 75, "SessionDependencies should use cascade result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cascade_consistency_across_entry_points(self):
        """
        Verify all entry points use same cascade logic.

        CHUNK 0017-004-002-02 AUTOMATED-TEST 2:
        Verify all entry points use same cascade logic.
        """
        from app.agents.simple_chat import load_conversation_history, simple_chat

        # Test that load_conversation_history uses centralized cascade
        with patch('app.agents.config_loader.get_agent_history_limit') as mock_get_limit:
            with patch('app.agents.simple_chat.get_message_service') as mock_get_service:
                # Setup mocks
                mock_get_limit.return_value = 100
                mock_service = AsyncMock()
                mock_service.get_session_messages.return_value = []
                mock_get_service.return_value = mock_service

                # Call load_conversation_history with None max_messages
                session_id = str(uuid4())
                await load_conversation_history(session_id, max_messages=None)

                # Verify centralized cascade was used
                mock_get_limit.assert_called_with("simple_chat")

        # Test that simple_chat also uses centralized cascade
        with patch('app.agents.config_loader.get_agent_history_limit') as mock_get_limit:
            with patch('app.agents.simple_chat.get_agent_config') as mock_get_config:
                with patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create:
                    with patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent:
                        with patch('app.agents.simple_chat.load_conversation_history') as mock_load_history:
                            with patch('app.services.agent_session.get_session_stats') as mock_get_stats:
                                # Setup mocks
                                mock_get_limit.return_value = 100
                                mock_agent_config = MagicMock()
                                mock_agent_config.model_settings = {"model": "test-model"}
                                mock_get_config.return_value = mock_agent_config
                                
                                mock_session_deps = MagicMock()
                                mock_session_create.return_value = mock_session_deps
                                
                                mock_agent = AsyncMock()
                                mock_result = MagicMock()
                                mock_result.output = "Test response"
                                mock_result.usage.return_value = MagicMock(input_tokens=10, output_tokens=20, total_tokens=30)
                                mock_result.new_messages.return_value = []
                                mock_agent.run.return_value = mock_result
                                mock_get_chat_agent.return_value = mock_agent
                                
                                mock_load_history.return_value = []
                                mock_get_stats.return_value = {}

                                # Call simple_chat
                                session_id = str(uuid4())
                                await simple_chat("test message", session_id)

                                # Verify both entry points would use same cascade function
                                mock_get_limit.assert_called_with("simple_chat")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_session_dependencies_cascade_integration(self):
        """
        Test SessionDependencies uses cascade properly.

        CHUNK 0017-004-002-02 AUTOMATED-TEST 3:
        Test SessionDependencies uses cascade properly.
        """
        from app.agents.simple_chat import simple_chat

        # Test with different cascade values
        test_cases = [
            {"cascade_value": 25, "expected": 25},
            {"cascade_value": 150, "expected": 150},
            {"cascade_value": 50, "expected": 50},  # Default fallback
        ]

        for case in test_cases:
            with patch('app.agents.config_loader.get_agent_history_limit') as mock_get_limit:
                with patch('app.agents.simple_chat.get_agent_config') as mock_get_config:
                    with patch('app.agents.simple_chat.SessionDependencies.create') as mock_session_create:
                        with patch('app.agents.simple_chat.get_chat_agent') as mock_get_chat_agent:
                            with patch('app.agents.simple_chat.load_conversation_history') as mock_load_history:
                                with patch('app.services.agent_session.get_session_stats') as mock_get_stats:
                                    # Setup mocks
                                    mock_get_limit.return_value = case["cascade_value"]
                                    mock_agent_config = MagicMock()
                                    mock_agent_config.model_settings = {"model": "test-model"}
                                    mock_get_config.return_value = mock_agent_config
                                    
                                    mock_session_deps = MagicMock()
                                    mock_session_create.return_value = mock_session_deps
                                    
                                    mock_agent = AsyncMock()
                                    mock_result = MagicMock()
                                    mock_result.output = "Test response"
                                    mock_result.usage.return_value = MagicMock(input_tokens=10, output_tokens=20, total_tokens=30)
                                    mock_result.new_messages.return_value = []
                                    mock_agent.run.return_value = mock_result
                                    mock_get_chat_agent.return_value = mock_agent
                                    
                                    mock_load_history.return_value = []
                                    mock_get_stats.return_value = {}

                                    # Call simple_chat
                                    session_id = str(uuid4())
                                    await simple_chat("test message", session_id)

                                    # Verify SessionDependencies.create was called with cascade result
                                    mock_session_create.assert_called_once()
                                    call_kwargs = mock_session_create.call_args[1]
                                    assert call_kwargs['history_limit'] == case["expected"], \
                                        f"Expected {case['expected']}, got {call_kwargs['history_limit']} for cascade value {case['cascade_value']}"


class TestNoDuplicateCascadeLogic:
    """Test that duplicate cascade logic has been removed."""

    @pytest.mark.unit
    def test_no_inline_cascade_logic_in_simple_chat(self):
        """
        Verify no inline cascade logic remains in simple_chat.py.

        CHUNK 0017-004-002-02 AUTOMATED-TEST (Additional):
        Ensure duplicate cascade implementations are removed.
        """
        import inspect
        from app.agents import simple_chat

        # Get the source code of simple_chat.py
        source = inspect.getsource(simple_chat)
        
        # These patterns should not exist anymore (inline cascade logic)
        forbidden_patterns = [
            "chat_config.get(\"history_limit\"",  # Direct global config access
            "context_management.get('history_limit')",  # Inline agent config access
            "agent_history_limit = None",  # Manual cascade variable
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Found forbidden inline cascade pattern: {pattern}"
        
        # These patterns should exist (centralized cascade usage)
        required_patterns = [
            "get_agent_history_limit",  # Centralized cascade function usage
        ]
        
        for pattern in required_patterns:
            assert pattern in source, f"Missing required centralized cascade pattern: {pattern}"

    @pytest.mark.unit
    def test_consistent_cascade_function_usage(self):
        """
        Verify consistent usage of cascade functions.

        CHUNK 0017-004-002-02 AUTOMATED-TEST (Additional):
        Ensure all cascade usage follows the same pattern.
        """
        import inspect
        from app.agents import simple_chat

        # Get the source code
        source = inspect.getsource(simple_chat)
        
        # Count occurrences of get_agent_history_limit
        cascade_calls = source.count("get_agent_history_limit")
        
        # Should have at least 2 calls (SessionDependencies creation + load_conversation_history)
        assert cascade_calls >= 2, f"Expected at least 2 cascade function calls, found {cascade_calls}"
        
        # Should not have any direct config access for history_limit
        direct_config_access = source.count("chat_config.get(\"history_limit\"")
        assert direct_config_access == 0, f"Found {direct_config_access} instances of direct config access"
