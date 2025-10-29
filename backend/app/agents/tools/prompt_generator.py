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
from pydantic import BaseModel, Field
from app.models.directory import DirectoryList
from app.services.directory_importer import DirectoryImporter
import logfire


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
    result = await db_session.execute(
        select(DirectoryList).where(
            DirectoryList.account_id == account_id,
            DirectoryList.list_name.in_(accessible_lists)
        )
    )
    lists_metadata = result.scalars().all()
    
    if not lists_metadata:
        logfire.warn('directory.no_lists_found', account_id=str(account_id))
        return ""
    
    # Build CONCISE documentation - avoid tool loops
    docs_lines = ["## Directory Tool\n"]
    
    # Build list of available directories with counts
    documented_lists: List[DirectoryListDocs] = []
    list_summaries = []
    
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
            search_strategy_guidance = None
            search_strategy_examples = []
            if schema.get('search_strategy'):
                strategy = schema['search_strategy']
                search_strategy_guidance = strategy.get('guidance')
                strategy_examples = strategy.get('examples', [])
                # Format: "term1, term2, term3"
                search_strategy_examples = [ex.get('term', '') for ex in strategy_examples if ex.get('term')]
            
            # Create Pydantic model for structured logging
            list_docs = DirectoryListDocs(
                list_name=list_meta.list_name,
                entry_type=list_meta.entry_type,
                entry_count=entry_count,
                tags_description=tags_desc,
                tags_examples=tags_ex,
                searchable_fields=searchable_fields_dict,
                query_examples=search_strategy_examples  # Use examples from schema
            )
            documented_lists.append(list_docs)
            
            # Build concise summary for prompt
            list_summaries.append(f"`{list_meta.list_name}` ({entry_count} {list_meta.entry_type}s)")
            
            # Store first found search strategy (usually only one schema per agent)
            if search_strategy_guidance and not docs_lines[-1].startswith("**Search Strategy**"):
                strategy_text = search_strategy_guidance
                if search_strategy_examples:
                    examples_text = ", ".join(f"'{ex}'" for ex in search_strategy_examples)
                    strategy_text = f"{search_strategy_guidance} Examples: {examples_text}"
                docs_lines.append(f"\n**Search Strategy**: {strategy_text}")
            
        except Exception as e:
            logfire.error('directory.schema_load_error', list_name=list_meta.list_name, error=str(e))
            continue
    
    # Build minimal prompt text
    docs_lines.append("**Available**: " + ", ".join(list_summaries))
    
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

