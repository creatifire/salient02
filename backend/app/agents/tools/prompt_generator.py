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
import logging

logger = logging.getLogger(__name__)


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
        logger.info("No accessible lists configured")
        return ""
    
    logger.info(f"Generating directory docs for lists: {accessible_lists}")
    
    # Get list metadata from database
    result = await db_session.execute(
        select(DirectoryList).where(
            DirectoryList.account_id == account_id,
            DirectoryList.list_name.in_(accessible_lists)
        )
    )
    lists_metadata = result.scalars().all()
    
    if not lists_metadata:
        logger.warning(f"No directory lists found for account {account_id}")
        return ""
    
    # Build documentation using Pydantic models for structured logging
    docs_lines = ["## Directory Search Tool\n"]
    docs_lines.append("Search structured directory entries with natural language queries.\n")
    
    documented_lists: List[DirectoryListDocs] = []
    
    for list_meta in lists_metadata:
        try:
            # Load schema
            schema = DirectoryImporter.load_schema(list_meta.schema_file)
            
            # Entry count - use separate query to avoid lazy loading issue
            from app.models.directory import DirectoryEntry
            count_result = await db_session.execute(
                select(func.count(DirectoryEntry.id)).where(
                    DirectoryEntry.directory_list_id == list_meta.id
                )
            )
            entry_count = count_result.scalar_one()
            
            # Extract tags usage
            tags_desc = None
            tags_ex = []
            if schema.get('tags_usage'):
                tags_usage = schema['tags_usage']
                tags_desc = tags_usage.get('description')
                tags_ex = tags_usage.get('examples', [])
            
            # Extract searchable fields
            searchable_fields_dict = {}
            if schema.get('searchable_fields'):
                for field_name, field_def in schema['searchable_fields'].items():
                    searchable_fields_dict[field_name] = {
                        'description': field_def.get('description', 'N/A'),
                        'examples': ', '.join(f'"{ex}"' for ex in field_def.get('examples', [])[:3])
                    }
            
            # Build query examples
            query_examples = []
            if list_meta.entry_type == 'medical_professional':
                query_examples = [
                    f'Find cardiologist: `search_directory(list_name="{list_meta.list_name}", filters={{"specialty": "Cardiology"}})`',
                    f'Female surgeon: `search_directory(list_name="{list_meta.list_name}", filters={{"specialty": "Surgery", "gender": "female"}})`',
                    f'Spanish-speaking ER doctor: `search_directory(list_name="{list_meta.list_name}", filters={{"department": "Emergency Medicine"}}, tag="Spanish")`'
                ]
            elif list_meta.entry_type == 'pharmaceutical':
                query_examples = [
                    f'Pain medications: `search_directory(list_name="{list_meta.list_name}", filters={{"indications": "pain"}})`',
                    f'NSAIDs: `search_directory(list_name="{list_meta.list_name}", tag="NSAID")`'
                ]
            elif list_meta.entry_type == 'product':
                query_examples = [
                    f'Laptops by brand: `search_directory(list_name="{list_meta.list_name}", filters={{"category": "Laptops", "brand": "Dell"}})`',
                    f'In-stock items: `search_directory(list_name="{list_meta.list_name}", filters={{"in_stock": "true"}})`'
                ]
            
            # Create Pydantic model for this list
            list_docs = DirectoryListDocs(
                list_name=list_meta.list_name,
                entry_type=list_meta.entry_type,
                entry_count=entry_count,
                tags_description=tags_desc,
                tags_examples=tags_ex,
                searchable_fields=searchable_fields_dict,
                query_examples=query_examples
            )
            documented_lists.append(list_docs)
            
            # Build markdown for this list
            docs_lines.append(f"\n### {list_meta.list_name} ({list_meta.entry_type})")
            docs_lines.append(f"**Entries**: {entry_count}\n")
            
            if tags_desc:
                docs_lines.append(f"**Tags**: {tags_desc}")
                if tags_ex:
                    docs_lines.append(f"  Examples: {', '.join(tags_ex)}\n")
            
            if searchable_fields_dict:
                docs_lines.append("**Searchable Filters**:")
                for field_name, field_info in searchable_fields_dict.items():
                    docs_lines.append(f"- `{field_name}`: {field_info['description']}")
                    docs_lines.append(f"  Examples: {field_info['examples']}")
                docs_lines.append("")
            
            if query_examples:
                docs_lines.append("**Query Examples**:")
                for example in query_examples:
                    docs_lines.append(f"- {example}")
                docs_lines.append("")
            
        except Exception as e:
            logger.error(f"Error loading schema for {list_meta.list_name}: {e}")
            continue
    
    markdown_content = '\n'.join(docs_lines)
    
    # Create Pydantic model for complete documentation
    generated_docs = GeneratedDirectoryDocs(
        account_id=account_id,
        accessible_lists=accessible_lists,
        lists_documented=documented_lists,
        markdown_content=markdown_content
    )
    
    # Log structured Pydantic model (Logfire will automatically capture all fields)
    logger.info(
        'Directory documentation generated: {docs!r}',
        docs=generated_docs
    )
    
    return generated_docs.markdown_content

