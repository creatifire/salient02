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
from ...database import get_database_service
from typing import Optional, Dict
import logfire


async def search_directory(
    ctx: RunContext[SessionDependencies],
    list_name: str,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    filters: Optional[Dict[str, str]] = None,
) -> str:
    """
    Search directory for entries (doctors, drugs, products, consultants, etc.).
    
    **CRITICAL: Parameter Selection Rules:**
    - `query`: ONLY for searching doctor/entry NAMES (e.g., "Dr. Smith", "John")
    - `filters`: MUST use for specialty, department, gender, or any JSONB field searches
    - NEVER use `query` for medical specialties - always use `filters={"specialty": "..."}`
    
    **For Medical Specialties:**
    - User asks "urologists" → Use `filters={"specialty": "Urology"}` (NOT query="urologist")
    - User asks "cardiologists" → Use `filters={"specialty": "Cardiology"}` (NOT query="cardiologist")
    - User asks "heart doctors" → Use `filters={"specialty": "Cardiology"}` (NOT query="heart")
    
    Args:
        list_name: Which list to search (e.g., "doctors", "prescription_drugs", "electronics")
        query: Name to search ONLY (e.g., "Dr. Smith", "John", "Mary") - partial match, case-insensitive
               DO NOT use for specialties or departments - use filters instead
        tag: Tag filter (language for medical, drug class for pharma, category for products)
        filters: Type-specific JSONB filters as a dictionary - USE THIS for specialties, departments, etc.
                 Examples: {"specialty": "Urology", "gender": "female"}
                          {"specialty": "Cardiology"}  # For "cardiologists" queries
                          {"department": "Emergency Medicine"}
                          {"drug_class": "NSAID", "indications": "pain"}
                          {"category": "Laptops", "brand": "Dell", "in_stock": "true"}
    
    Examples:
        # Medical professionals - ALWAYS use filters for specialty searches
        search_directory(list_name="doctors", filters={"specialty": "Urology"})  # "what urologists"
        search_directory(list_name="doctors", filters={"specialty": "Cardiology"})  # "heart doctors"
        search_directory(list_name="doctors", filters={"specialty": "Cardiology", "gender": "female"}, tag="Spanish")
        search_directory(list_name="doctors", query="smith", filters={"gender": "female"})  # Name search OK
        search_directory(list_name="doctors", filters={"department": "Emergency Medicine", "specialty": "Pediatrics"})
        
        # Pharmaceuticals
        search_directory(list_name="prescription_drugs", filters={"drug_class": "NSAID"})
        search_directory(list_name="prescription_drugs", filters={"indications": "pain"}, tag="Over-the-counter")
        
        # Products
        search_directory(list_name="electronics", filters={"category": "Laptops", "brand": "Dell"})
        search_directory(list_name="electronics", query="macbook", filters={"in_stock": "true"})  # Name search OK
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

