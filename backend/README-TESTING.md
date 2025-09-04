# Testing Setup

## Quick Start

1. **Install development dependencies:**
   ```bash
   pip install -r ../requirements-dev.txt
   ```

2. **Run tests:**
   ```bash
   # Run all unit tests
   pytest tests/unit/ -v
   
   # Run with coverage
   pytest tests/ --cov=app --cov-report=html
   
   # Use the test runner script
   ./run_tests.sh
   ```

## Development Dependencies

The `requirements-dev.txt` file includes:
- **pytest** - Main testing framework
- **pytest-asyncio** - Async test support  
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities

## Test Structure

```
backend/tests/
├── unit/                           # Unit tests (fast, no external deps)
│   ├── test_pydantic_ai_setup.py  # CHUNK 0005-001-001-01 tests
│   ├── test_agent_base_structure.py # CHUNK 0005-001-001-02 tests  
│   └── test_agent_config_loader.py # CHUNK 0005-001-001-03 tests
├── integration/                    # Integration tests (real dependencies)
├── fixtures/                      # Shared test data
│   └── sample_data.py
└── conftest.py                    # Pytest configuration & fixtures
```

## Test Markers

- `@pytest.mark.unit` - Unit tests (fast)
- `@pytest.mark.integration` - Integration tests (slower)
- `@pytest.mark.slow` - Long-running tests

## Coverage Target

- **Unit Tests**: 70% code coverage minimum
- **Integration Tests**: All critical API endpoints
- **Coverage Report**: Available at `htmlcov/index.html` after running tests with `--cov`
