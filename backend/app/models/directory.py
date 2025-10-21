# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
SQLAlchemy models for the multi-purpose directory service.

Models:
    DirectoryList: Account-level collections (doctors, drugs, products, etc.)
    DirectoryEntry: Individual entries within directory lists
"""
from __future__ import annotations

from sqlalchemy import Column, String, ARRAY, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.database import Base
import uuid
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.account import Account


class DirectoryList(Base):
    """Directory list collection belonging to an account.
    
    Examples: doctors list, prescription_drugs list, product_catalog list
    Each list has an entry_type that defines the JSONB schema structure.
    """
    __tablename__ = "directory_lists"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("accounts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    list_name: Mapped[str] = mapped_column(String, nullable=False)
    list_description: Mapped[Optional[str]] = mapped_column(Text)
    entry_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    schema_file: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="directory_lists")
    entries: Mapped[List["DirectoryEntry"]] = relationship(
        "DirectoryEntry", 
        back_populates="directory_list", 
        cascade="all, delete-orphan"
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "list_name": self.list_name,
            "list_description": self.list_description,
            "entry_type": self.entry_type,
            "schema_file": self.schema_file,
            "entry_count": len(self.entries) if self.entries else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DirectoryEntry(Base):
    """Individual entry in a directory list.
    
    Examples:
    - Medical professional (doctor, nurse, therapist)
    - Pharmaceutical (prescription drug, OTC medication)
    - Product (electronics, furniture, etc.)
    - Consultant (expert, contractor)
    
    The entry_data JSONB field structure is defined by the schema_file 
    referenced in the parent DirectoryList.
    """
    __tablename__ = "directory_entries"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    directory_list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("directory_lists.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    contact_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    entry_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    directory_list: Mapped["DirectoryList"] = relationship("DirectoryList", back_populates="entries")
    
    def to_dict(self) -> dict:
        """Convert model to dictionary representation."""
        return {
            "id": str(self.id),
            "directory_list_id": str(self.directory_list_id),
            "name": self.name,
            "tags": self.tags,
            "contact_info": self.contact_info,
            "entry_data": self.entry_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

