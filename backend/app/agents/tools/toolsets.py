"""
Pydantic AI toolset wrappers for existing agent tools.

Wraps existing tool functions (directory_tools.py, vector_tools.py) using
Pydantic AI's native FunctionToolset for multi-tool support.
"""

from pydantic_ai.toolsets import FunctionToolset
from .directory_tools import search_directory
from .vector_tools import vector_search
import logging

logger = logging.getLogger(__name__)


# Directory toolset - wraps existing search_directory function
directory_toolset = FunctionToolset(tools=[search_directory])

# Vector search toolset - wraps existing vector_search function
vector_toolset = FunctionToolset(tools=[vector_search])


def get_enabled_toolsets(agent_config: dict) -> list[FunctionToolset]:
    """
    Get list of enabled toolsets based on agent configuration.
    
    Args:
        agent_config: Agent configuration dict from config.yaml
        
    Returns:
        List of enabled FunctionToolset instances
        
    Example:
        config = {"tools": {"directory": {"enabled": True}, "vector_search": {"enabled": False}}}
        toolsets = get_enabled_toolsets(config)
        # Returns: [directory_toolset]
    """
    toolsets = []
    tools_config = agent_config.get("tools", {})
    
    # Check directory tool
    if tools_config.get("directory", {}).get("enabled", False):
        toolsets.append(directory_toolset)
        logger.info("✅ Directory toolset enabled")
    
    # Check vector search tool
    if tools_config.get("vector_search", {}).get("enabled", False):
        toolsets.append(vector_toolset)
        logger.info("✅ Vector search toolset enabled")
    
    if not toolsets:
        logger.info("No toolsets enabled (base agent only)")
    
    return toolsets

