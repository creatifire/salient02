"""
Unit tests for profile_capture configuration loading.

Tests verify that profile_capture configuration loads correctly from agent
config.yaml files as specified in chunk 0017-006-001-01.
"""

# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

import pytest
from pathlib import Path
import yaml


class TestProfileConfigLoading:
    """Test suite for profile_capture configuration loading."""
    
    @pytest.fixture
    def configs_dir(self):
        """Get the agent configs directory path."""
        backend_dir = Path(__file__).parent.parent.parent
        return backend_dir / "config" / "agent_configs"
    
    def load_agent_config(self, configs_dir: Path, account: str, instance: str) -> dict:
        """Helper to load agent config YAML."""
        config_path = configs_dir / account / instance / "config.yaml"
        assert config_path.exists(), f"Config file not found: {config_path}"
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_profile_config_loads(self, configs_dir):
        """Test that profile_capture config loads from agent YAML files."""
        # Test all agent configs have profile_capture section
        test_agents = [
            ("wyckoff", "wyckoff_info_chat1"),
            ("windriver", "windriver_info_chat1"),
            ("prepexcellence", "prepexcel_info_chat1"),
            ("agrofresh", "agro_info_chat1"),
            ("default_account", "simple_chat1"),
            ("default_account", "simple_chat2"),
            ("acme", "acme_chat1"),
        ]
        
        for account, instance in test_agents:
            config = self.load_agent_config(configs_dir, account, instance)
            
            # Verify tools section exists
            assert "tools" in config, f"{account}/{instance}: 'tools' section missing"
            
            # Verify profile_capture section exists
            assert "profile_capture" in config["tools"], \
                f"{account}/{instance}: 'profile_capture' not found in tools"
            
            profile_config = config["tools"]["profile_capture"]
            
            # Verify required fields exist
            assert "enabled" in profile_config, \
                f"{account}/{instance}: 'enabled' field missing"
            assert "schema_file" in profile_config, \
                f"{account}/{instance}: 'schema_file' field missing"
    
    def test_profile_config_defaults(self, configs_dir):
        """Test that default schema_file is 'profile.yaml'."""
        test_agents = [
            ("wyckoff", "wyckoff_info_chat1"),
            ("windriver", "windriver_info_chat1"),
            ("prepexcellence", "prepexcel_info_chat1"),
            ("agrofresh", "agro_info_chat1"),
            ("default_account", "simple_chat1"),
            ("default_account", "simple_chat2"),
            ("acme", "acme_chat1"),
        ]
        
        for account, instance in test_agents:
            config = self.load_agent_config(configs_dir, account, instance)
            profile_config = config["tools"]["profile_capture"]
            
            # Verify schema_file is "profile.yaml"
            assert profile_config["schema_file"] == "profile.yaml", \
                f"{account}/{instance}: Expected schema_file='profile.yaml', got '{profile_config['schema_file']}'"
    
    def test_profile_disabled_by_default(self, configs_dir):
        """Test that profile_capture is disabled for default_account agents."""
        # These agents should have profile_capture disabled
        disabled_agents = [
            ("default_account", "simple_chat1"),
            ("default_account", "simple_chat2"),
            ("acme", "acme_chat1"),
        ]
        
        for account, instance in disabled_agents:
            config = self.load_agent_config(configs_dir, account, instance)
            profile_config = config["tools"]["profile_capture"]
            
            assert profile_config["enabled"] is False, \
                f"{account}/{instance}: Expected enabled=False, got {profile_config['enabled']}"
    
    def test_profile_enabled_for_production_agents(self, configs_dir):
        """Test that profile_capture is enabled for production agents."""
        # These agents should have profile_capture enabled
        enabled_agents = [
            ("wyckoff", "wyckoff_info_chat1"),
            ("windriver", "windriver_info_chat1"),
            ("prepexcellence", "prepexcel_info_chat1"),
            ("agrofresh", "agro_info_chat1"),
        ]
        
        for account, instance in enabled_agents:
            config = self.load_agent_config(configs_dir, account, instance)
            profile_config = config["tools"]["profile_capture"]
            
            assert profile_config["enabled"] is True, \
                f"{account}/{instance}: Expected enabled=True, got {profile_config['enabled']}"
    
    def test_profile_config_structure_valid(self, configs_dir):
        """Test that profile_capture config structure is valid."""
        test_agents = [
            ("wyckoff", "wyckoff_info_chat1"),
            ("default_account", "simple_chat1"),
        ]
        
        for account, instance in test_agents:
            config = self.load_agent_config(configs_dir, account, instance)
            profile_config = config["tools"]["profile_capture"]
            
            # Verify data types
            assert isinstance(profile_config["enabled"], bool), \
                f"{account}/{instance}: 'enabled' must be boolean"
            assert isinstance(profile_config["schema_file"], str), \
                f"{account}/{instance}: 'schema_file' must be string"
            
            # Verify schema_file is not empty
            assert len(profile_config["schema_file"]) > 0, \
                f"{account}/{instance}: 'schema_file' cannot be empty"
    
    def test_profile_config_follows_tool_pattern(self, configs_dir):
        """Test that profile_capture follows same pattern as other tools."""
        # Check wyckoff config as reference
        config = self.load_agent_config(configs_dir, "wyckoff", "wyckoff_info_chat1")
        tools = config["tools"]
        
        # Verify profile_capture is at same level as other tools
        assert "profile_capture" in tools
        assert "vector_search" in tools
        assert "directory" in tools
        assert "web_search" in tools
        
        # Verify profile_capture has similar structure (enabled field)
        assert "enabled" in tools["profile_capture"]
        assert "enabled" in tools["vector_search"]
        assert "enabled" in tools["directory"]
        assert "enabled" in tools["web_search"]

