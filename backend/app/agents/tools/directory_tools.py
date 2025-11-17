"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

from __future__ import annotations

"""
Directory search tool for Pydantic AI agents.

Provides natural language search across multi-tenant directory lists
(doctors, drugs, products, consultants, services, etc.)
"""

from pydantic_ai import RunContext
from ..base.dependencies import SessionDependencies
from ...services.directory_service import DirectoryService
from ...services.directory_importer import DirectoryImporter
from ...database import get_database_service
from ...models.directory import DirectoryList, DirectoryEntry
from typing import Optional, Dict
from sqlalchemy import select, func
import logfire
import json


async def get_available_directories(
    ctx: RunContext[SessionDependencies]
) -> str:
    """
    Get metadata about available directory tools.
    
    **CALL THIS FIRST before using search_directory** to understand:
    - What directories exist
    - What data each contains
    - When to use each directory
    - What fields are searchable
    - Example queries
    
    Returns JSON with directory metadata including:
    - Directory name (list_name)
    - Entry type (doctors, contacts, products, etc.)
    - Entry count
    - Use cases (when to use this directory)
    - Searchable fields
    - Example queries
    
    **Usage Pattern**:
    1. User asks question
    2. Call get_available_directories() to see options
    3. Choose appropriate directory based on metadata
    4. Call search_directory(list_name=...) with chosen directory
    
    Example:
        User: "What's the cardiology department phone number?"
        Step 1: get_available_directories()
        Step 2: Review returned metadata, see phone_directory has department contacts
        Step 3: search_directory(list_name="phone_directory", query="cardiology")
    """
    logfire.info('directory.get_available_called')
    
    # Get context from dependencies
    agent_config = ctx.deps.agent_config
    account_id = ctx.deps.account_id
    
    if not account_id:
        logfire.error('directory.get_available_no_account')
        return json.dumps({"error": "No account context available"})
    
    directory_config = agent_config.get("tools", {}).get("directory", {})
    accessible_lists = directory_config.get("accessible_lists", [])
    
    if not accessible_lists:
        logfire.warn('directory.no_accessible_lists_configured')
        return json.dumps({
            "directories": [],
            "total_count": 0,
            "message": "No directories configured for this account"
        })
    
    # Create independent database session for this tool call
    db_service = get_database_service()
    async with db_service.get_session() as session:
        # Get list metadata from database
        result = await session.execute(
            select(DirectoryList).where(
                DirectoryList.account_id == account_id,
                DirectoryList.list_name.in_(accessible_lists)
            )
        )
        lists_metadata = result.scalars().all()
        
        if not lists_metadata:
            logfire.warn('directory.no_lists_found', account_id=str(account_id))
            return json.dumps({
                "directories": [],
                "total_count": 0,
                "message": f"No directories found for account {account_id}"
            })
        
        directories_info = []
        
        for list_meta in lists_metadata:
            try:
                # Get entry count
                count_result = await session.execute(
                    select(func.count(DirectoryEntry.id)).where(
                        DirectoryEntry.directory_list_id == list_meta.id
                    )
                )
                entry_count = count_result.scalar_one()
                
                # Load YAML schema
                schema = DirectoryImporter.load_schema(list_meta.schema_file)
                purpose = schema.get('directory_purpose', {})
                
                # Extract searchable fields
                searchable_fields = []
                if schema.get('searchable_fields'):
                    searchable_fields = list(schema['searchable_fields'].keys())
                
                # Build directory info
                directory_info = {
                    "list_name": list_meta.list_name,
                    "entry_type": list_meta.entry_type,
                    "entry_count": entry_count,
                    "description": purpose.get('description', ''),
                    "use_cases": purpose.get('use_for', []),
                    "searchable_fields": searchable_fields,
                    "example_queries": purpose.get('example_queries', []),
                    "not_for": purpose.get('not_for', [])
                }
                
                directories_info.append(directory_info)
                
                logfire.info(
                    'directory.metadata_loaded',
                    list_name=list_meta.list_name,
                    entry_count=entry_count
                )
                
            except Exception as e:
                logfire.error(
                    'directory.metadata_load_error',
                    list_name=list_meta.list_name,
                    error=str(e)
                )
                # Continue with other directories even if one fails
                continue
        
        result = {
            "directories": directories_info,
            "total_count": len(directories_info)
        }
        
        logfire.info(
            'directory.get_available_complete',
            directories_count=len(directories_info)
        )
        
        return json.dumps(result, indent=2)


async def search_directory(
    ctx: RunContext[SessionDependencies],
    list_name: str,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    filters: Optional[Dict[str, str]] = None,
) -> str:
    """
    Search a directory for structured data entries with exact fields.
    
    **IMPORTANT**: Call get_available_directories() FIRST to see what directories exist
    and choose the right one for your query.
    
    This tool searches structured records with specific fields (names, specialties,
    departments, contact info, etc.). Each directory has different fields - use
    get_available_directories() to see what's searchable.
    
    Args:
        list_name: Directory name (get from get_available_directories())
        query: Natural language search across all text fields
        tag: Filter by tag (if directory supports tags)
        filters: Exact field matches (e.g., {"specialty": "Cardiology"})
    
    Search Strategies:
        1. query parameter: Searches across ALL text fields (names, descriptions, etc.)
           - Best for: "Find X", "Who is...", "Search for..."
           - Example: query="cardiology" searches names, specialties, departments
        
        2. filters parameter: Exact field matches (case-insensitive)
           - Best for: Structured queries with known field names
           - Example: filters={"department_name": "Billing"}
        
        3. Combined: Use both for precision
           - Example: query="heart", filters={"language": "Spanish"}
    
    Returns:
        JSON with matching entries or error message
    """
    logfire.info(
        'directory.search_called',
        list_name=list_name,
        query=query,
        tag=tag,
        filters=filters
    )
    
    # Get context from dependencies
    agent_config = ctx.deps.agent_config
    account_id = ctx.deps.account_id
    
    if not account_id:
        logfire.error('directory.search_no_account', list_name=list_name)
        return "Error: Account context not available"
    
    directory_config = agent_config.get("tools", {}).get("directory", {})
    accessible_lists = directory_config.get("accessible_lists", [])
    
    if not accessible_lists:
        return "Directory not configured"
    
    # Validate list_name is accessible
    if list_name not in accessible_lists:
        return f"List '{list_name}' not accessible. Available: {', '.join(accessible_lists)}"
    
    # Create independent database session for this tool call (BUG-0023-001)
    db_service = get_database_service()
    async with db_service.get_session() as session:
        service = DirectoryService()
        list_ids = await service.get_accessible_lists(session, account_id, [list_name])
    
        logfire.info(
            'directory.lists_resolved',
            list_name=list_name,
            list_ids=[str(lid) for lid in list_ids],
            account_id=str(account_id)
        )
        
        if not list_ids:
            logfire.warn('directory.list_not_found', list_name=list_name)
            return f"List '{list_name}' not found"
        
        tags = [tag] if tag else None
        
        # Get search mode from config (default: substring for backward compatibility)
        search_mode = directory_config.get("search_mode", "substring")
        max_results = directory_config.get("max_results", 5)
        
        logfire.info(
            'directory.search_executing',
            list_ids=[str(lid) for lid in list_ids],
            name_query=query,
            tags=tags,
            jsonb_filters=filters,
            search_mode=search_mode,
            limit=max_results
        )
        
        entries = await service.search(
            session=session,
            accessible_list_ids=list_ids,
            name_query=query,
            tags=tags,
            jsonb_filters=filters,
            search_mode=search_mode,
            limit=max_results
        )
        
        logfire.info(
            'directory.search_complete',
            entries_found=len(entries),
            list_name=list_name
        )
        
        if not entries:
            return "No entries found"
        
        # Format results (adaptive by entry type)
        result_lines = [f"Found {len(entries)} entry(ies):\n"]
        
        for i, entry in enumerate(entries, 1):
            lines = [f"{i}. **{entry.name}**"]
            
            # Medical professionals
            if 'department' in entry.entry_data or 'specialty' in entry.entry_data:
                dept = entry.entry_data.get('department', '')
                spec = entry.entry_data.get('specialty', '')
                if dept or spec:
                    lines.append(f"   {dept}" + (f" - {spec}" if spec else ""))
            
            # Pharmaceuticals
            if 'drug_class' in entry.entry_data:
                lines.append(f"   Class: {entry.entry_data['drug_class']}")
                if entry.entry_data.get('dosage_forms'):
                    lines.append(f"   Forms: {', '.join(entry.entry_data['dosage_forms'])}")
            
            # Products
            if 'category' in entry.entry_data:
                lines.append(f"   Category: {entry.entry_data['category']}")
                if entry.entry_data.get('price'):
                    lines.append(f"   Price: ${entry.entry_data['price']}")
            
            # Tags
            if entry.tags:
                lines.append(f"   Tags: {', '.join(entry.tags)}")
            
            # Contact info
            if entry.contact_info.get('location'):
                lines.append(f"   Location: {entry.contact_info['location']}")
            if entry.contact_info.get('product_url'):
                lines.append(f"   URL: {entry.contact_info['product_url']}")
            
            # Additional details
            if entry.entry_data.get('education'):
                lines.append(f"   Education: {entry.entry_data['education']}")
            if entry.entry_data.get('indications'):
                lines.append(f"   Uses: {entry.entry_data['indications'][:100]}...")
            if entry.entry_data.get('in_stock') is not None:
                lines.append(f"   {'In Stock' if entry.entry_data['in_stock'] else 'Out of Stock'}")
            
            result_lines.append('\n'.join(lines))
        
        return '\n\n'.join(result_lines)

