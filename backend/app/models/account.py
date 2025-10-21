"""
Account model for multi-tenant architecture.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""


from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import Base


class Account(Base):
    """
    Account model for multi-tenancy.
    
    Each account represents a separate tenant with isolated agent instances,
    sessions, and data.
    """
    __tablename__ = "accounts"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    # Account identification
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Status and subscription
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active", index=True)
    subscription_tier: Mapped[str] = mapped_column(String, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    agent_instances = relationship("AgentInstanceModel", back_populates="account", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Account(id={self.id}, slug='{self.slug}', name='{self.name}', status='{self.status}')>"
