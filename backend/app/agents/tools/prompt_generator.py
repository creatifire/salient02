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
from sqlalchemy import select
from app.models.directory import DirectoryList
from app.services.directory_importer import DirectoryImporter
import logging

logger = logging.getLogger(__name__)


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
    
    # Build documentation
    docs = ["## Directory Search Tool\n"]
    docs.append("Search structured directory entries with natural language queries.\n")
    
    for list_meta in lists_metadata:
        try:
            # Load schema
            schema = DirectoryImporter.load_schema(list_meta.schema_file)
            
            docs.append(f"\n### {list_meta.list_name} ({list_meta.entry_type})")
            
            # Entry count from relationship
            entry_count = len(list_meta.entries) if list_meta.entries else 0
            docs.append(f"**Entries**: {entry_count}\n")
            
            # Tags documentation
            if schema.get('tags_usage'):
                tags_usage = schema['tags_usage']
                docs.append(f"**Tags**: {tags_usage.get('description', 'N/A')}")
                if tags_usage.get('examples'):
                    docs.append(f"  Examples: {', '.join(tags_usage['examples'])}\n")
            
            # Searchable fields
            if schema.get('searchable_fields'):
                docs.append("**Searchable Filters**:")
                for field_name, field_def in schema['searchable_fields'].items():
                    docs.append(f"- `{field_name}`: {field_def.get('description', 'N/A')}")
                    if field_def.get('examples'):
                        examples_str = ', '.join(f'"{ex}"' for ex in field_def['examples'][:3])
                        docs.append(f"  Examples: {examples_str}")
                docs.append("")
            
            # Usage examples (type-specific)
            docs.append("**Query Examples**:")
            if list_meta.entry_type == 'medical_professional':
                docs.append(f'- Find cardiologist: `search_directory(list_name="{list_meta.list_name}", filters={{"specialty": "Cardiology"}})`')
                docs.append(f'- Female surgeon: `search_directory(list_name="{list_meta.list_name}", filters={{"specialty": "Surgery", "gender": "female"}})`')
                docs.append(f'- Spanish-speaking ER doctor: `search_directory(list_name="{list_meta.list_name}", filters={{"department": "Emergency Medicine"}}, tag="Spanish")`')
            elif list_meta.entry_type == 'pharmaceutical':
                docs.append(f'- Pain medications: `search_directory(list_name="{list_meta.list_name}", filters={{"indications": "pain"}})`')
                docs.append(f'- NSAIDs: `search_directory(list_name="{list_meta.list_name}", tag="NSAID")`')
            elif list_meta.entry_type == 'product':
                docs.append(f'- Laptops by brand: `search_directory(list_name="{list_meta.list_name}", filters={{"category": "Laptops", "brand": "Dell"}})`')
                docs.append(f'- In-stock items: `search_directory(list_name="{list_meta.list_name}", filters={{"in_stock": "true"}})`')
            
            docs.append("")
            
        except Exception as e:
            logger.error(f"Error loading schema for {list_meta.list_name}: {e}")
            continue
    
    generated_docs = '\n'.join(docs)
    logger.info(f"Generated {len(generated_docs)} chars of directory documentation")
    
    return generated_docs

