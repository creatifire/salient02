# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Directory Service for querying multi-purpose directory entries.

Provides database query layer for searching directory entries (doctors, drugs, products, etc.)
with multi-tenant access control and flexible filtering (name, tags, JSONB fields).
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.directory import DirectoryList, DirectoryEntry
import logging

logger = logging.getLogger(__name__)


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
        limit: int = 10
    ) -> List[DirectoryEntry]:
        """
        Search directory entries with flexible filters.
        
        Supports:
        - Name search (partial match, case-insensitive)
        - Tag filtering (array overlap, e.g., languages)
        - JSONB field filtering (department, specialty, drug_class, etc.)
        
        Multi-tenant isolation enforced via accessible_list_ids parameter.
        
        Args:
            session: Database session
            accessible_list_ids: List UUIDs to search within (pre-filtered by account)
            name_query: Partial name match (case-insensitive)
            tags: List of tags to filter by (array overlap)
            jsonb_filters: Dict of JSONB field filters (e.g., {"department": "Cardiology"})
            limit: Maximum number of results (default: 10)
            
        Returns:
            List of DirectoryEntry instances matching filters
            
        Examples:
            # Search for cardiologists
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                jsonb_filters={"specialty": "cardiology"}
            )
            
            # Search for Spanish-speaking doctors named "Smith"
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                name_query="smith",
                tags=["Spanish"]
            )
            
            # Search for products in Electronics category
            entries = await DirectoryService.search(
                session,
                accessible_list_ids=[list_id],
                jsonb_filters={"category": "Electronics"}
            )
        """
        if not accessible_list_ids:
            logger.warning("Search called with no accessible lists")
            return []
        
        # Base query: filter by accessible lists
        query = select(DirectoryEntry).where(
            DirectoryEntry.directory_list_id.in_(accessible_list_ids)
        )
        
        # Name search (partial match, case-insensitive)
        if name_query:
            query = query.where(DirectoryEntry.name.ilike(f"%{name_query}%"))
        
        # Tag filtering (array overlap)
        if tags:
            query = query.where(DirectoryEntry.tags.overlap(tags))
        
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
            f"(name={name_query}, tags={tags}, filters={jsonb_filters})"
        )
        
        return entries

