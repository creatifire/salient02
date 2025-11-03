"""
Profile model for incremental customer profile data collection.

This model accumulates customer information gradually during chat interactions
without requiring upfront registration. Supports progressive profiling for
better user experience and sales qualification.

Key Capabilities:
- Contact information capture (name, email, phone, address)
- Interest tracking for products and services  
- Flexible preferences storage for custom attributes
- Automatic timestamp tracking for data freshness
- One-to-one relationship with chat sessions

Based on datamodel specification in memorybank/architecture/datamodel.md
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from . import Base


class Profile(Base):
    """
    Incremental customer profile data collection during chat interactions.
    
    Key Features:
    - All fields nullable: Data collected incrementally over multiple conversations
    - Contact info: customer_name, phone, email, address fields
    - Interest tracking: products_of_interest, services_of_interest as arrays
    - Flexible preferences: JSONB field for extensible customer data
    - One-to-one with session: Each session has at most one profile
    
    Usage:
    - Lead qualification: Collect contact information gradually  
    - Personalization: Tailor recommendations based on interests
    - Sales handoff: Provide complete customer context to sales team
    - CRM integration: Export profile data to external systems
    """
    
    __tablename__ = "profiles"
    
    # Primary key - GUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to sessions table (one-to-one relationship)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, unique=True, index=True)
    
    # Contact information - all nullable for incremental collection
    customer_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)  # Allow various phone formats
    email = Column(String(255), nullable=True, index=True)  # For email-based session linking
    
    # Address information - nullable for privacy and gradual collection
    address_street = Column(String(500), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(50), nullable=True)
    address_zip = Column(String(20), nullable=True)
    
    # Interest tracking - PostgreSQL arrays for multiple values
    # Examples: ["SmartFresh", "FreshCloud", "1-MCP"] 
    products_of_interest = Column(ARRAY(String), nullable=True)
    
    # Examples: ["Post-harvest consultation", "Quality monitoring", "Supply chain optimization"]
    services_of_interest = Column(ARRAY(String), nullable=True)
    
    # Flexible preference storage - JSONB for extensibility
    # Examples:
    # - {"company_size": "50-100 employees", "crops": ["apples", "pears"], "region": "Pacific Northwest"}
    # - {"budget_range": "$10k-50k", "timeline": "Q2 2024", "current_solutions": ["competitor_x"]}
    # - {"communication_preference": "email", "best_contact_time": "morning"}
    preferences = Column(JSONB, nullable=True)
    
    # Timestamp - updated whenever profile data changes
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationship back to session (one-to-one)
    session = relationship("Session", back_populates="profile")
    
    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, session_id={self.session_id}, customer_name={self.customer_name}, email={self.email})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email,
            "address_street": self.address_street,
            "address_city": self.address_city,
            "address_state": self.address_state,
            "address_zip": self.address_zip,
            "products_of_interest": list(self.products_of_interest) if self.products_of_interest else None,
            "services_of_interest": list(self.services_of_interest) if self.services_of_interest else None,
            "preferences": self.preferences,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
