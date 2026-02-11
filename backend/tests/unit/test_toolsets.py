import pytest
from app.agents.tools.toolsets import (
    directory_toolset, 
    vector_toolset, 
    get_enabled_toolsets
)


def test_toolsets_exist():
    """Verify toolset instances are created."""
    assert directory_toolset is not None
    assert vector_toolset is not None


def test_get_enabled_toolsets_all():
    """Test all toolsets enabled."""
    config = {
        "tools": {
            "directory": {"enabled": True},
            "vector_search": {"enabled": True}
        }
    }
    toolsets = get_enabled_toolsets(config)
    assert len(toolsets) == 2


def test_get_enabled_toolsets_directory_only():
    """Test directory toolset only."""
    config = {"tools": {"directory": {"enabled": True}}}
    toolsets = get_enabled_toolsets(config)
    assert len(toolsets) == 1


def test_get_enabled_toolsets_none():
    """Test no toolsets enabled."""
    config = {"tools": {}}
    toolsets = get_enabled_toolsets(config)
    assert len(toolsets) == 0

