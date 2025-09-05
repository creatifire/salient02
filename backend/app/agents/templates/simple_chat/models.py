"""
Simple Chat Agent Response Models.

This module defines the ChatResponse Pydantic model for structured agent outputs.
Designed for basic conversational interactions without complex tool integration.

Key Features:
- Simple text-based response format
- Confidence scoring for response quality assessment  
- Extensible metadata for future enhancements
- Validation rules ensuring response quality
- JSON serialization support for API integration

Usage:
    response = ChatResponse(
        message="Hello! How can I help you today?",
        confidence=0.95,
        metadata={"model": "openai:gpt-4o", "tokens": 15}
    )
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class ChatResponse(BaseModel):
    """
    Simple structured response model for basic chat agent interactions.
    
    Focused on text-based conversations without complex tool integration,
    citations, or multi-modal content. Provides foundation for future
    enhancements while maintaining simplicity for basic use cases.
    
    Fields:
        message: Primary response content (required)
        confidence: Response quality confidence score 0.0-1.0 (optional)
        metadata: Additional response context and debugging info (optional)
        timestamp: Response generation timestamp (auto-generated)
        session_id: Session identifier for conversation tracking (optional)
        
    Example:
        response = ChatResponse(
            message="I can help you with questions about our products and services.",
            confidence=0.92,
            metadata={
                "model": "openai:gpt-4o",
                "temperature": 0.3,
                "tokens_used": 28,
                "response_time_ms": 1250
            }
        )
    """
    
    message: str = Field(
        description="Primary response message content",
        min_length=1,
        max_length=10000,
        example="I'd be happy to help you with that question!"
    )
    
    confidence: Optional[float] = Field(
        default=None,
        description="Response quality confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0,
        example=0.85
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response context, model info, and debugging data",
        example={
            "model": "openai:gpt-4o",
            "temperature": 0.3,
            "tokens_used": 42,
            "response_time_ms": 1180
        }
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response generation timestamp (UTC)",
        example="2024-12-25T14:30:00Z"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation tracking",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    @validator('message')
    def validate_message_content(cls, v):
        """Ensure message content is meaningful and properly formatted."""
        if not v.strip():
            raise ValueError("Message content cannot be empty or only whitespace")
        
        # Basic content quality checks
        if len(v.strip()) < 2:
            raise ValueError("Message content must be at least 2 characters")
        
        return v.strip()
    
    @validator('confidence')
    def validate_confidence_score(cls, v):
        """Ensure confidence score is within valid range."""
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
    
    @validator('metadata')
    def validate_metadata_structure(cls, v):
        """Ensure metadata follows expected patterns."""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Validate common metadata fields if present
        if 'model' in v and not isinstance(v['model'], str):
            raise ValueError("Metadata 'model' field must be a string")
        
        if 'tokens_used' in v and not isinstance(v['tokens_used'], int):
            raise ValueError("Metadata 'tokens_used' field must be an integer")
        
        if 'response_time_ms' in v and not isinstance(v['response_time_ms'], (int, float)):
            raise ValueError("Metadata 'response_time_ms' field must be a number")
        
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization and API responses.
        
        Returns:
            Dictionary representation of the ChatResponse
        """
        return {
            "message": self.message,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }
    
    def add_metadata(self, key: str, value: Any) -> ChatResponse:
        """
        Add metadata field and return new ChatResponse instance.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            New ChatResponse instance with updated metadata
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        
        return self.copy(update={"metadata": new_metadata})
    
    def with_session(self, session_id: str) -> ChatResponse:
        """
        Set session ID and return new ChatResponse instance.
        
        Args:
            session_id: Session identifier
            
        Returns:
            New ChatResponse instance with session ID set
        """
        return self.copy(update={"session_id": session_id})
    
    def is_confident(self, threshold: float = 0.8) -> bool:
        """
        Check if response meets confidence threshold.
        
        Args:
            threshold: Confidence threshold (default 0.8)
            
        Returns:
            True if confidence is above threshold or not set
        """
        if self.confidence is None:
            return True  # Assume confident if not specified
        return self.confidence >= threshold
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "message": "I'd be happy to help you with that question! What specific information are you looking for?",
                "confidence": 0.92,
                "metadata": {
                    "model": "openai:gpt-4o",
                    "temperature": 0.3,
                    "tokens_used": 35,
                    "response_time_ms": 1420
                },
                "timestamp": "2024-12-25T14:30:15.123456Z",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
