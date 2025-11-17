"""
Vector Search Tool for Pydantic AI Agents
Enables agents to search vector databases (Pinecone) for relevant information.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



from pydantic_ai import RunContext
from typing import Optional
import logfire

from ..base.dependencies import SessionDependencies
from ...services.vector_service import VectorService, VectorQueryResponse
from ...services.agent_pinecone_config import (
    load_agent_pinecone_config,
    get_cached_pinecone_client
)


async def vector_search(
    ctx: RunContext[SessionDependencies],
    query: str,
    max_results: Optional[int] = None
) -> str:
    """
    Semantic search over document content for explanations, descriptions, and knowledge.
    
    **USE THIS TOOL FOR:**
    - "What is...", "Tell me about...", "Explain..." questions
    - General information from documents and web pages
    - Product/service descriptions and capabilities
    - Organization policies, procedures, and guidelines
    - Educational content, guides, FAQs
    - Technical documentation and explanations
    
    **DO NOT USE THIS TOOL FOR:**
    - Finding specific people (doctors, staff, employees) → use search_directory
    - Department contact information (phone, email, location) → use search_directory
    - Structured records with exact fields → use search_directory
    - Anything requiring current/exact data from a database → use search_directory
    
    This tool searches through unstructured document text (website content, PDFs, articles),
    NOT structured database records. For structured data with specific fields, use
    get_available_directories() to discover directories, then use search_directory().
    
    Why use this tool?
    1. Provides organization-specific context from published content
    2. Grounds responses in actual documents (not hallucinations)
    3. Retrieves explanations, descriptions, and narrative content
    4. Works across all content types (web pages, docs, guides)
    
    Args:
        ctx: Pydantic AI context with session dependencies
        query: Natural language question or search terms
        max_results: Maximum number of results to return (defaults to agent config)
    
    Returns:
        Formatted search results with relevant content, or message if no results found.
        Results include text excerpts, relevance scores, and metadata (e.g., page titles, URLs).
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
        logfire.error(
            'agent.tool.vector_search.config_missing',
            session_id=session_id,
            agent=agent_config.get("instance_name", "unknown")
        )
        return "Vector search configuration error."
    
    # Get cached PineconeClient (reuses connection pool per Pinecone best practices)
    pinecone_client = get_cached_pinecone_client(pinecone_config)
    vector_service = VectorService(pinecone_client=pinecone_client)
    
    # Query parameters: Configuration cascade (LLM param → agent → app.yaml → code)
    from ...config import load_config
    app_config = load_config()
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
    
    logfire.info(
        'agent.tool.vector_search.start',
        session_id=session_id,
        query=query,
        index=pinecone_config.index_name,
        namespace=pinecone_config.namespace,
        top_k=top_k,
        threshold=similarity_threshold
    )
    
    # Perform search
    try:
        response: VectorQueryResponse = await vector_service.query_similar(
            query_text=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            namespace=pinecone_config.namespace
        )
        
        logfire.info(
            'agent.tool.vector_search.complete',
            session_id=session_id,
            results_count=response.total_results,
            query_time_ms=response.query_time_ms
        )
        
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
        logfire.exception(
            'agent.tool.vector_search.error',
            session_id=session_id,
            query=query
        )
        return "Vector search encountered an error. Please try rephrasing your query."

