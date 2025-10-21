"""
Agent Instance model for multi-tenant architecture.
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""


from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from . import Base


class AgentInstanceModel(Base):
    """
    Agent Instance model for multi-tenancy.
    
    Represents a configured instance of an agent type for a specific account.
    Database stores metadata; actual configuration lives in YAML files.
    
    Hybrid approach:
    - DB: Metadata (slugs, status, timestamps) for validation, discovery, tracking
    - Files: Configuration (model, tools, prompts) for flexibility
    """
    __tablename__ = "agent_instances"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    # Account relationship
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Instance identification
    instance_slug: Mapped[str] = mapped_column(String, nullable=False)
    agent_type: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="active", index=True)
    
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
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    # Relationships
    account = relationship("Account", back_populates="agent_instances")
    messages = relationship("Message", back_populates="agent_instance")
    
    # Unique constraint: (account_id, instance_slug) must be unique
    __table_args__ = (
        UniqueConstraint('account_id', 'instance_slug', name='uq_agent_instances_account_slug'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<AgentInstance(id={self.id}, "
            f"account_id={self.account_id}, "
            f"instance_slug='{self.instance_slug}', "
            f"agent_type='{self.agent_type}', "
            f"status='{self.status}')>"
        )
