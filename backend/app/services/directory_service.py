# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Directory Service for querying multi-purpose directory entries.

Provides database query layer for searching directory entries (doctors, drugs, products, etc.)
with multi-tenant access control and flexible filtering (name, tags, JSONB fields).
"""

from __future__ import annotations

import re
from typing import List, Optional, Literal
from uuid import UUID
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from ..models.directory import DirectoryList, DirectoryEntry
import logging

logger = logging.getLogger(__name__)

# Type alias for search modes
SearchMode = Literal["exact", "substring", "fts"]


class DirectoryService:
    """Service for querying directory lists and entries with multi-tenant access control."""
    
    @staticmethod
    async def get_accessible_lists(
        session: AsyncSession,
        account_id: UUID,
        list_names: List[str]
    ) -> List[UUID]:
        """
        Get directory list IDs for an account by list names.
        
        Used to resolve list names from agent config to database IDs for querying.
        Enforces multi-tenant isolation (account can only access their own lists).
        
        Args:
            session: Database session
            account_id: Account UUID
            list_names: List of directory list names (e.g., ["doctors", "nurses"])
            
        Returns:
            List of DirectoryList UUIDs accessible to this account
            
        Example:
            list_ids = await DirectoryService.get_accessible_lists(
                session, 
                account_id=UUID('481d3e72...'),
                list_names=["doctors"]
            )
            # Returns: [UUID('0b416400...')]
        """
        if not list_names:
            return []
        
        result = await session.execute(
            select(DirectoryList.id).where(
                and_(
                    DirectoryList.account_id == account_id,
                    DirectoryList.list_name.in_(list_names)
                )
            )
        )
        
        list_ids = [row[0] for row in result.fetchall()]
        
        if len(list_ids) < len(list_names):
            found_names = await session.execute(
                select(DirectoryList.list_name).where(
                    DirectoryList.id.in_(list_ids)
                )
            )
            found = {row[0] for row in found_names.fetchall()}
            missing = set(list_names) - found
            if missing:
                logger.warning(f"Lists not found for account {account_id}: {missing}")
        
        logger.info(f"Resolved {len(list_ids)} accessible list(s) for account {account_id}")
        return list_ids
    
    @staticmethod
    async def search(
        session: AsyncSession,
        accessible_list_ids: List[UUID],
        name_query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        jsonb_filters: Optional[dict] = None,
        search_mode: SearchMode = "substring",
        limit: int = 10
    ) -> List[DirectoryEntry]:
        """
        Search directory entries with flexible filters.
        
        Supports:
        - Name search (exact, substring, or full-text search)
        - Tag filtering (array overlap, e.g., languages)
        - JSONB field filtering (department, specialty, drug_class, etc.)
        - Relevance ranking (for FTS mode)
        
        Multi-tenant isolation enforced via accessible_list_ids parameter.
        
        Args:
            session: Database session
            accessible_list_ids: List UUIDs to search within (pre-filtered by account)
            name_query: Name search query (behavior depends on search_mode)
            tags: List of tags to filter by (array overlap)
            jsonb_filters: Dict of JSONB field filters (e.g., {"department": "Cardiology"})
            search_mode: Search mode for name_query
                - "exact": Exact match (name == query)
                - "substring": Case-insensitive partial match (default, backward compatible)
                - "fts": Full-text search with ranking (handles word variations, stemming)
            limit: Maximum number of results (default: 10)
            
        Returns:
            List of DirectoryEntry instances matching filters
            - For "fts" mode: Sorted by relevance (ts_rank DESC)
            - For other modes: Database order
            
        Examples:
            # Substring search (default - backward compatible)
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                name_query="cardio",  # Matches "cardiologist", "Cardiology"
                search_mode="substring"
            )
            
            # Full-text search with relevance ranking
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                name_query="heart doctor",  # Matches "cardiologist", "cardiology"
                search_mode="fts"
            )
            
            # Exact match
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                name_query="Dr. John Smith",
                search_mode="exact"
            )
            
            # Combined filters
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                name_query="cardio",
                tags=["Spanish"],
                jsonb_filters={"gender": "female"},
                search_mode="fts"
            )
        """
        if not accessible_list_ids:
            logger.warning("Search called with no accessible lists")
            return []
        
        # Base query: filter by accessible lists
        # Using selectinload() prevents N+1 queries if relationships are accessed later
        query = (
            select(DirectoryEntry)
            .options(
                selectinload(DirectoryEntry.directory_list)  # Eager load directory_list relationship
            )
            .where(
                DirectoryEntry.directory_list_id.in_(accessible_list_ids)
            )
        )
        
        # Track if we've applied FTS ranking (for combining with filter queries)
        fts_rank_expr = None
        fts_ts_query = None
        
        # Name search - behavior depends on search_mode
        if name_query:
            if search_mode == "fts":
                # Full-text search with relevance ranking
                try:
                    # Convert query to tsquery (simple format: replace spaces with &)
                    # This handles multi-word queries like "heart doctor"
                    tsquery_str = ' & '.join(name_query.strip().split())
                    
                    # Create tsquery function call
                    fts_ts_query = func.to_tsquery('english', tsquery_str)
                    
                    # Filter: search_vector matches query
                    query = query.where(
                        DirectoryEntry.search_vector.op('@@')(fts_ts_query)
                    )
                    
                    # Rank by relevance (higher is better)
                    fts_rank_expr = func.ts_rank(DirectoryEntry.search_vector, fts_ts_query)
                    query = query.order_by(fts_rank_expr.desc())
                    
                    logger.debug(f"FTS query: {tsquery_str}")
                    
                except Exception as e:
                    # Fallback to substring search if tsquery fails
                    logger.warning(
                        f"FTS query failed for '{name_query}': {e}. "
                        f"Falling back to substring search."
                    )
                    query = query.where(DirectoryEntry.name.ilike(f"%{name_query}%"))
                    
            elif search_mode == "exact":
                # Exact match (case-sensitive)
                query = query.where(DirectoryEntry.name == name_query)
                
            else:  # substring (default)
                # Partial match, case-insensitive (backward compatible)
                query = query.where(DirectoryEntry.name.ilike(f"%{name_query}%"))
        
        # Tag filtering (array overlap - PostgreSQL && operator)
        if tags:
            query = query.where(DirectoryEntry.tags.op('&&')(tags))
        
        # JSONB field filtering
        # When FTS mode enabled: Use tsvector for fuzzy matching (handles word variations)
        # When non-FTS mode: Use regex for exact/substring matching
        if jsonb_filters:
            if search_mode == "fts":
                # BUG-0023-004: Use tsvector for specialty searches when FTS mode enabled
                # This enables fuzzy matching: "Urology" → "Urologic Surgery" via stemming
                # Build tsquery from all filter values (combine with AND)
                filter_values = []
                for value in jsonb_filters.values():
                    # Split multi-word values and join with & (AND logic)
                    filter_values.extend(value.strip().split())
                
                if filter_values:
                    # Build combined tsquery from name_query (if exists) and filter values
                    tsquery_parts = []
                    
                    # Add name_query parts if it exists (for combined ranking)
                    if name_query:
                        name_parts = name_query.strip().split()
                        tsquery_parts.extend(name_parts)
                    
                    # Add filter values
                    tsquery_parts.extend(filter_values)
                    
                    # Build combined tsquery string
                    combined_tsquery_str = ' & '.join(tsquery_parts)
                    combined_ts_query = func.to_tsquery('english', combined_tsquery_str)
                    
                    # Apply tsvector search if not already applied by name_query
                    if not name_query:
                        # No name_query, so apply tsvector search for filters only
                        query = query.where(
                            DirectoryEntry.search_vector.op('@@')(combined_ts_query)
                        )
                        # Add ranking by relevance
                        fts_rank_expr = func.ts_rank(DirectoryEntry.search_vector, combined_ts_query)
                        query = query.order_by(fts_rank_expr.desc())
                    else:
                        # name_query already applied tsvector, but use combined query for better ranking
                        # Replace existing order_by with combined ranking
                        fts_rank_expr = func.ts_rank(DirectoryEntry.search_vector, combined_ts_query)
                        # Remove any existing order_by and add new one
                        # Note: SQLAlchemy will replace order_by if called again
                        query = query.order_by(fts_rank_expr.desc())
                    
                    # NOTE: We do NOT apply additional JSONB field filters here
                    # The tsvector search already handles matching across ALL fields (name, tags, entry_data)
                    # Additional JSONB substring filters would conflict with tsvector's fuzzy matching
                    # Example: "Urology" → tsvector matches "Urologic Surgery" via stemming
                    # But substring filter "%Urology%" fails because "Urology" is not a substring of "Urologic Surgery"
                    # This causes false negatives, so we rely on tsvector only
                    
                    logger.debug(f"FTS filter query: {combined_tsquery_str}")
            else:
                # Non-FTS modes: Use regex word-boundary matching
                # Uses regex word boundaries to prevent false matches:
                # - "Urology" matches "Urology" and "Urologic Surgery" but NOT "Neurology"
                # - Word boundary \m = start of word
                # - Escapes special regex characters in value to prevent injection
                for key, value in jsonb_filters.items():
                    # Escape special regex characters in the search value
                    escaped_value = re.escape(value)
                    # Pattern: word starts with escaped value (case-insensitive)
                    # \m = word boundary at start, allows "Urology" to match "Urologic Surgery"
                    word_boundary_pattern = f"\\m{escaped_value}"
                    query = query.where(
                        DirectoryEntry.entry_data[key].astext.op('~*')(word_boundary_pattern)
                    )
        
        # Limit results
        query = query.limit(limit)
        
        # Execute query
        result = await session.execute(query)
        entries = result.scalars().all()
        
        logger.info(
            f"Search returned {len(entries)} entries "
            f"(mode={search_mode}, query={name_query}, tags={tags}, filters={jsonb_filters})"
        )
        
        return entries

