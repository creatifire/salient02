"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

"""
System prompt generation for directory tools.

Auto-generates directory tool documentation from:
1. Agent config (accessible_lists)
2. Database (list metadata, entry counts)
3. Schema files (searchable fields, tags usage)
"""

from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from ...models.directory import DirectoryList
from ...services.directory_importer import DirectoryImporter
import logfire


def load_base_prompt(agent_config: Dict) -> str:
    """
    Load base system prompt from agent configuration.
    
    Args:
        agent_config: Agent configuration from config.yaml
        
    Returns:
        System prompt content as string
    """
    # For now, return the system_prompt from config if present
    # In the future, this could load from files
    return agent_config.get("system_prompt", "You are a helpful assistant.")


class DirectoryListDocs(BaseModel):
    """Documentation for a single directory list."""
    list_name: str = Field(description="Name of the directory list")
    entry_type: str = Field(description="Type of entries in the list")
    entry_count: int = Field(description="Number of entries in the list")
    tags_description: Optional[str] = Field(None, description="Description of tags usage")
    tags_examples: List[str] = Field(default_factory=list, description="Example tags")
    searchable_fields: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Fields that can be filtered")
    query_examples: List[str] = Field(default_factory=list, description="Example queries for this list")


class GeneratedDirectoryDocs(BaseModel):
    """Complete generated documentation for directory tool."""
    account_id: UUID = Field(description="Account these docs were generated for")
    accessible_lists: List[str] = Field(description="Lists that were documented")
    lists_documented: List[DirectoryListDocs] = Field(description="Documentation for each list")
    markdown_content: str = Field(description="Full markdown documentation")
    
    class Config:
        """Pydantic config for Logfire integration."""
        # This makes the model log nicely in Logfire
        str_strip_whitespace = True


async def generate_directory_tool_docs(
    agent_config: Dict,
    account_id: UUID,
    db_session: AsyncSession
) -> str:
    """
    Auto-generate system prompt documentation for directory tool.
    
    Args:
        agent_config: Agent configuration dict from config.yaml
        account_id: Account UUID for multi-tenant filtering
        db_session: Async database session
    
    Returns:
        Formatted markdown documentation string
    """
    directory_config = agent_config.get("tools", {}).get("directory", {})
    accessible_lists = directory_config.get("accessible_lists", [])
    
    if not accessible_lists:
        logfire.info('directory.no_accessible_lists_configured')
        return ""
    
    logfire.info('directory.generating_docs', accessible_lists=accessible_lists)
    
    # Get list metadata from database
    # Using selectinload() prevents N+1 queries if relationships are accessed (e.g., in to_dict())
    result = await db_session.execute(
        select(DirectoryList)
        .options(
            selectinload(DirectoryList.entries),  # Eager load entries relationship
            selectinload(DirectoryList.account)  # Eager load account relationship
        )
        .where(
            DirectoryList.account_id == account_id,
            DirectoryList.list_name.in_(accessible_lists)
        )
    )
    lists_metadata = result.scalars().all()
    
    if not lists_metadata:
        logfire.warn('directory.no_lists_found', account_id=str(account_id))
        return ""
    
    # Build documentation
    docs_lines = []
    documented_lists: List[DirectoryListDocs] = []
    list_summaries = []
    
    # If multiple directories, add selection guide first
    if len(lists_metadata) > 1:
        docs_lines.append("## Directory Tool\n")
        docs_lines.append("You have access to multiple directories. Choose the appropriate directory based on the query:\n")
    else:
        docs_lines.append("## Directory Tool\n")
    
    # First pass: Build directory selection guide (if multiple directories)
    if len(lists_metadata) > 1:
        for list_meta in lists_metadata:
            try:
                schema = DirectoryImporter.load_schema(list_meta.schema_file)
                purpose = schema.get('directory_purpose', {})
                
                # Get entry count
                from app.models.directory import DirectoryEntry
                count_result = await db_session.execute(
                    select(func.count(DirectoryEntry.id)).where(
                        DirectoryEntry.directory_list_id == list_meta.id
                    )
                )
                entry_count = count_result.scalar_one()
                
                docs_lines.append(f"\n### Directory: `{list_meta.list_name}` ({entry_count} {list_meta.entry_type}s)")
                docs_lines.append(f"**Contains**: {purpose.get('description', 'N/A')}")
                
                if purpose.get('use_for'):
                    docs_lines.append("**Use for**:")
                    for use_case in purpose['use_for']:
                        docs_lines.append(f"- {use_case}")
                
                if purpose.get('example_queries'):
                    examples = ', '.join(f'"{q}"' for q in purpose['example_queries'][:3])
                    docs_lines.append(f"\n**Example queries**: {examples}")
                
                if purpose.get('not_for'):
                    for exclusion in purpose['not_for']:
                        docs_lines.append(f"**Don't use for**: {exclusion}")
                
                docs_lines.append("\n---")
            
            except Exception as e:
                logfire.error('directory.schema_load_error', list_name=list_meta.list_name, error=str(e))
                continue
        
        # Multi-directory query guidance
        docs_lines.append("\n### Multi-Directory Queries")
        docs_lines.append("\n**If a query involves multiple aspects**:")
        docs_lines.append("1. Search the most specific directory first")
        docs_lines.append("2. Combine results if relevant to the query")
        docs_lines.append("3. Example: 'I need a cardiologist, what's the phone number?'")
        docs_lines.append("   - First: Search `doctors` for cardiologists → Get doctor's contact info")
        docs_lines.append("   - Then: If scheduling mentioned, check `phone_directory` for appointments")
        docs_lines.append("")
    
    # Second pass: Build detailed tool documentation for each directory
    for list_meta in lists_metadata:
        try:
            # Entry count - use separate query to avoid lazy loading issue
            from app.models.directory import DirectoryEntry
            count_result = await db_session.execute(
                select(func.count(DirectoryEntry.id)).where(
                    DirectoryEntry.directory_list_id == list_meta.id
                )
            )
            entry_count = count_result.scalar_one()
            
            # Load schema for Pydantic model (for logging only) and search strategy
            schema = DirectoryImporter.load_schema(list_meta.schema_file)
            tags_desc = None
            tags_ex = []
            if schema.get('tags_usage'):
                tags_usage = schema['tags_usage']
                tags_desc = tags_usage.get('description')
                tags_ex = tags_usage.get('examples', [])
            
            searchable_fields_dict = {}
            if schema.get('searchable_fields'):
                for field_name, field_def in schema['searchable_fields'].items():
                    searchable_fields_dict[field_name] = {
                        'description': field_def.get('description', 'N/A'),
                        'examples': ', '.join(f'"{ex}"' for ex in field_def.get('examples', [])[:3])
                    }
            
            # Extract search strategy from schema
            search_strategy_text = None
            if schema.get('search_strategy'):
                strategy = schema['search_strategy']
                strategy_parts = []
                
                # Add guidance
                if strategy.get('guidance'):
                    strategy_parts.append(strategy['guidance'])
                
                # Add synonym mappings (most important for medical terms)
                if strategy.get('synonym_mappings'):
                    mappings = strategy['synonym_mappings']
                    # Use custom heading from schema if provided
                    heading = strategy.get('synonym_mappings_heading', 'Term Mappings (Lay → Formal)')
                    strategy_parts.append(f"\n**{heading}:**")
                    for mapping in mappings[:10]:  # Limit to first 10 to keep prompt manageable
                        lay_terms = ', '.join(f'"{term}"' for term in mapping.get('lay_terms', [])[:3])
                        formal_terms = ', '.join(f'"{term}"' for term in mapping.get('formal_terms', []))
                        if lay_terms and formal_terms:
                            strategy_parts.append(f"  • {lay_terms} → {formal_terms}")
                
                # Add concrete examples with thought process
                if strategy.get('examples'):
                    examples = strategy['examples'][:2]  # Limit to 2 examples
                    for i, ex in enumerate(examples, 1):
                        if ex.get('user_query') and ex.get('tool_calls'):
                            strategy_parts.append(f"\n**Example {i}:** \"{ex['user_query']}\"")
                            if ex.get('thought_process'):
                                strategy_parts.append(f"  → Think: {ex['thought_process'].strip()}")
                            tool_calls = ex.get('tool_calls', [])
                            for tool_call in tool_calls[:2]:  # Max 2 tool calls per example
                                strategy_parts.append(f"  → Call: {tool_call}")
                
                if strategy_parts:
                    search_strategy_text = '\n'.join(strategy_parts)
            
            # Create Pydantic model for structured logging (using empty list for query_examples since we're using full text now)
            list_docs = DirectoryListDocs(
                list_name=list_meta.list_name,
                entry_type=list_meta.entry_type,
                entry_count=entry_count,
                tags_description=tags_desc,
                tags_examples=tags_ex,
                searchable_fields=searchable_fields_dict,
                query_examples=[]  # Not using simple examples anymore - using full strategy text
            )
            documented_lists.append(list_docs)
            
            # Build concise summary for prompt
            list_summaries.append(f"`{list_meta.list_name}` ({entry_count} {list_meta.entry_type}s)")
            
            # For single directory, add search strategy details
            if len(lists_metadata) == 1 and search_strategy_text:
                docs_lines.append(f"\n{search_strategy_text}")
            
        except Exception as e:
            logfire.error('directory.schema_load_error', list_name=list_meta.list_name, error=str(e))
            continue
    
    # Build minimal prompt text - list available directories
    if list_summaries:
        docs_lines.append("\n**Available**: " + ", ".join(list_summaries) + "\n")
    
    markdown_content = '\n'.join(docs_lines)
    
    # Create Pydantic model for complete documentation
    generated_docs = GeneratedDirectoryDocs(
        account_id=account_id,
        accessible_lists=accessible_lists,
        lists_documented=documented_lists,
        markdown_content=markdown_content
    )
    
    # Log structured Pydantic model (Logfire will automatically capture all fields)
    logfire.info(
        'directory.documentation_generated',
        docs=generated_docs
    )
    
    # ALSO log the actual prompt text for debugging
    logfire.info('directory.generated_prompt_text', prompt_length=len(markdown_content), prompt_text=markdown_content)
    
    return generated_docs.markdown_content

