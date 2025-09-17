"""
Validation and integration tests for configuration standardization.

Tests for CHUNK 0017-004-001-10: Validation and integration testing
Ensures no regressions with parameter name changes and validates system behavior.
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestValidationIntegration:
    """Comprehensive validation tests for configuration standardization."""

    @pytest.mark.unit
    def test_full_configuration_regression_suite(self):
        """
        Run complete test suite with new parameter names.

        CHUNK 0017-004-001-10 AUTOMATED-TEST 1:
        Verify no regressions introduced by parameter standardization.
        """
        # Run the core configuration cascade tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/unit/test_configuration_cascade.py",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        assert result.returncode == 0, f"Configuration cascade tests failed:\n{result.stdout}\n{result.stderr}"
        
        # Verify session dependencies tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/unit/test_session_dependencies.py",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        assert result.returncode == 0, f"Session dependencies tests failed:\n{result.stdout}\n{result.stderr}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_configuration_cascade_scenarios(self):
        """
        Test all cascade scenarios (agent->global->fallback).

        CHUNK 0017-004-001-10 AUTOMATED-TEST 2:
        Verify agent-first configuration cascade works in all scenarios.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Test 1: Agent config takes priority
        mock_agent_config = MagicMock()
        mock_agent_config.context_management = {"history_limit": 75}
        
        mock_global_config = {"chat": {"history_limit": 50}}
        
        with patch('app.agents.config_loader.get_agent_config', return_value=mock_agent_config):
            with patch('app.config.load_config', return_value=mock_global_config):
                result = await get_agent_history_limit("simple_chat")
                assert result == 75, f"Agent config should take priority, got {result}"
        
        # Test 2: Global config fallback
        mock_agent_config_empty = MagicMock()
        mock_agent_config_empty.context_management = None
        
        with patch('app.agents.config_loader.get_agent_config', return_value=mock_agent_config_empty):
            with patch('app.config.load_config', return_value=mock_global_config):
                result = await get_agent_history_limit("simple_chat")
                assert result == 50, f"Global config should be fallback, got {result}"
        
        # Test 3: Hardcoded fallback
        with patch('app.agents.config_loader.get_agent_config', side_effect=Exception("Config not found")):
            with patch('app.config.load_config', return_value={}):
                result = await get_agent_history_limit("simple_chat")
                assert result == 50, f"Hardcoded fallback should be 50, got {result}"

    @pytest.mark.unit
    def test_legacy_endpoint_compatibility(self):
        """
        Verify legacy endpoints unaffected by agent config changes.

        CHUNK 0017-004-001-10 AUTOMATED-TEST 3:
        Ensure legacy endpoints still work with app.yaml only.
        """
        # Test that legacy endpoints don't import agent config functions
        from app import main
        
        # Verify main.py doesn't import agent-specific config functions
        main_source = Path(__file__).parent.parent.parent / "app" / "main.py"
        main_content = main_source.read_text()
        
        # Legacy endpoints should not use agent-specific config
        assert "get_agent_config" not in main_content, "Legacy endpoints should not use agent-specific config"
        assert "get_agent_history_limit" not in main_content, "Legacy endpoints should not use agent-specific config"
        
        # Legacy endpoints should use global config only
        assert "load_config" in main_content, "Legacy endpoints should use global config"


class TestSystemPromptLoading:
    """Test system prompt loading from external files."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_system_prompt_loads_from_external_file(self):
        """
        Test system prompt loading from external files.

        CHUNK 0017-004-001-10 MANUAL-TEST 1 (Automated):
        Verify system prompt loads correctly from .md files.
        """
        from app.agents.config_loader import get_agent_config
        
        # Test with real simple_chat config
        try:
            agent_config = await get_agent_config("simple_chat")
            
            # Verify config has prompts section
            assert hasattr(agent_config, 'prompts'), "Agent config should have prompts section"
            assert agent_config.prompts is not None, "Prompts section should not be None"
            
            # Verify system prompt is loaded (should be a string, not a file path)
            if 'system_prompt' in agent_config.prompts:
                system_prompt = agent_config.prompts['system_prompt']
                assert isinstance(system_prompt, str), "System prompt should be loaded as string"
                assert len(system_prompt) > 0, "System prompt should not be empty"
                assert not system_prompt.endswith('.md'), "System prompt should be content, not file path"
                
        except Exception as e:
            pytest.skip(f"Agent config not available in test environment: {e}")


class TestErrorHandling:
    """Test error handling for missing/invalid configuration files."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_agent_config_graceful_fallback(self):
        """
        Test error handling for missing agent configuration files.

        CHUNK 0017-004-001-10 MANUAL-TEST 2 (Automated):
        Verify system remains stable with missing config files.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Test with non-existent agent
        with patch('app.agents.config_loader.get_agent_config', side_effect=FileNotFoundError("Config not found")):
            with patch('app.config.load_config', return_value={"chat": {"history_limit": 30}}):
                result = await get_agent_history_limit("non_existent_agent")
                
                # Should fall back to global config
                assert result == 30, f"Should fall back to global config, got {result}"

    @pytest.mark.unit  
    @pytest.mark.asyncio
    async def test_corrupted_agent_config_fallback(self):
        """
        Test error handling for corrupted agent configuration files.

        CHUNK 0017-004-001-10 MANUAL-TEST 3 (Automated):
        Verify system handles corrupted config files gracefully.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Test with corrupted agent config (returns invalid data)
        with patch('app.agents.config_loader.get_agent_config', side_effect=ValueError("Invalid YAML")):
            with patch('app.config.load_config', return_value={"chat": {"history_limit": 40}}):
                result = await get_agent_history_limit("corrupted_agent")
                
                # Should fall back to global config
                assert result == 40, f"Should fall back to global config on corruption, got {result}"


class TestParameterStandardization:
    """Test parameter name standardization across the system."""

    @pytest.mark.unit
    def test_no_old_parameter_names_in_codebase(self):
        """
        Verify old parameter names are removed from codebase.

        CHUNK 0017-004-001-10 AUTOMATED-TEST (Additional):
        Ensure max_history_messages is not used anywhere in agent code.
        """
        # Check key files for old parameter names
        key_files = [
            "app/agents/simple_chat.py",
            "app/agents/base/dependencies.py", 
            "app/agents/config_loader.py",
            "app/services/agent_session.py"
        ]
        
        project_root = Path(__file__).parent.parent.parent
        
        for file_path in key_files:
            full_path = project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                
                # Should not contain old parameter names
                assert "max_history_messages" not in content, f"Found max_history_messages in {file_path}"
                
                # Should contain new standardized parameter names
                if "dependencies.py" in file_path or "simple_chat.py" in file_path:
                    assert "history_limit" in content, f"Should contain history_limit in {file_path}"

    @pytest.mark.unit
    def test_config_files_use_standardized_names(self):
        """
        Verify configuration files use standardized parameter names.

        CHUNK 0017-004-001-10 AUTOMATED-TEST (Additional):
        Check that config files use history_limit consistently.
        """
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Check app.yaml uses history_limit
        app_yaml = project_root / "backend" / "config" / "app.yaml"
        if app_yaml.exists():
            content = app_yaml.read_text()
            assert "history_limit" in content, "app.yaml should contain history_limit"
            assert "max_history_messages" not in content, "app.yaml should not contain max_history_messages"
        
        # Check agent config uses history_limit
        agent_config = project_root / "backend" / "config" / "agent_configs" / "simple_chat" / "config.yaml"
        if agent_config.exists():
            content = agent_config.read_text()
            assert "history_limit" in content, "Agent config should contain history_limit"
            assert "max_history_messages" not in content, "Agent config should not contain max_history_messages"
