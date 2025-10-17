"""
Vector Search Tool for Pydantic AI Agents
Enables agents to search vector databases (Pinecone) for relevant information.
"""

from pydantic_ai import RunContext
from typing import Optional
import logging

from backend.app.agents.base.dependencies import SessionDependencies
from backend.app.services.vector_service import VectorService, VectorQueryResponse
from backend.app.services.agent_pinecone_config import load_agent_pinecone_config


logger = logging.getLogger(__name__)


async def vector_search(
    ctx: RunContext[SessionDependencies],
    query: str,
    max_results: Optional[int] = None
) -> str:
    """
    Search the knowledge base for relevant information using vector similarity.
    
    This tool searches pre-loaded content from vector databases (e.g., website content,
    documentation) to find information relevant to the user's query.
    
    Args:
        ctx: Pydantic AI context with session dependencies
        query: Natural language query to search for
        max_results: Maximum number of results to return (defaults to agent config)
    
    Returns:
        Formatted search results or message if no results found
    """
    agent_config = ctx.deps.agent_config
    session_id = ctx.deps.session_id
    
    # Get vector search config
    vector_config = agent_config.get("tools", {}).get("vector_search", {})
    if not vector_config.get("enabled", False):
        return "Vector search is not enabled for this agent."
    
    # Load agent's Pinecone config
    pinecone_config = load_agent_pinecone_config(agent_config)
    if not pinecone_config:
        logger.error({
            "event": "vector_search_config_missing",
            "session_id": session_id,
            "agent": agent_config.get("instance_name", "unknown")
        })
        return "Vector search configuration error."
    
    # Create agent-specific VectorService
    from backend.app.services.pinecone_client import PineconeClient
    pinecone_client = PineconeClient.create_from_agent_config(pinecone_config)
    vector_service = VectorService(pinecone_client=pinecone_client)
    
    # Query parameters: Configuration cascade (LLM param → agent → app.yaml → code)
    from backend.app.config import app_config
    global_vector_config = app_config.get("vector", {}).get("search", {})
    
    top_k = (
        max_results or  # LLM parameter (highest priority)
        vector_config.get("max_results") or  # Agent config
        global_vector_config.get("max_results", 5)  # app.yaml → code default
    )
    similarity_threshold = (
        vector_config.get("similarity_threshold") or  # Agent config
        global_vector_config.get("similarity_threshold", 0.7)  # app.yaml → code default
    )
    
    logger.info({
        "event": "vector_search_start",
        "session_id": session_id,
        "query": query,
        "index": pinecone_config.index_name,
        "namespace": pinecone_config.namespace,
        "top_k": top_k,
        "threshold": similarity_threshold
    })
    
    # Perform search
    try:
        response: VectorQueryResponse = await vector_service.query_similar(
            query_text=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            namespace=pinecone_config.namespace
        )
        
        logger.info({
            "event": "vector_search_complete",
            "session_id": session_id,
            "results_count": response.total_results,
            "query_time_ms": response.query_time_ms
        })
        
        # Format results for LLM consumption
        if not response.results:
            return f"No relevant information found in knowledge base for query: '{query}'"
        
        formatted_lines = [
            f"Found {response.total_results} relevant result(s) in knowledge base:\n"
        ]
        
        for i, result in enumerate(response.results, 1):
            formatted_lines.append(f"{i}. {result.text}")
            formatted_lines.append(f"   Relevance Score: {result.score:.3f}")
            
            # Include metadata if present (e.g., page title, URL, category from WordPress)
            if result.metadata:
                metadata_str = ", ".join(
                    f"{k}: {v}" for k, v in result.metadata.items() 
                    if k not in ["text", "created_at", "embedding_model"]
                )
                if metadata_str:
                    formatted_lines.append(f"   Details: {metadata_str}")
            
            formatted_lines.append("")  # Blank line between results
        
        return "\n".join(formatted_lines)
        
    except Exception as e:
        logger.error({
            "event": "vector_search_error",
            "session_id": session_id,
            "error": str(e),
            "query": query
        })
        return "Vector search encountered an error. Please try rephrasing your query."

