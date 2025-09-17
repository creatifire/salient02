"""
Cascade monitoring and audit trail system.

Provides comprehensive logging, performance monitoring, and debugging capabilities
for the configuration cascade system.

CHUNK 0017-004-002-03: Enhanced cascade logging and monitoring
"""

import time
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from loguru import logger


@dataclass
class CascadeAttempt:
    """Records a single cascade source attempt."""
    source: str
    success: bool
    value: Optional[Any] = None
    error: Optional[str] = None
    config_file_path: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class CascadeAuditTrail:
    """Comprehensive audit trail for cascade decisions."""
    agent_name: str
    parameter: str
    attempts: List[CascadeAttempt] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    successful_source: Optional[str] = None
    final_value: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize audit trail timing."""
        self.start_time = time.perf_counter()
    
    def attempt_source(self, source: str, config_file_path: Optional[str] = None) -> 'CascadeSourceContext':
        """Create a context manager for tracking a cascade source attempt."""
        return CascadeSourceContext(self, source, config_file_path)
    
    def record_attempt(self, attempt: CascadeAttempt):
        """Record a cascade attempt."""
        self.attempts.append(attempt)
        
        if attempt.success:
            self.successful_source = attempt.source
            self.final_value = attempt.value
    
    def finalize_and_log(self):
        """Finalize the audit trail and log comprehensive results."""
        self.end_time = time.perf_counter()
        total_duration_ms = (self.end_time - self.start_time) * 1000 if self.start_time else 0
        
        # Build comprehensive audit log
        audit_log = {
            "event": "cascade_decision_audit",
            "agent_name": self.agent_name,
            "parameter": self.parameter,
            "successful_source": self.successful_source,
            "final_value": self.final_value,
            "total_duration_ms": round(total_duration_ms, 2),
            "timestamp": datetime.now(UTC).isoformat(),
            "attempts": [
                {
                    "source": attempt.source,
                    "success": attempt.success,
                    "value": attempt.value if attempt.success else None,
                    "error": attempt.error,
                    "config_file_path": attempt.config_file_path,
                    "duration_ms": attempt.duration_ms,
                } for attempt in self.attempts
            ],
            "cascade_summary": {
                "attempted_sources": [attempt.source for attempt in self.attempts],
                "failed_sources": [attempt.source for attempt in self.attempts if not attempt.success],
                "fallback_used": self.successful_source == "hardcoded_fallback",
                "performance": {
                    "total_attempts": len(self.attempts),
                    "total_duration_ms": round(total_duration_ms, 2),
                    "average_attempt_ms": round(total_duration_ms / len(self.attempts), 2) if self.attempts else 0
                }
            },
            "troubleshooting": self._generate_troubleshooting_guide()
        }
        
        # Log with appropriate level based on outcome
        if self.successful_source == "hardcoded_fallback":
            logger.warning(audit_log)  # Warn if falling back to hardcoded values
        elif any(not attempt.success for attempt in self.attempts):
            logger.info(audit_log)  # Info if some sources failed but cascade worked
        else:
            logger.debug(audit_log)  # Debug for successful first-try cascades
    
    def _generate_troubleshooting_guide(self) -> Dict[str, str]:
        """Generate contextual troubleshooting guidance."""
        guide = {}
        
        if self.successful_source == "hardcoded_fallback":
            guide["issue"] = f"Using hardcoded fallback for {self.parameter}"
            guide["check_agent_config"] = f"Verify agent config file exists with {self.parameter} setting"
            guide["check_global_config"] = f"Verify app.yaml has {self.parameter} in appropriate section"
            guide["expected_path"] = f"backend/config/agent_configs/{self.agent_name}/config.yaml"
        
        elif self.successful_source == "global_config":
            guide["status"] = f"Using global config for {self.parameter}"
            guide["optimization"] = f"Consider adding {self.parameter} to agent-specific config for customization"
        
        elif self.successful_source == "agent_config":
            guide["status"] = f"Using agent-specific config for {self.parameter} (optimal)"
        
        # Add failure-specific guidance
        failed_attempts = [attempt for attempt in self.attempts if not attempt.success]
        if failed_attempts:
            guide["failed_sources"] = {
                attempt.source: attempt.error or "Source unavailable"
                for attempt in failed_attempts
            }
        
        return guide


class CascadeSourceContext:
    """Context manager for tracking individual cascade source attempts."""
    
    def __init__(self, audit_trail: CascadeAuditTrail, source: str, config_file_path: Optional[str] = None):
        self.audit_trail = audit_trail
        self.source = source
        self.config_file_path = config_file_path
        self.start_time: Optional[float] = None
        self.attempt: Optional[CascadeAttempt] = None
    
    def __enter__(self) -> 'CascadeSourceContext':
        """Start timing the cascade attempt."""
        self.start_time = time.perf_counter()
        self.attempt = CascadeAttempt(
            source=self.source,
            success=False,
            config_file_path=self.config_file_path,
            timestamp=datetime.now(UTC)
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finalize the cascade attempt."""
        if self.start_time and self.attempt:
            end_time = time.perf_counter()
            self.attempt.duration_ms = round((end_time - self.start_time) * 1000, 2)
            
            if exc_type:
                self.attempt.error = str(exc_val)
                self.attempt.success = False
            
            self.audit_trail.record_attempt(self.attempt)
        
        # Don't suppress exceptions
        return False
    
    def success(self, value: Any) -> Any:
        """Mark the attempt as successful and return the value."""
        if self.attempt:
            self.attempt.success = True
            self.attempt.value = value
        return value
    
    def failure(self, error: str) -> None:
        """Mark the attempt as failed with an error message."""
        if self.attempt:
            self.attempt.success = False
            self.attempt.error = error


class CascadeMetrics:
    """Cascade performance and usage metrics."""
    
    @staticmethod
    def log_cascade_performance(agent_name: str, parameter: str, source: str, duration_ms: float):
        """Log cascade performance metrics."""
        logger.debug({
            "event": "cascade_performance_metric",
            "agent_name": agent_name,
            "parameter": parameter,
            "source": source,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    @staticmethod
    def log_fallback_usage(agent_name: str, parameter: str, reason: str):
        """Log fallback usage for monitoring configuration health."""
        logger.warning({
            "event": "cascade_fallback_usage",
            "agent_name": agent_name,
            "parameter": parameter,
            "reason": reason,
            "alert": "Configuration may need attention",
            "timestamp": datetime.now(UTC).isoformat(),
            "recommended_action": f"Check agent config for {agent_name} parameter {parameter}"
        })
    
    @staticmethod
    def log_cascade_health_check(agent_name: str, parameters_checked: List[str], health_status: str):
        """Log overall cascade system health."""
        logger.info({
            "event": "cascade_health_check",
            "agent_name": agent_name,
            "parameters_checked": parameters_checked,
            "health_status": health_status,
            "timestamp": datetime.now(UTC).isoformat()
        })


def enhanced_cascade_wrapper(parameter_name: str):
    """
    Decorator to add enhanced logging and monitoring to cascade functions.
    
    Usage:
        @enhanced_cascade_wrapper("history_limit")
        async def get_agent_history_limit(agent_name: str) -> int:
            # Implementation with audit trail
    """
    def decorator(func):
        async def wrapper(agent_name: str, *args, **kwargs):
            audit_trail = CascadeAuditTrail(agent_name, parameter_name)
            
            try:
                result = await func(agent_name, audit_trail, *args, **kwargs)
                return result
            finally:
                audit_trail.finalize_and_log()
        
        return wrapper
    return decorator
