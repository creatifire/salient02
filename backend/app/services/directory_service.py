# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Directory Service for querying multi-purpose directory entries.

Provides database query layer for searching directory entries (doctors, drugs, products, etc.)
with multi-tenant access control and flexible filtering (name, tags, JSONB fields).
"""

from __future__ import annotations

from typing import List, Optional, Literal
from uuid import UUID
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
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
        query = select(DirectoryEntry).where(
            DirectoryEntry.directory_list_id.in_(accessible_list_ids)
        )
        
        # Name search - behavior depends on search_mode
        if name_query:
            if search_mode == "fts":
                # Full-text search with relevance ranking
                try:
                    # Convert query to tsquery (simple format: replace spaces with &)
                    # This handles multi-word queries like "heart doctor"
                    tsquery_str = ' & '.join(name_query.strip().split())
                    
                    # Create tsquery function call
                    ts_query = func.to_tsquery('english', tsquery_str)
                    
                    # Filter: search_vector matches query
                    query = query.where(
                        DirectoryEntry.search_vector.op('@@')(ts_query)
                    )
                    
                    # Rank by relevance (higher is better)
                    rank_expr = func.ts_rank(DirectoryEntry.search_vector, ts_query)
                    query = query.order_by(rank_expr.desc())
                    
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
        
        # JSONB field filtering (case-insensitive partial match)
        if jsonb_filters:
            for key, value in jsonb_filters.items():
                query = query.where(
                    DirectoryEntry.entry_data[key].astext.ilike(f"%{value}%")
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

