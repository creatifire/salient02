"""
Agent-Specific Pinecone Configuration
Loads per-agent Pinecone settings from agent config YAML files.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pinecone import Pinecone


logger = logging.getLogger(__name__)


@dataclass
class AgentPineconeConfig:
    """Per-agent Pinecone configuration"""
    api_key: str
    index_name: str
    index_host: str  # Auto-discovered or explicit
    namespace: str
    embedding_model: str
    dimensions: int


def load_agent_pinecone_config(
    instance_config: Dict[str, Any]
) -> Optional[AgentPineconeConfig]:
    """
    Load Pinecone config from agent's config.yaml.
    Returns None if vector_search is disabled or missing pinecone settings.
    
    Configuration cascade: agent config → app.yaml → code defaults
    
    Args:
        instance_config: Agent instance configuration dictionary from YAML
        
    Returns:
        AgentPineconeConfig if valid, None if disabled or invalid
    """
    vector_config = instance_config.get("tools", {}).get("vector_search", {})
    
    # Check if vector search is enabled
    if not vector_config.get("enabled", False):
        logger.info(f"Vector search disabled for agent: {instance_config.get('instance_name', 'unknown')}")
        return None
    
    # Check if pinecone config exists
    pinecone_config = vector_config.get("pinecone", {})
    if not pinecone_config:
        logger.warning(
            f"Vector search enabled but no pinecone config found for agent: "
            f"{instance_config.get('instance_name', 'unknown')}"
        )
        return None
    
    # Get API key from environment variable
    api_key_env = pinecone_config.get("api_key_env", "PINECONE_API_KEY")
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise ValueError(
            f"Pinecone API key not found in environment variable: {api_key_env}"
        )
    
    # Get required index name
    index_name = pinecone_config.get("index_name")
    if not index_name:
        raise ValueError(
            f"Pinecone index_name required in config for agent: "
            f"{instance_config.get('instance_name', 'unknown')}"
        )
    
    # Get namespace (default to "__default__")
    namespace = pinecone_config.get("namespace", "__default__")
    
    # Get or auto-discover index host
    index_host = pinecone_config.get("index_host")
    if not index_host:
        logger.info(f"Auto-discovering index host for: {index_name}")
        try:
            pc = Pinecone(api_key=api_key)
            index_info = pc.describe_index(index_name)
            index_host = index_info.host
            logger.info(f"Auto-discovered host: {index_host}")
        except Exception as e:
            raise ValueError(
                f"Failed to auto-discover index host for {index_name}: {str(e)}"
            )
    
    # Get embedding config (with defaults)
    embedding_config = vector_config.get("embedding", {})
    embedding_model = embedding_config.get("model", "text-embedding-3-small")
    dimensions = embedding_config.get("dimensions", 1536)
    
    logger.info({
        "event": "agent_pinecone_config_loaded",
        "agent": instance_config.get("instance_name", "unknown"),
        "index": index_name,
        "namespace": namespace,
        "embedding_model": embedding_model
    })
    
    return AgentPineconeConfig(
        api_key=api_key,
        index_name=index_name,
        index_host=index_host,
        namespace=namespace,
        embedding_model=embedding_model,
        dimensions=dimensions
    )

