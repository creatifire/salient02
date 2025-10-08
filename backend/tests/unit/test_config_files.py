"""
Automated tests for multi-tenant agent configuration files.
Tests for 0022-001-001-01 - Test instance configuration files.
"""
import pytest
import yaml
from pathlib import Path

# Base path for agent configs
# Path(__file__) = backend/tests/unit/test_config_files.py
# .parent = backend/tests/unit/
# .parent.parent = backend/tests/
# .parent.parent.parent = backend/
CONFIG_BASE = Path(__file__).parent.parent.parent / "config" / "agent_configs"

# Test instances
TEST_INSTANCES = [
    ("default_account", "simple_chat1"),
    ("default_account", "simple_chat2"),
    ("acme", "acme_chat1"),
]


class TestConfigFilesExist:
    """Test that all required config files exist at correct paths."""
    
    @pytest.mark.parametrize("account,instance", TEST_INSTANCES)
    def test_config_yaml_exists(self, account, instance):
        """Verify config.yaml exists for each test instance."""
        config_path = CONFIG_BASE / account / instance / "config.yaml"
        assert config_path.exists(), f"Config file missing: {config_path}"
        assert config_path.is_file(), f"Config path is not a file: {config_path}"
    
    @pytest.mark.parametrize("account,instance", TEST_INSTANCES)
    def test_system_prompt_exists(self, account, instance):
        """Verify system_prompt.md exists for each test instance."""
        prompt_path = CONFIG_BASE / account / instance / "system_prompt.md"
        assert prompt_path.exists(), f"System prompt missing: {prompt_path}"
        assert prompt_path.is_file(), f"System prompt path is not a file: {prompt_path}"


class TestConfigsValidYAML:
    """Test that all YAML files parse without errors."""
    
    @pytest.mark.parametrize("account,instance", TEST_INSTANCES)
    def test_config_parses(self, account, instance):
        """Verify each config.yaml parses as valid YAML."""
        config_path = CONFIG_BASE / account / instance / "config.yaml"
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data is not None, f"Config file is empty: {config_path}"
        assert isinstance(data, dict), f"Config must be a dictionary: {config_path}"


class TestConfigsRequiredFields:
    """Test that all required fields are present in each config."""
    
    REQUIRED_FIELDS = [
        "agent_type",
        "account",
        "instance_name",
        "model_settings",
        "tools",
        "context_management",
    ]
    
    REQUIRED_MODEL_SETTINGS = ["model", "temperature", "max_tokens"]
    REQUIRED_CONTEXT_MANAGEMENT = ["history_limit"]
    
    @pytest.mark.parametrize("account,instance", TEST_INSTANCES)
    def test_top_level_fields(self, account, instance):
        """Verify all required top-level fields are present."""
        config_path = CONFIG_BASE / account / instance / "config.yaml"
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        for field in self.REQUIRED_FIELDS:
            assert field in data, f"Missing required field '{field}' in {config_path}"
    
    @pytest.mark.parametrize("account,instance", TEST_INSTANCES)
    def test_model_settings_fields(self, account, instance):
        """Verify required model_settings fields are present."""
        config_path = CONFIG_BASE / account / instance / "config.yaml"
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        model_settings = data.get("model_settings", {})
        for field in self.REQUIRED_MODEL_SETTINGS:
            assert field in model_settings, f"Missing model_settings.{field} in {config_path}"
    
    @pytest.mark.parametrize("account,instance", TEST_INSTANCES)
    def test_context_management_fields(self, account, instance):
        """Verify required context_management fields are present."""
        config_path = CONFIG_BASE / account / instance / "config.yaml"
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        context_mgmt = data.get("context_management", {})
        for field in self.REQUIRED_CONTEXT_MANAGEMENT:
            assert field in context_mgmt, f"Missing context_management.{field} in {config_path}"


class TestInstanceNamesUnique:
    """Test that each instance has unique account/instance_name combination."""
    
    def test_unique_combinations(self):
        """Verify no duplicate account/instance_name combinations."""
        combinations = set()
        
        for account, instance in TEST_INSTANCES:
            config_path = CONFIG_BASE / account / instance / "config.yaml"
            
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            config_account = data.get("account")
            config_instance = data.get("instance_name")
            
            combination = (config_account, config_instance)
            
            assert combination not in combinations, \
                f"Duplicate combination: account={config_account}, instance={config_instance}"
            
            combinations.add(combination)
    
    def test_account_matches_path(self):
        """Verify config.account matches directory structure."""
        for account, instance in TEST_INSTANCES:
            config_path = CONFIG_BASE / account / instance / "config.yaml"
            
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            config_account = data.get("account")
            assert config_account == account, \
                f"Config account '{config_account}' doesn't match path account '{account}' in {config_path}"
    
    def test_instance_name_matches_path(self):
        """Verify config.instance_name matches directory structure."""
        for account, instance in TEST_INSTANCES:
            config_path = CONFIG_BASE / account / instance / "config.yaml"
            
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            config_instance = data.get("instance_name")
            assert config_instance == instance, \
                f"Config instance_name '{config_instance}' doesn't match path instance '{instance}' in {config_path}"


class TestDifferentiatedConfigs:
    """Test that acme_chat1 has differentiated settings for testing."""
    
    def test_acme_temperature_different(self):
        """Verify acme_chat1 has different temperature than default instances."""
        # Load default_account/simple_chat1
        default_path = CONFIG_BASE / "default_account" / "simple_chat1" / "config.yaml"
        with open(default_path, 'r') as f:
            default_data = yaml.safe_load(f)
        default_temp = default_data["model_settings"]["temperature"]
        
        # Load acme/acme_chat1
        acme_path = CONFIG_BASE / "acme" / "acme_chat1" / "config.yaml"
        with open(acme_path, 'r') as f:
            acme_data = yaml.safe_load(f)
        acme_temp = acme_data["model_settings"]["temperature"]
        
        assert acme_temp != default_temp, \
            f"Acme temperature ({acme_temp}) should differ from default ({default_temp}) for testing"
    
    def test_acme_history_limit_different(self):
        """Verify acme_chat1 has different history_limit than default instances."""
        # Load default_account/simple_chat1
        default_path = CONFIG_BASE / "default_account" / "simple_chat1" / "config.yaml"
        with open(default_path, 'r') as f:
            default_data = yaml.safe_load(f)
        default_history = default_data["context_management"]["history_limit"]
        
        # Load acme/acme_chat1
        acme_path = CONFIG_BASE / "acme" / "acme_chat1" / "config.yaml"
        with open(acme_path, 'r') as f:
            acme_data = yaml.safe_load(f)
        acme_history = acme_data["context_management"]["history_limit"]
        
        assert acme_history != default_history, \
            f"Acme history_limit ({acme_history}) should differ from default ({default_history}) for testing"
    
    def test_acme_namespace_different(self):
        """Verify acme_chat1 has account-specific Pinecone namespace."""
        acme_path = CONFIG_BASE / "acme" / "acme_chat1" / "config.yaml"
        with open(acme_path, 'r') as f:
            acme_data = yaml.safe_load(f)
        
        namespace = acme_data["tools"]["vector_search"]["pinecone"]["namespace"]
        assert namespace == "acme", \
            f"Acme should have account-specific namespace 'acme', got '{namespace}'"


class TestBackwardCompatibility:
    """Test that old config path still exists for backward compatibility."""
    
    def test_legacy_simple_chat_exists(self):
        """Verify legacy simple_chat/config.yaml still exists."""
        legacy_path = CONFIG_BASE / "simple_chat" / "config.yaml"
        assert legacy_path.exists(), \
            "Legacy config path simple_chat/config.yaml should exist for backward compatibility"
    
    def test_legacy_system_prompt_exists(self):
        """Verify legacy simple_chat/system_prompt.md still exists."""
        legacy_path = CONFIG_BASE / "simple_chat" / "system_prompt.md"
        assert legacy_path.exists(), \
            "Legacy system_prompt.md should exist for backward compatibility"
