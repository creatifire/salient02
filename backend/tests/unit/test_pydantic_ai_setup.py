"""
Unit tests for CHUNK 0005-001-001-01 - Pydantic AI Dependencies
Tests the installation and compatibility of pydantic-ai with the project.
"""
import pytest
import sys


@pytest.mark.unit
def test_pydantic_ai_import():
    """Test that pydantic-ai imports successfully with correct version."""
    try:
        import pydantic_ai
        # Check if version meets minimum requirement
        version_parts = pydantic_ai.__version__.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        assert major > 0 or (major == 0 and minor >= 8), f"pydantic-ai version {pydantic_ai.__version__} is below minimum 0.8.1"
    except ImportError as e:
        pytest.fail(f"pydantic-ai import failed: {e}")


@pytest.mark.unit
def test_fastapi_compatibility():
    """Test that pydantic-ai works alongside FastAPI without conflicts."""
    try:
        from pydantic_ai import Agent
        from fastapi import FastAPI
        
        # Should be able to create both without conflicts
        app = FastAPI()
        agent = Agent('test')  # Use 'test' for TestModel
        
        assert agent is not None
        assert app is not None
        assert hasattr(agent, 'run') or hasattr(agent, '__call__'), "Agent should have callable interface"
        
    except Exception as e:
        pytest.fail(f"FastAPI compatibility issue: {e}")


@pytest.mark.unit
def test_core_dependencies_available():
    """Test that all required core dependencies are available."""
    required_packages = ['pydantic', 'fastapi', 'asyncio']
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            pytest.fail(f"Required dependency {package} not available")


@pytest.mark.unit
def test_version_constraints():
    """Test that dependency versions meet minimum requirements."""
    try:
        import pydantic
        import fastapi
        
        # Check pydantic version (should be >= 2.0.0)
        pydantic_version = pydantic.__version__.split('.')
        pydantic_major = int(pydantic_version[0])
        assert pydantic_major >= 2, f"pydantic version {pydantic.__version__} is below minimum 2.0.0"
        
        # Check fastapi version (should be >= 0.100.0)  
        fastapi_version = fastapi.__version__.split('.')
        fastapi_major, fastapi_minor = int(fastapi_version[0]), int(fastapi_version[1])
        assert fastapi_major > 0 or (fastapi_major == 0 and fastapi_minor >= 100), f"fastapi version {fastapi.__version__} is below minimum 0.100.0"
        
    except Exception as e:
        pytest.fail(f"Version constraint check failed: {e}")


@pytest.mark.unit
def test_python_version_compatibility():
    """Test that Python version is compatible."""
    python_version = sys.version_info
    assert python_version >= (3, 8), f"Python {python_version.major}.{python_version.minor} is below minimum 3.8"
