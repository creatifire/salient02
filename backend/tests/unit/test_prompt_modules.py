import pytest
from app.agents.tools.prompt_modules import (
    load_prompt_module,
    load_modules_for_agent
)


def test_load_system_module():
    """Test loading system-level module."""
    content = load_prompt_module("directory_keyword_hints")
    assert content is not None
    assert len(content) > 0
    assert "Directory Selection Hints" in content


def test_load_nonexistent_module():
    """Test graceful handling of missing module."""
    content = load_prompt_module("does_not_exist")
    assert content is None


def test_load_modules_for_agent_enabled():
    """Test loading multiple modules via agent config."""
    config = {
        "prompting": {
            "modules": {
                "enabled": True,
                "selected": ["directory_keyword_hints"]
            }
        }
    }
    combined = load_modules_for_agent(config)
    assert combined != ""
    assert "Directory Selection Hints" in combined


def test_load_modules_for_agent_disabled():
    """Test that disabled modules return empty string."""
    config = {
        "prompting": {
            "modules": {
                "enabled": False,
                "selected": ["directory_keyword_hints"]
            }
        }
    }
    combined = load_modules_for_agent(config)
    assert combined == ""


def test_load_modules_for_agent_none_selected():
    """Test that no selected modules return empty string."""
    config = {
        "prompting": {
            "modules": {
                "enabled": True,
                "selected": []
            }
        }
    }
    combined = load_modules_for_agent(config)
    assert combined == ""


def test_load_modules_for_agent_missing_config():
    """Test that missing config section returns empty string."""
    config = {}
    combined = load_modules_for_agent(config)
    assert combined == ""

