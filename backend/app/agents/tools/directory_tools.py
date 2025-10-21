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
from app.agents.base.dependencies import SessionDependencies
from app.services.directory_service import DirectoryService
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def search_directory(
    ctx: RunContext[SessionDependencies],
    list_name: str,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    **kwargs
) -> str:
    """
    Search directory for entries (doctors, drugs, products, consultants, etc.).
    
    Use for: Name searches, tag/attribute filters, entry-specific fields
    
    Args:
        list_name: Which list to search (e.g., "doctors", "nurse_practitioners")
        query: Name to search (partial match)
        tag: Tag filter (language, drug class, category, etc.)
        **kwargs: Entry-type specific filters (department, specialty, drug_class, category, price)
    
    Example: search_directory(list_name="doctors", query="smith", tag="Spanish")
    """
    session = ctx.deps.db_session
    agent_config = ctx.deps.agent_config
    account_id = ctx.deps.account_id
    
    if not account_id:
        return "Error: Account context not available"
    
    directory_config = agent_config.get("tools", {}).get("directory", {})
    accessible_lists = directory_config.get("accessible_lists", [])
    
    if not accessible_lists:
        return "Directory not configured"
    
    # Validate list_name is accessible
    if list_name not in accessible_lists:
        return f"List '{list_name}' not accessible. Available: {', '.join(accessible_lists)}"
    
    service = DirectoryService()
    list_ids = await service.get_accessible_lists(session, account_id, [list_name])
    
    if not list_ids:
        return f"List '{list_name}' not found"
    
    tags = [tag] if tag else None
    jsonb_filters = {k: kwargs[k] for k in ['department', 'specialty', 'drug_class', 'category', 'brand', 'price'] if k in kwargs and kwargs[k]}
    
    entries = await service.search(
        session=session,
        accessible_list_ids=list_ids,
        name_query=query,
        tags=tags,
        jsonb_filters=jsonb_filters if jsonb_filters else None,
        limit=directory_config.get("max_results", 5)
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

