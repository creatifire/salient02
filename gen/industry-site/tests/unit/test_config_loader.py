"""
Unit tests for ConfigLoader class.
"""

import pytest
from pathlib import Path
from lib.config.config_loader import ConfigLoader
from lib.errors.exceptions import ConfigError, ConfigValidationError


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("""
OPENROUTER_API_KEY=test-api-key-123
EXA_API_KEY=test-exa-key-456
TEST_VALUE=hello-world
""")
    return env_file


@pytest.fixture
def valid_config_file(tmp_path):
    """Create a valid test configuration file."""
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text("""
company:
  name: Test Company
  industry: Testing
  description: A test company
  tagline: Test tagline
  website: https://test.example.com

llm:
  api_key: ${OPENROUTER_API_KEY}
  base_url: https://openrouter.ai/api/v1
  models:
    tool_calling: anthropic/claude-sonnet-4.5
    no_tools: anthropic/claude-haiku-4.5
  timeout: 60
  max_retries: 3

research:
  exa_api_key: ${EXA_API_KEY}
  jina_api_key: ${TEST_VALUE}
  companies_to_research: 10
  products_per_company: 5

generation:
  product_count: 100
  category_count: 10
  product_relationships:
    min: 0
    max: 3
  entries_per_directory: 25
""")
    return config_file


@pytest.fixture
def invalid_config_file(tmp_path):
    """Create an invalid configuration file (missing required fields)."""
    config_file = tmp_path / "invalid-config.yaml"
    config_file.write_text("""
company:
  name: Test Company

llm:
  api_key: test-key
""")
    return config_file


@pytest.mark.unit
def test_loads_valid_config(valid_config_file, temp_env_file):
    """Test that ConfigLoader loads valid config successfully."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    config = loader.load()
    
    # Verify config structure
    assert 'company' in config
    assert 'llm' in config
    assert 'research' in config
    assert 'generation' in config
    
    # Verify company info
    assert config['company']['name'] == 'Test Company'
    assert config['company']['industry'] == 'Testing'


@pytest.mark.unit
def test_env_var_substitution(valid_config_file, temp_env_file):
    """Test that environment variables are substituted correctly."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    config = loader.load()
    
    # Verify environment variables were substituted
    assert config['llm']['api_key'] == 'test-api-key-123'
    assert config['research']['exa_api_key'] == 'test-exa-key-456'
    
    # Original template should not be present
    assert '${OPENROUTER_API_KEY}' not in str(config)
    assert '${EXA_API_KEY}' not in str(config)


@pytest.mark.unit
def test_env_var_substitution_missing_var(tmp_path):
    """Test that missing environment variables result in empty strings."""
    # Create config with undefined variable
    config_file = tmp_path / "test-config.yaml"
    config_file.write_text("""
company:
  name: Test Company
  industry: Testing
  description: A test company
  tagline: Test tagline
  website: https://test.example.com

llm:
  api_key: ${UNDEFINED_VAR_12345}
  base_url: https://openrouter.ai/api/v1
  models:
    tool_calling: anthropic/claude-sonnet-4.5
    no_tools: anthropic/claude-haiku-4.5
  timeout: 60
  max_retries: 3

research:
  exa_api_key: test-key
  jina_api_key: test-key
  companies_to_research: 10
  products_per_company: 5

generation:
  product_count: 100
  category_count: 10
  product_relationships:
    min: 0
    max: 3
  entries_per_directory: 25
""")
    
    # Create env file without the variable
    env_file = tmp_path / "partial.env"
    env_file.write_text("SOME_OTHER_KEY=value\n")
    
    loader = ConfigLoader(config_file, env_file=env_file)
    config = loader.load()
    
    # Missing env var should be left as template string
    assert config['llm']['api_key'] == '${UNDEFINED_VAR_12345}'


@pytest.mark.unit
def test_missing_required_field_raises_error(invalid_config_file, temp_env_file):
    """Test that validation errors are caught for missing required fields."""
    loader = ConfigLoader(invalid_config_file, env_file=temp_env_file)
    
    with pytest.raises(ConfigValidationError) as exc_info:
        loader.load()
    
    # Should mention missing fields
    error_msg = str(exc_info.value)
    assert 'required' in error_msg.lower() or 'missing' in error_msg.lower()


@pytest.mark.unit
def test_missing_config_file_raises_error(tmp_path, temp_env_file):
    """Test that missing config file raises ConfigError."""
    nonexistent_file = tmp_path / "nonexistent.yaml"
    loader = ConfigLoader(nonexistent_file, env_file=temp_env_file)
    
    with pytest.raises((ConfigError, FileNotFoundError)) as exc_info:
        loader.load()
    
    # Should mention file not found
    error_msg = str(exc_info.value).lower()
    assert 'not found' in error_msg or 'no such file' in error_msg


@pytest.mark.unit
def test_dot_notation_access(valid_config_file, temp_env_file):
    """Test that dot notation access works."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    loader.load()
    
    # Test dot notation access
    assert loader.get('company.name') == 'Test Company'
    assert loader.get('company.industry') == 'Testing'
    assert loader.get('llm.models.tool_calling') == 'anthropic/claude-sonnet-4.5'
    assert loader.get('llm.timeout') == 60
    assert loader.get('generation.product_count') == 100


@pytest.mark.unit
def test_dot_notation_default_value(valid_config_file, temp_env_file):
    """Test that dot notation returns default for missing keys."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    loader.load()
    
    # Test default values for nonexistent keys
    assert loader.get('nonexistent.key') is None
    assert loader.get('nonexistent.key', 'default') == 'default'
    assert loader.get('company.nonexistent', 42) == 42


@pytest.mark.unit
def test_property_accessors(valid_config_file, temp_env_file):
    """Test that property methods work."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    loader.load()
    
    # Test company property
    company = loader.company
    assert company is not None
    assert company['name'] == 'Test Company'
    assert company['industry'] == 'Testing'
    
    # Test llm property
    llm = loader.llm
    assert llm is not None
    assert llm['base_url'] == 'https://openrouter.ai/api/v1'
    assert llm['models']['tool_calling'] == 'anthropic/claude-sonnet-4.5'
    
    # Test generation property
    generation = loader.generation
    assert generation is not None
    assert generation['product_count'] == 100
    assert generation['category_count'] == 10


@pytest.mark.unit
def test_dictionary_style_access(valid_config_file, temp_env_file):
    """Test that dictionary-style access works after loading."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    config = loader.load()
    
    # Access via returned config dict
    assert config['company']['name'] == 'Test Company'
    assert config['llm']['api_key'] == 'test-api-key-123'


@pytest.mark.unit
def test_access_before_load_raises_error(valid_config_file, temp_env_file):
    """Test that accessing config before load raises error."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    
    # Should raise error when accessing before load
    with pytest.raises((ConfigError, RuntimeError)) as exc_info:
        _ = loader.company
    
    error_msg = str(exc_info.value).lower()
    assert 'not loaded' in error_msg or 'load' in error_msg


@pytest.mark.unit
def test_config_immutable_after_load(valid_config_file, temp_env_file):
    """Test that config values are preserved correctly."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    config1 = loader.load()
    
    # Get the same values again
    company_name_1 = loader.get('company.name')
    
    # Values should be consistent
    assert company_name_1 == 'Test Company'
    assert loader.get('company.name') == company_name_1


@pytest.mark.unit
def test_numeric_validation(valid_config_file, temp_env_file):
    """Test that numeric values are validated correctly."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    config = loader.load()
    
    # Verify numeric values are in expected ranges
    assert config['llm']['timeout'] > 0
    assert config['llm']['max_retries'] > 0
    assert config['generation']['product_count'] > 0
    assert config['generation']['category_count'] > 0
    assert config['research']['companies_to_research'] > 0


@pytest.mark.unit
def test_load_with_default_env_file(valid_config_file, temp_env_file):
    """Test loading config with default .env file path."""
    # This tests the automatic .env detection
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    config = loader.load()
    
    assert config is not None
    assert 'company' in config


@pytest.mark.unit
def test_reload_config(valid_config_file, temp_env_file):
    """Test that config can be reloaded."""
    loader = ConfigLoader(valid_config_file, env_file=temp_env_file)
    
    # First load
    config1 = loader.load()
    name1 = config1['company']['name']
    
    # Load again (should work without error)
    config2 = loader.load()
    name2 = config2['company']['name']
    
    # Values should be the same
    assert name1 == name2 == 'Test Company'
