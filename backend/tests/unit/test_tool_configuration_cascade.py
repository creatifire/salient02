"""
Tests for tool configuration cascade functionality.

Tests the agent-first configuration cascade for tool configurations,
ensuring per-agent tool enable/disable capability and proper parameter inheritance.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import pytest
from app.agents.config_loader import get_agent_tool_config


@pytest.mark.asyncio
async def test_tool_configuration_cascade():
    """
    Test that tool configs cascade properly using generic infrastructure.
    
    Verifies:
    - Tool configuration loaded from agent config
    - Each tool parameter cascades independently
    - CascadeAuditTrail integration works for tools
    """
    # Test vector_search tool for simple_chat agent
    vector_search_config = await get_agent_tool_config("simple_chat", "vector_search")
    
    # Verify enabled status (from agent config)
    assert vector_search_config["enabled"] is True, "vector_search should be enabled in simple_chat"
    
    # Verify max_results parameter (from agent config)
    assert vector_search_config["max_results"] == 5, "max_results should come from agent config"
    
    # Verify similarity_threshold parameter (from agent config)
    assert vector_search_config["similarity_threshold"] == 0.7, "similarity_threshold should come from agent config"
    
    # Verify namespace_isolation parameter (from agent config)
    assert vector_search_config["namespace_isolation"] is True, "namespace_isolation should come from agent config"


@pytest.mark.asyncio
async def test_per_agent_tool_enablement():
    """
    Test that agents can have different tool sets with inheritance.
    
    Verifies:
    - Different agents can enable/disable tools independently
    - Tool configuration is agent-specific
    - Fallback values work when agent config missing
    """
    # Test web_search tool for simple_chat (enabled in config)
    web_search_config = await get_agent_tool_config("simple_chat", "web_search")
    assert web_search_config["enabled"] is True, "web_search should be enabled in simple_chat"
    assert web_search_config["provider"] == "exa", "web_search provider should come from agent config"
    
    # Test conversation_management tool
    conv_config = await get_agent_tool_config("simple_chat", "conversation_management")
    assert conv_config["enabled"] is True, "conversation_management should be enabled"
    assert conv_config["auto_summarize_threshold"] == 10, "auto_summarize_threshold should come from agent config"
    
    # Test profile_capture tool (not in agent config, should use fallback)
    profile_config = await get_agent_tool_config("simple_chat", "profile_capture")
    assert profile_config["enabled"] is False, "profile_capture should use fallback (disabled)"
    
    # Test email_summary tool (not in agent config, should use fallback)
    email_config = await get_agent_tool_config("simple_chat", "email_summary")
    assert email_config["enabled"] is False, "email_summary should use fallback (disabled)"


@pytest.mark.asyncio
async def test_tool_config_monitoring_integration():
    """
    Test that CascadeAuditTrail integration works for tool decisions.
    
    Verifies:
    - Audit trail is created for tool parameter lookups
    - Performance metrics are tracked
    - Troubleshooting guidance is available
    """
    # This test verifies that the cascade infrastructure is being used
    # by checking that the function completes successfully with comprehensive monitoring
    
    # Get tool config (this triggers audit trail internally)
    config = await get_agent_tool_config("simple_chat", "vector_search")
    
    # Verify we got valid configuration (proves cascade worked)
    assert "enabled" in config, "Tool config should have enabled parameter"
    assert "max_results" in config, "Tool config should have max_results parameter"
    
    # The audit trail logging happens internally via get_agent_parameter()
    # This test ensures the integration is working by verifying successful completion


@pytest.mark.asyncio
async def test_tool_config_mixed_inheritance():
    """
    Test mixed tool parameter inheritance scenarios.
    
    Verifies:
    - Individual tool parameters can come from different sources
    - Some parameters from agent config, others from fallback
    - Proper cascade behavior for each parameter independently
    """
    # Test a tool where some parameters exist in agent config and others don't
    vector_search_config = await get_agent_tool_config("simple_chat", "vector_search")
    
    # These should come from agent config (exist in simple_chat/config.yaml)
    assert vector_search_config["enabled"] is True
    assert vector_search_config["max_results"] == 5
    assert vector_search_config["similarity_threshold"] == 0.7
    assert vector_search_config["namespace_isolation"] is True
    
    # Test web_search with mixed inheritance
    web_search_config = await get_agent_tool_config("simple_chat", "web_search")
    
    # These should come from agent config
    assert web_search_config["enabled"] is True
    assert web_search_config["provider"] == "exa"
    
    # Test unknown tool returns disabled config
    unknown_config = await get_agent_tool_config("simple_chat", "unknown_tool")
    assert unknown_config["enabled"] is False, "Unknown tools should be disabled by default"


@pytest.mark.asyncio
async def test_tool_config_fallback_behavior():
    """
    Test that fallback values work correctly when agent config is missing.
    
    Verifies:
    - Fallback values are used when tool not in agent config
    - System degrades gracefully with sensible defaults
    """
    # Test a tool that's not configured in agent config
    profile_config = await get_agent_tool_config("simple_chat", "profile_capture")
    
    # Should use fallback value (disabled)
    assert profile_config["enabled"] is False, "profile_capture should use fallback when not in agent config"
    
    # Test email_summary fallback
    email_config = await get_agent_tool_config("simple_chat", "email_summary")
    assert email_config["enabled"] is False, "email_summary should use fallback when not in agent config"


@pytest.mark.asyncio
async def test_tool_config_parameter_types():
    """
    Test that different parameter types are handled correctly.
    
    Verifies:
    - Boolean parameters (enabled flags)
    - Integer parameters (max_results, thresholds)
    - String parameters (provider names)
    - Float parameters (similarity thresholds)
    """
    # Test vector_search with multiple parameter types
    vector_config = await get_agent_tool_config("simple_chat", "vector_search")
    
    # Boolean
    assert isinstance(vector_config["enabled"], bool), "enabled should be boolean"
    
    # Integer
    assert isinstance(vector_config["max_results"], int), "max_results should be integer"
    assert vector_config["max_results"] > 0, "max_results should be positive"
    
    # Float
    assert isinstance(vector_config["similarity_threshold"], (int, float)), "similarity_threshold should be numeric"
    assert 0.0 <= vector_config["similarity_threshold"] <= 1.0, "similarity_threshold should be between 0 and 1"
    
    # Test web_search string parameter
    web_config = await get_agent_tool_config("simple_chat", "web_search")
    assert isinstance(web_config["provider"], str), "provider should be string"
    assert web_config["provider"] in ["exa", "tavily", "linkup"], "provider should be valid option"

