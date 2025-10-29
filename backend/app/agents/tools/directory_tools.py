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
    specialty: Optional[str] = None,
    department: Optional[str] = None,
    gender: Optional[str] = None,
    drug_class: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
) -> str:
    """
    Search directory for entries (doctors, drugs, products, consultants, etc.).
    
    Use for: Name searches, tag/attribute filters, entry-specific fields
    
    Args:
        list_name: Which list to search (e.g., "doctors", "nurse_practitioners")
        query: Name to search (partial match)
        tag: Tag filter (language spoken, drug class, product category, etc.)
        specialty: Medical specialty filter (e.g., "Cardiology", "Endocrinology")
        department: Department filter (e.g., "Emergency Medicine", "Surgery")
        gender: Gender filter (e.g., "male", "female")
        drug_class: Drug class filter (for pharmaceutical entries)
        category: Product category filter (for product entries)
        brand: Brand filter (for product entries)
    
    Examples:
        search_directory(list_name="doctors", specialty="Cardiology", tag="Spanish")
        search_directory(list_name="doctors", query="smith", gender="female")
        search_directory(list_name="doctors", specialty="Endocrinology", tag="Hindi", gender="female")
    """
    logger.info({
        "event": "directory_search_called",
        "list_name": list_name,
        "query": query,
        "tag": tag,
        "specialty": specialty,
        "department": department,
        "gender": gender,
        "drug_class": drug_class,
        "category": category,
        "brand": brand
    })
    
    session = ctx.deps.db_session
    agent_config = ctx.deps.agent_config
    account_id = ctx.deps.account_id
    
    if not account_id:
        logger.error({"event": "directory_search_no_account", "list_name": list_name})
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
    
    logger.info({
        "event": "directory_lists_resolved",
        "list_name": list_name,
        "list_ids": [str(lid) for lid in list_ids],
        "account_id": str(account_id)
    })
    
    if not list_ids:
        logger.warning({"event": "directory_list_not_found", "list_name": list_name})
        return f"List '{list_name}' not found"
    
    tags = [tag] if tag else None
    
    # Build JSONB filters from explicit parameters
    jsonb_filters = {}
    if specialty:
        jsonb_filters['specialty'] = specialty
    if department:
        jsonb_filters['department'] = department
    if gender:
        jsonb_filters['gender'] = gender
    if drug_class:
        jsonb_filters['drug_class'] = drug_class
    if category:
        jsonb_filters['category'] = category
    if brand:
        jsonb_filters['brand'] = brand
    
    # Get search mode from config (default: substring for backward compatibility)
    search_mode = directory_config.get("search_mode", "substring")
    
    logger.info({
        "event": "directory_search_executing",
        "list_ids": [str(lid) for lid in list_ids],
        "name_query": query,
        "tags": tags,
        "jsonb_filters": jsonb_filters,
        "search_mode": search_mode,
        "limit": directory_config.get("max_results", 5)
    })
    
    entries = await service.search(
        session=session,
        accessible_list_ids=list_ids,
        name_query=query,
        tags=tags,
        jsonb_filters=jsonb_filters if jsonb_filters else None,
        search_mode=search_mode,
        limit=directory_config.get("max_results", 5)
    )
    
    logger.info({
        "event": "directory_search_complete",
        "entries_found": len(entries),
        "list_name": list_name
    })
    
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

