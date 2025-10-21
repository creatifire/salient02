"""
Base tool classes and utilities for Pydantic AI agents.

This module provides the foundation classes for agent tools, including
error handling, usage tracking, authentication, and result standardization.

Key Classes:
- BaseTool: Abstract base class for all agent tools
- BaseToolOutput: Standardized tool output format
- ToolError: Custom exception for tool execution errors
- ToolRegistry: Registry for available tools (Phase 3+)

Design Principles:
- Consistent error handling across all tools
- Usage tracking and cost monitoring
- Authentication and authorization support
- Structured outputs with validation
- Integration with Pydantic AI tool decorators
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""



from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field

from .types import ToolResult
from .dependencies import BaseDependencies


class ToolError(Exception):
    """Custom exception for tool execution errors."""
    
    def __init__(
        self, 
        message: str, 
        tool_name: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.tool_name = tool_name
        self.error_code = error_code
        self.details = details or {}
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class BaseToolOutput(BaseModel):
    """Standardized output format for agent tools."""
    
    result: Any = Field(description="The main tool execution result")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )
    
    def to_tool_result(self, tool_name: str, execution_time_ms: float) -> ToolResult:
        """Convert to standard ToolResult format."""
        return ToolResult(
            tool_name=tool_name,
            success=True,
            result=self.result,
            execution_time_ms=execution_time_ms,
            metadata=self.metadata
        )


DepsType = TypeVar('DepsType', bound=BaseDependencies)


class BaseTool(ABC):
    """
    Abstract base class for all agent tools.
    
    Provides common functionality including:
    - Error handling and logging
    - Execution time tracking  
    - Authentication and authorization
    - Usage tracking for cost monitoring
    - Structured output formatting
    
    Subclasses should implement the _execute method with their specific logic.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usage_stats = {
            "total_calls": 0,
            "total_errors": 0,
            "total_execution_time_ms": 0.0,
        }
    
    @abstractmethod
    async def _execute(self, deps: DepsType, **kwargs) -> BaseToolOutput:
        """
        Execute the tool with the given dependencies and parameters.
        
        Args:
            deps: Dependency injection context
            **kwargs: Tool-specific parameters
            
        Returns:
            BaseToolOutput with the execution result
            
        Raises:
            ToolError: If execution fails
        """
        pass
    
    async def execute(self, deps: DepsType, **kwargs) -> ToolResult:
        """
        Execute the tool with error handling and usage tracking.
        
        Args:
            deps: Dependency injection context
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution outcome
        """
        start_time = time.time()
        
        try:
            # Pre-execution validation and setup
            await self._pre_execute_hook(deps, **kwargs)
            
            # Execute the tool
            output = await self._execute(deps, **kwargs)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Update usage statistics
            self.usage_stats["total_calls"] += 1
            self.usage_stats["total_execution_time_ms"] += execution_time_ms
            
            # Post-execution cleanup and tracking
            await self._post_execute_hook(deps, output, execution_time_ms)
            
            # Return standardized result
            return output.to_tool_result(self.name, execution_time_ms)
            
        except ToolError as e:
            # Handle tool-specific errors
            execution_time_ms = (time.time() - start_time) * 1000
            self.usage_stats["total_errors"] += 1
            
            await self._error_hook(deps, e, execution_time_ms)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error_message=e.message,
                execution_time_ms=execution_time_ms,
                metadata={
                    "error_code": e.error_code,
                    "error_details": e.details,
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            execution_time_ms = (time.time() - start_time) * 1000
            self.usage_stats["total_errors"] += 1
            
            tool_error = ToolError(
                message=f"Unexpected error: {str(e)}",
                tool_name=self.name,
                error_code="UNEXPECTED_ERROR",
                details={"exception_type": type(e).__name__}
            )
            
            await self._error_hook(deps, tool_error, execution_time_ms)
            
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None, 
                error_message=tool_error.message,
                execution_time_ms=execution_time_ms,
                metadata=tool_error.details
            )
    
    async def _pre_execute_hook(self, deps: DepsType, **kwargs) -> None:
        """
        Pre-execution hook for validation and setup.
        
        Override in subclasses for:
        - Parameter validation
        - Authentication checks
        - Resource limit validation
        - Setup of external connections
        """
        pass
    
    async def _post_execute_hook(
        self, 
        deps: DepsType, 
        output: BaseToolOutput,
        execution_time_ms: float
    ) -> None:
        """
        Post-execution hook for cleanup and tracking.
        
        Override in subclasses for:
        - Usage tracking and cost monitoring
        - Result logging and audit trails
        - Cleanup of external connections
        - Performance monitoring
        """
        pass
    
    async def _error_hook(
        self, 
        deps: DepsType, 
        error: ToolError,
        execution_time_ms: float
    ) -> None:
        """
        Error handling hook for logging and monitoring.
        
        Override in subclasses for:
        - Error logging and alerting
        - Error rate monitoring
        - Fallback strategy execution
        - Error reporting to external systems
        """
        # TODO: Integrate with existing logging system (loguru)
        print(f"Tool {self.name} error: {error.message}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for this tool."""
        avg_execution_time = 0.0
        if self.usage_stats["total_calls"] > 0:
            avg_execution_time = (
                self.usage_stats["total_execution_time_ms"] / 
                self.usage_stats["total_calls"]
            )
        
        return {
            **self.usage_stats,
            "average_execution_time_ms": avg_execution_time,
            "error_rate": (
                self.usage_stats["total_errors"] / max(1, self.usage_stats["total_calls"])
            ),
        }
