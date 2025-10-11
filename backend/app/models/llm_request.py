"""
LLMRequest model for comprehensive LLM usage tracking and cost analysis.

This model captures detailed information about every LLM API call for:
- Cost tracking and budget management across sessions
- Performance monitoring and latency analysis
- Debugging failed requests and response quality issues
- Usage analytics and reporting for optimization
- Token consumption patterns and efficiency metrics

Based on datamodel specification in memorybank/architecture/datamodel.md
"""

import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from . import Base


class LLMRequest(Base):
    """
    LLM usage tracking for cost analysis and request monitoring.
    
    Key Features:
    - provider: LLM provider (e.g., 'openrouter')
    - model: Model identifier for cost calculation
    - request_body/response_body: Sanitized request/response data
    - Token usage: prompt_tokens, completion_tokens, total_tokens
    - Cost tracking: unit costs and computed total cost
    - Performance: latency_ms for monitoring
    
    Usage:  
    - Cost analysis: Track spending per session/user
    - Performance monitoring: Identify slow requests
    - Usage analytics: Model performance comparison
    - Billing: Customer usage reporting (future multi-tenant)
    """
    
    __tablename__ = "llm_requests"
    
    # Primary key - GUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to sessions table
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Multi-tenant: agent instance that made this request
    agent_instance_id = Column(UUID(as_uuid=True), ForeignKey("agent_instances.id"), nullable=True, index=True)
    
    # LLM provider identifier
    provider = Column(String(50), nullable=False)
    
    # Model identifier (e.g., 'openai/gpt-4', 'anthropic/claude-3-sonnet')
    model = Column(String(100), nullable=False)
    
    # Sanitized request payload (remove sensitive data, keep structure)
    # Example: {"messages": [{"role": "user", "content": "[REDACTED]"}], "temperature": 0.7}
    request_body = Column(JSONB, nullable=True)
    
    # Response metadata (headers, usage stats, etc.)
    # Example: {"usage": {...}, "model": "...", "headers": {"x-ratelimit-remaining": "99"}}
    response_body = Column(JSONB, nullable=True)
    
    # Token usage tracking
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True) 
    total_tokens = Column(Integer, nullable=True)
    
    # Cost tracking - actual costs from LLM provider (e.g., OpenRouter)
    # Stored as NUMERIC(12, 8) for high precision (handles costs like $0.0000408)
    prompt_cost = Column(Numeric(12, 8), nullable=True)  # Cost for prompt/input tokens (e.g., 0.0000408)
    completion_cost = Column(Numeric(12, 8), nullable=True)  # Cost for completion/output tokens (e.g., 0.003646)
    total_cost = Column(Numeric(12, 8), nullable=True)  # Total cost (prompt + completion) (e.g., 0.0036868)
    
    # Performance tracking
    latency_ms = Column(Integer, nullable=True)  # Request duration in milliseconds
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationship back to session
    session = relationship("Session", back_populates="llm_requests")
    
    def __repr__(self) -> str:
        return f"<LLMRequest(id={self.id}, session_id={self.session_id}, provider={self.provider}, model={self.model}, cost={self.computed_cost})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.""" 
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "agent_instance_id": str(self.agent_instance_id) if self.agent_instance_id else None,
            "provider": self.provider,
            "model": self.model,
            "request_body": self.request_body,
            "response_body": self.response_body,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": float(self.prompt_cost) if self.prompt_cost else None,
            "completion_cost": float(self.completion_cost) if self.completion_cost else None,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
