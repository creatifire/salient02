# Automated Testing Conventions

Testing standards and conventions for the Industry Site Generator project.

## Testing Framework

**pytest** - Python's standard testing framework

```bash
pip install pytest pytest-cov pytest-mock
```

## Test Organization

```
gen/industry-site/
├── lib/                           # Source code
│   ├── config/
│   ├── llm/
│   └── ...
├── tests/                         # All tests
│   ├── conftest.py               # Shared fixtures
│   ├── unit/                     # Fast, isolated tests
│   │   ├── test_config_loader.py
│   │   ├── test_state_manager.py
│   │   └── ...
│   ├── integration/              # Multi-module tests
│   │   ├── test_config_and_state.py
│   │   └── ...
│   ├── functional/               # End-to-end workflow tests
│   │   ├── test_script_01_init.py
│   │   └── ...
│   └── fixtures/                 # Test data
│       ├── valid-config.yaml
│       └── sample-data.json
└── pytest.ini                    # pytest configuration
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions/classes in isolation
- Fast execution (milliseconds)
- No external dependencies (mock APIs, file system)
- High coverage of edge cases

### Integration Tests (`tests/integration/`)
- Test multiple modules working together
- Use real file system (temp directories)
- May use mocked external APIs
- Moderate execution time

### Functional Tests (`tests/functional/`)
- Test complete workflows (scripts 01-12)
- End-to-end scenarios
- May use actual APIs with test keys
- Slower execution (mark with `@pytest.mark.slow`)

## Naming Conventions

### Test Files
- Pattern: `test_<module_name>.py`
- Examples: `test_config_loader.py`, `test_llm_client.py`

### Test Classes (Optional)
- Pattern: `Test<ClassName>`
- Use for grouping related tests
- Example: `class TestConfigLoader:`

### Test Functions
- Pattern: `test_<what_is_being_tested>`
- Be descriptive and specific
- Examples:
  - `test_loads_valid_config()`
  - `test_env_var_substitution()`
  - `test_missing_required_field_raises_error()`

## Fixture Conventions

### Common Fixtures (`conftest.py`)

```python
import pytest
from pathlib import Path
import tempfile
import yaml

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def valid_config_path(temp_dir):
    """Create valid config file for testing."""
    config = {
        'company': {'name': 'Test', 'industry': 'test', 'description': 'test'},
        'llm': {'api_key': 'test-key', 'models': {'tool_calling': 'm1', 'no_tools': 'm2'}},
        'generation': {'product_count': 100, 'category_count': 10}
    }
    config_path = temp_dir / 'config.yaml'
    config_path.write_text(yaml.safe_dump(config))
    return config_path

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-openrouter-key')
    monkeypatch.setenv('EXA_API_KEY', 'test-exa-key')
    monkeypatch.setenv('JINA_API_KEY', 'test-jina-key')
```

## Test Structure Pattern

```python
def test_feature_name(fixtures):
    """Brief description of what is being tested."""
    # Arrange - Set up test data
    input_data = {'key': 'value'}
    
    # Act - Execute the code under test
    result = function_under_test(input_data)
    
    # Assert - Verify the results
    assert result == expected_value
    assert 'key' in result
```

## Assertion Conventions

### Use pytest's natural assertions

```python
# Good - Clear and readable
assert config['company']['name'] == 'Test Company'
assert 'llm' in config
assert len(products) > 0

# Avoid - unittest style (not needed with pytest)
self.assertEqual(config['company']['name'], 'Test Company')
```

### Exception Testing

```python
import pytest
from lib.errors import ConfigValidationError

def test_invalid_config_raises_error():
    """Test that invalid config raises ConfigValidationError."""
    loader = ConfigLoader('invalid.yaml')
    
    with pytest.raises(ConfigValidationError) as exc_info:
        loader.load()
    
    # Optionally verify error message
    assert 'Missing required field' in str(exc_info.value)
```

## Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple inputs:

```python
@pytest.mark.parametrize("key_path,expected", [
    ('company.name', 'Test Company'),
    ('llm.models.tool_calling', 'model-1'),
    ('nonexistent.key', None),
])
def test_dot_notation_access(valid_config_path, key_path, expected):
    """Test dot notation access with various keys."""
    loader = ConfigLoader(valid_config_path)
    loader.load()
    
    assert loader.get(key_path) == expected
```

## Mocking External Dependencies

### Mock API Calls

```python
def test_llm_client_api_call(mocker):
    """Test LLM client makes correct API call."""
    # Mock the OpenAI client
    mock_openai = mocker.patch('lib.llm.client.OpenAI')
    mock_response = {'choices': [{'message': {'content': 'test response'}}]}
    mock_openai.return_value.chat.completions.create.return_value = mock_response
    
    # Test
    client = LLMClient(api_key='test-key')
    response = client.generate_text('test prompt')
    
    assert response == 'test response'
```

### Mock File Operations

```python
def test_read_research_files(mocker, temp_dir):
    """Test reading research files."""
    # Create test files
    research_file = temp_dir / 'research.md'
    research_file.write_text('# Test Research')
    
    # Test
    content = read_research_file(research_file)
    
    assert '# Test Research' in content
```

## Test Markers

Define markers in `pytest.ini`:

```ini
[pytest]
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (multiple modules)
    functional: Functional/E2E tests (full workflows)
    slow: Tests that take significant time
    llm: Tests requiring LLM API (expensive)
```

Use markers in tests:

```python
@pytest.mark.unit
def test_config_validation():
    """Test config validation logic."""
    pass

@pytest.mark.integration
def test_config_and_state():
    """Test ConfigLoader and StateManager together."""
    pass

@pytest.mark.slow
@pytest.mark.llm
def test_full_generation_workflow():
    """Test complete site generation (expensive)."""
    pass
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific category
pytest tests/unit
pytest -m unit

# Run with coverage
pytest --cov=lib --cov-report=html

# Run specific test
pytest tests/unit/test_config_loader.py::test_loads_valid_config

# Run tests matching pattern
pytest -k "config"

# Skip slow tests
pytest -m "not slow"

# Verbose output with print statements
pytest -v -s

# Parallel execution
pytest -n auto
```

## Coverage Goals

- **Minimum**: 80% code coverage
- **Target**: 90%+ for critical modules (config, validation, generation)
- **Required**: 100% for error handling paths

Check coverage:
```bash
pytest --cov=lib --cov-report=term-missing
```

## pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts = 
    -v                          # Verbose output
    --strict-markers           # Strict marker usage
    --cov=lib                  # Coverage for lib/ folder
    --cov-report=html          # HTML coverage report
    --cov-report=term-missing  # Show missing lines

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (multiple modules)
    functional: Functional/E2E tests (full workflows)
    slow: Tests that take significant time
    llm: Tests requiring LLM API (expensive)
```

## Best Practices

### DO

- Write tests before or alongside implementation
- Keep tests simple and focused (one concept per test)
- Use descriptive test names that explain what is being tested
- Use fixtures for common setup
- Mock external dependencies (APIs, file system when appropriate)
- Test both success and failure cases
- Test edge cases and boundaries
- Keep tests fast (mock slow operations)
- Use temp directories for file operations

### DON'T

- Test implementation details (test behavior, not internals)
- Write tests that depend on other tests
- Use hard-coded paths (use fixtures and temp directories)
- Leave debug print statements in tests
- Skip writing tests for "simple" functions
- Test third-party library code
- Make real API calls in unit tests
- Commit test artifacts (use temp directories)

## Example Test File

```python
"""Tests for ConfigLoader class."""

import pytest
from pathlib import Path
import yaml
from lib.config import ConfigLoader
from lib.errors import ConfigValidationError


class TestConfigLoader:
    """Test suite for ConfigLoader."""
    
    def test_loads_valid_config(self, valid_config_path):
        """Test loading a valid configuration."""
        loader = ConfigLoader(valid_config_path)
        config = loader.load()
        
        assert config['company']['name'] == 'Test Company'
        assert 'llm' in config
        assert 'generation' in config
    
    def test_env_var_substitution(self, temp_dir, mock_env_vars):
        """Test environment variable substitution."""
        config_data = """
company:
  name: Test
  industry: test
  description: test
llm:
  api_key: ${OPENROUTER_API_KEY}
  models:
    tool_calling: model1
    no_tools: model2
generation:
  product_count: 10
  category_count: 5
"""
        config_path = temp_dir / 'config.yaml'
        config_path.write_text(config_data)
        
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        assert config['llm']['api_key'] == 'test-openrouter-key'
    
    def test_missing_required_field_raises_error(self, temp_dir):
        """Test that missing required field raises ConfigValidationError."""
        config_data = """
company:
  name: Test
llm:
  api_key: test
  models:
    tool_calling: model1
    no_tools: model2
generation:
  product_count: 10
"""
        config_path = temp_dir / 'invalid.yaml'
        config_path.write_text(config_data)
        
        loader = ConfigLoader(config_path)
        
        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load()
        
        error_msg = str(exc_info.value)
        assert 'industry' in error_msg or 'description' in error_msg
    
    @pytest.mark.parametrize("key_path,expected", [
        ('company.name', 'Test Company'),
        ('llm.api_key', 'test-key'),
        ('nonexistent.key', None),
    ])
    def test_dot_notation_access(self, valid_config_path, key_path, expected):
        """Test dot notation access with various keys."""
        loader = ConfigLoader(valid_config_path)
        loader.load()
        
        result = loader.get(key_path)
        assert result == expected
```

## Integration with Development Workflow

### Pre-commit Hook
Run fast tests before commits:
```bash
pytest tests/unit -q
```

### CI/CD Pipeline
- Run all tests on push
- Fail build if coverage drops below threshold
- Generate and archive coverage reports

### Development Cycle
1. Write/update test
2. Run test (should fail - red)
3. Implement feature
4. Run test (should pass - green)
5. Refactor if needed
6. Verify test still passes

## References

- pytest documentation: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- pytest-mock: https://pytest-mock.readthedocs.io/
