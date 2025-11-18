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
            return json.dumps({"entries": [], "total": 0, "message": "No entries found"})
        
        # Format results as JSON (flattened structure)
        results = []
        
        for entry in entries:
            # Start with base fields (always included)
            result = {
                "name": entry.name,
                "entry_type": entry.directory_list.entry_type
            }
            
            # Add tags if present
            if entry.tags:
                result["tags"] = entry.tags
            
            # Add contact info fields (flatten from contact_info JSONB)
            if entry.contact_info.get('phone'):
                result["phone"] = entry.contact_info['phone']
            if entry.contact_info.get('email'):
                result["email"] = entry.contact_info['email']
            if entry.contact_info.get('fax'):
                result["fax"] = entry.contact_info['fax']
            if entry.contact_info.get('location'):
                result["location"] = entry.contact_info['location']
            if entry.contact_info.get('product_url'):
                result["url"] = entry.contact_info['product_url']
            
            # Add type-specific fields from entry_data (flatten based on entry_type)
            entry_type = entry.directory_list.entry_type
            
            if entry_type == "medical_professional":
                if entry.entry_data.get('department'):
                    result["department"] = entry.entry_data['department']
                if entry.entry_data.get('specialty'):
                    result["specialty"] = entry.entry_data['specialty']
                if entry.entry_data.get('education'):
                    result["education"] = entry.entry_data['education']
                if entry.entry_data.get('board_certifications'):
                    result["board_certifications"] = entry.entry_data['board_certifications']
                if entry.entry_data.get('gender'):
                    result["gender"] = entry.entry_data['gender']
            
            elif entry_type == "contact_information":
                if entry.entry_data.get('service_type'):
                    result["service_type"] = entry.entry_data['service_type']
                if entry.entry_data.get('hours_of_operation'):
                    result["hours"] = entry.entry_data['hours_of_operation']
                if entry.entry_data.get('description'):
                    result["description"] = entry.entry_data['description']
            
            elif entry_type == "pharmaceutical":
                if entry.entry_data.get('drug_class'):
                    result["drug_class"] = entry.entry_data['drug_class']
                if entry.entry_data.get('generic_name'):
                    result["generic_name"] = entry.entry_data['generic_name']
                if entry.entry_data.get('brand_names'):
                    result["brand_names"] = entry.entry_data['brand_names']
                if entry.entry_data.get('dosage_forms'):
                    result["dosage_forms"] = entry.entry_data['dosage_forms']
                if entry.entry_data.get('strengths'):
                    result["strengths"] = entry.entry_data['strengths']
                if entry.entry_data.get('indications'):
                    result["indications"] = entry.entry_data['indications']
                if entry.entry_data.get('contraindications'):
                    result["contraindications"] = entry.entry_data['contraindications']
                if entry.entry_data.get('side_effects'):
                    result["side_effects"] = entry.entry_data['side_effects']
            
            elif entry_type == "product":
                if entry.entry_data.get('category'):
                    result["category"] = entry.entry_data['category']
                if entry.entry_data.get('subcategory'):
                    result["subcategory"] = entry.entry_data['subcategory']
                if entry.entry_data.get('price') is not None:
                    result["price"] = entry.entry_data['price']
                if entry.entry_data.get('in_stock') is not None:
                    result["in_stock"] = entry.entry_data['in_stock']
                if entry.entry_data.get('manufacturer'):
                    result["manufacturer"] = entry.entry_data['manufacturer']
                if entry.entry_data.get('model_number'):
                    result["model_number"] = entry.entry_data['model_number']
                if entry.entry_data.get('features'):
                    result["features"] = entry.entry_data['features']
                if entry.entry_data.get('warranty'):
                    result["warranty"] = entry.entry_data['warranty']
            
            elif entry_type == "department":
                if entry.entry_data.get('department_function'):
                    result["department_function"] = entry.entry_data['department_function']
                if entry.entry_data.get('manager_name'):
                    result["manager"] = entry.entry_data['manager_name']
                if entry.entry_data.get('staff_count') is not None:
                    result["staff_count"] = entry.entry_data['staff_count']
                if entry.entry_data.get('budget'):
                    result["budget"] = entry.entry_data['budget']
                if entry.entry_data.get('key_responsibilities'):
                    result["responsibilities"] = entry.entry_data['key_responsibilities']
            
            elif entry_type == "service":
                if entry.entry_data.get('service_type'):
                    result["service_type"] = entry.entry_data['service_type']
                if entry.entry_data.get('service_category'):
                    result["category"] = entry.entry_data['service_category']
                if entry.entry_data.get('duration'):
                    result["duration"] = entry.entry_data['duration']
                if entry.entry_data.get('cost'):
                    result["cost"] = entry.entry_data['cost']
                if entry.entry_data.get('insurance_accepted'):
                    result["insurance_accepted"] = entry.entry_data['insurance_accepted']
                if entry.entry_data.get('preparation_required') is not None:
                    result["preparation_required"] = entry.entry_data['preparation_required']
                if entry.entry_data.get('preparation_instructions'):
                    result["preparation"] = entry.entry_data['preparation_instructions']
                if entry.entry_data.get('recovery_time'):
                    result["recovery_time"] = entry.entry_data['recovery_time']
            
            elif entry_type == "location":
                if entry.entry_data.get('location_type'):
                    result["location_type"] = entry.entry_data['location_type']
                if entry.entry_data.get('building_name'):
                    result["building"] = entry.entry_data['building_name']
                if entry.entry_data.get('floor'):
                    result["floor"] = entry.entry_data['floor']
                if entry.entry_data.get('room_number'):
                    result["room"] = entry.entry_data['room_number']
                if entry.entry_data.get('directions'):
                    result["directions"] = entry.entry_data['directions']
                if entry.entry_data.get('parking_info'):
                    result["parking"] = entry.entry_data['parking_info']
                if entry.entry_data.get('accessibility_features'):
                    result["accessibility"] = entry.entry_data['accessibility_features']
                if entry.entry_data.get('hours'):
                    result["hours"] = entry.entry_data['hours']
            
            elif entry_type == "faq":
                if entry.entry_data.get('question'):
                    result["question"] = entry.entry_data['question']
                if entry.entry_data.get('answer'):
                    result["answer"] = entry.entry_data['answer']
                if entry.entry_data.get('category'):
                    result["category"] = entry.entry_data['category']
                if entry.entry_data.get('related_links'):
                    result["related_links"] = entry.entry_data['related_links']
            
            elif entry_type == "cross_sell":
                if entry.entry_data.get('primary_item'):
                    result["primary_item"] = entry.entry_data['primary_item']
                if entry.entry_data.get('suggested_item'):
                    result["suggested_item"] = entry.entry_data['suggested_item']
                if entry.entry_data.get('relationship'):
                    result["relationship"] = entry.entry_data['relationship']
                if entry.entry_data.get('reason'):
                    result["reason"] = entry.entry_data['reason']
                if entry.entry_data.get('bundle_discount'):
                    result["bundle_discount"] = entry.entry_data['bundle_discount']
                if entry.entry_data.get('frequently_bought_together') is not None:
                    result["frequently_bought_together"] = entry.entry_data['frequently_bought_together']
            
            elif entry_type == "up_sell":
                if entry.entry_data.get('base_item'):
                    result["base_item"] = entry.entry_data['base_item']
                if entry.entry_data.get('premium_item'):
                    result["premium_item"] = entry.entry_data['premium_item']
                if entry.entry_data.get('additional_features'):
                    result["additional_features"] = entry.entry_data['additional_features']
                if entry.entry_data.get('price_difference'):
                    result["price_difference"] = entry.entry_data['price_difference']
                if entry.entry_data.get('value_proposition'):
                    result["value_proposition"] = entry.entry_data['value_proposition']
                if entry.entry_data.get('benefits'):
                    result["benefits"] = entry.entry_data['benefits']
            
            elif entry_type == "competitive_sell":
                if entry.entry_data.get('competitor_product'):
                    result["competitor_product"] = entry.entry_data['competitor_product']
                if entry.entry_data.get('our_product'):
                    result["our_product"] = entry.entry_data['our_product']
                if entry.entry_data.get('differentiators'):
                    result["differentiators"] = entry.entry_data['differentiators']
                if entry.entry_data.get('price_comparison'):
                    result["price_comparison"] = entry.entry_data['price_comparison']
                if entry.entry_data.get('value_proposition'):
                    result["value_proposition"] = entry.entry_data['value_proposition']
                if entry.entry_data.get('certifications'):
                    result["certifications"] = entry.entry_data['certifications']
            
            elif entry_type == "classes":
                # Event identification
                if entry.entry_data.get('event_type'):
                    result["event_type"] = entry.entry_data['event_type']
                if entry.entry_data.get('program_name'):
                    result["program_name"] = entry.entry_data['program_name']
                
                # Scheduling
                if entry.entry_data.get('start_date'):
                    result["start_date"] = entry.entry_data['start_date']
                if entry.entry_data.get('end_date'):
                    result["end_date"] = entry.entry_data['end_date']
                if entry.entry_data.get('days_of_week'):
                    result["days_of_week"] = entry.entry_data['days_of_week']
                if entry.entry_data.get('time_of_day'):
                    result["time"] = entry.entry_data['time_of_day']
                if entry.entry_data.get('duration'):
                    result["duration"] = entry.entry_data['duration']
                if entry.entry_data.get('timezone'):
                    result["timezone"] = entry.entry_data['timezone']
                if entry.entry_data.get('session_count') is not None:
                    result["session_count"] = entry.entry_data['session_count']
                
                # Cost
                if entry.entry_data.get('cost_type'):
                    result["cost_type"] = entry.entry_data['cost_type']
                if entry.entry_data.get('price') is not None:
                    result["price"] = entry.entry_data['price']
                if entry.entry_data.get('early_bird_price') is not None:
                    result["early_bird_price"] = entry.entry_data['early_bird_price']
                if entry.entry_data.get('registration_fee') is not None:
                    result["registration_fee"] = entry.entry_data['registration_fee']
                if entry.entry_data.get('payment_required') is not None:
                    result["payment_required"] = entry.entry_data['payment_required']
                
                # Logistics
                if entry.entry_data.get('instructor_name'):
                    result["instructor"] = entry.entry_data['instructor_name']
                if entry.entry_data.get('delivery_format'):
                    result["format"] = entry.entry_data['delivery_format']
                if entry.entry_data.get('venue'):
                    result["venue"] = entry.entry_data['venue']
                if entry.entry_data.get('capacity') is not None:
                    result["capacity"] = entry.entry_data['capacity']
                if entry.entry_data.get('registration_required') is not None:
                    result["registration_required"] = entry.entry_data['registration_required']
                if entry.entry_data.get('registration_deadline'):
                    result["registration_deadline"] = entry.entry_data['registration_deadline']
                if entry.entry_data.get('enrollment_status'):
                    result["enrollment_status"] = entry.entry_data['enrollment_status']
                
                # Content
                if entry.entry_data.get('description'):
                    result["description"] = entry.entry_data['description']
                if entry.entry_data.get('target_audience'):
                    result["target_audience"] = entry.entry_data['target_audience']
                if entry.entry_data.get('prerequisites'):
                    result["prerequisites"] = entry.entry_data['prerequisites']
                if entry.entry_data.get('learning_objectives'):
                    result["learning_objectives"] = entry.entry_data['learning_objectives']
                if entry.entry_data.get('materials_provided'):
                    result["materials_provided"] = entry.entry_data['materials_provided']
                if entry.entry_data.get('materials_required'):
                    result["materials_required"] = entry.entry_data['materials_required']
                if entry.entry_data.get('certificate_offered') is not None:
                    result["certificate_offered"] = entry.entry_data['certificate_offered']
                if entry.entry_data.get('continuing_education_credits'):
                    result["ce_credits"] = entry.entry_data['continuing_education_credits']
            
            results.append(result)
        
        return json.dumps({"entries": results, "total": len(results)}, indent=2)

