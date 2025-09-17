"""
Tests for enhanced cascade logging and monitoring system.

Tests for CHUNK 0017-004-002-03: Enhanced cascade logging and monitoring
Verifies comprehensive audit trails, performance monitoring, and troubleshooting guidance.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
import json
from datetime import datetime, UTC


class TestCascadeAuditTrail:
    """Test comprehensive cascade audit trail system."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cascade_logging_shows_source(self):
        """
        Verify logs indicate config source used with comprehensive details.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 1:
        Verify logs indicate config source used.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Mock agent config to return a value
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            with patch('app.agents.cascade_monitor.logger') as mock_logger:
                # Setup agent config mock
                mock_agent_config = MagicMock()
                mock_agent_config.context_management = {"history_limit": 75}
                mock_get_config.return_value = mock_agent_config

                # Call the function
                result = await get_agent_history_limit("test_agent")

                # Verify result
                assert result == 75

                # Verify comprehensive audit logging was called
                assert mock_logger.debug.called or mock_logger.info.called or mock_logger.warning.called
                
                # Get the log call arguments
                log_calls = mock_logger.debug.call_args_list + mock_logger.info.call_args_list + mock_logger.warning.call_args_list
                assert len(log_calls) > 0, "Expected at least one log call"
                
                # Find the cascade decision audit log
                audit_log = None
                for call in log_calls:
                    if call[0] and isinstance(call[0][0], dict):
                        log_data = call[0][0]
                        if log_data.get("event") == "cascade_decision_audit":
                            audit_log = log_data
                            break
                
                assert audit_log is not None, "Expected cascade_decision_audit log entry"
                
                # Verify comprehensive audit log structure
                assert audit_log["agent_name"] == "test_agent"
                assert audit_log["parameter"] == "history_limit"
                assert audit_log["successful_source"] == "agent_config"
                assert audit_log["final_value"] == 75
                assert "total_duration_ms" in audit_log
                assert "timestamp" in audit_log
                assert "attempts" in audit_log
                assert "cascade_summary" in audit_log
                assert "troubleshooting" in audit_log

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cascade_audit_trail(self):
        """
        Test comprehensive decision logging with multiple cascade attempts.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 2:
        Test comprehensive decision logging.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Mock to simulate agent config failure, then global config success
        with patch('app.agents.config_loader.get_agent_config') as mock_get_agent_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup mocks: agent config fails, global config succeeds
                    mock_get_agent_config.side_effect = Exception("Agent config not found")
                    mock_load_config.return_value = {"chat": {"history_limit": 30}}

                    # Call the function
                    result = await get_agent_history_limit("test_agent")

                    # Verify result uses global config
                    assert result == 30

                    # Get audit log
                    log_calls = mock_logger.debug.call_args_list + mock_logger.info.call_args_list + mock_logger.warning.call_args_list
                    audit_log = None
                    for call in log_calls:
                        if call[0] and isinstance(call[0][0], dict):
                            log_data = call[0][0]
                            if log_data.get("event") == "cascade_decision_audit":
                                audit_log = log_data
                                break
                    
                    assert audit_log is not None
                    
                    # Verify audit trail shows multiple attempts
                    attempts = audit_log["attempts"]
                    assert len(attempts) >= 2, "Expected at least agent_config and global_config attempts"
                    
                    # Verify first attempt (agent_config) failed
                    agent_attempt = next((a for a in attempts if a["source"] == "agent_config"), None)
                    assert agent_attempt is not None
                    assert agent_attempt["success"] is False
                    assert agent_attempt["error"] is not None
                    
                    # Verify second attempt (global_config) succeeded
                    global_attempt = next((a for a in attempts if a["source"] == "global_config"), None)
                    assert global_attempt is not None
                    assert global_attempt["success"] is True
                    assert global_attempt["value"] == 30
                    
                    # Verify cascade summary
                    summary = audit_log["cascade_summary"]
                    assert "attempted_sources" in summary
                    assert "failed_sources" in summary
                    assert "fallback_used" in summary
                    assert summary["fallback_used"] is False  # Should not use fallback
                    assert "performance" in summary

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fallback_usage_monitoring(self):
        """
        Test fallback usage monitoring and alerting.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 3:
        Test fallback usage monitoring and metrics.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Mock both agent and global config to fail, forcing fallback
        with patch('app.agents.config_loader.get_agent_config') as mock_get_agent_config:
            with patch('app.config.load_config') as mock_load_config:
                with patch('app.agents.cascade_monitor.logger') as mock_logger:
                    # Setup mocks to fail
                    mock_get_agent_config.side_effect = Exception("Agent config not found")
                    mock_load_config.side_effect = Exception("Global config not found")

                    # Call the function
                    result = await get_agent_history_limit("test_agent")

                    # Verify fallback value
                    assert result == 50

                    # Verify fallback usage was logged as warning
                    warning_calls = mock_logger.warning.call_args_list
                    
                    # Should have both fallback usage warning and audit trail
                    fallback_warning = None
                    audit_warning = None
                    
                    for call in warning_calls:
                        if call[0] and isinstance(call[0][0], dict):
                            log_data = call[0][0]
                            if log_data.get("event") == "cascade_fallback_usage":
                                fallback_warning = log_data
                            elif log_data.get("event") == "cascade_decision_audit":
                                audit_warning = log_data
                    
                    # Verify fallback usage warning
                    assert fallback_warning is not None
                    assert fallback_warning["agent_name"] == "test_agent"
                    assert fallback_warning["parameter"] == "history_limit"
                    assert "alert" in fallback_warning
                    assert "recommended_action" in fallback_warning
                    
                    # Verify audit trail also shows fallback usage
                    assert audit_warning is not None
                    assert audit_warning["successful_source"] == "hardcoded_fallback"
                    assert audit_warning["cascade_summary"]["fallback_used"] is True

    @pytest.mark.unit
    def test_cascade_audit_trail_performance_tracking(self):
        """
        Test cascade performance tracking and timing.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 4:
        Test performance monitoring in cascade decisions.
        """
        from app.agents.cascade_monitor import CascadeAuditTrail, CascadeSourceContext
        
        # Create audit trail
        audit_trail = CascadeAuditTrail("test_agent", "test_parameter")
        
        # Simulate timed cascade attempts
        with audit_trail.attempt_source("agent_config", "/path/to/config.yaml") as attempt:
            # Simulate some work
            import time
            time.sleep(0.001)  # 1ms
            attempt.success("test_value")
        
        # Finalize and check timing
        audit_trail.finalize_and_log()
        
        # Verify timing was recorded
        assert len(audit_trail.attempts) == 1
        attempt = audit_trail.attempts[0]
        assert attempt.duration_ms is not None
        assert attempt.duration_ms > 0
        assert attempt.success is True
        assert attempt.value == "test_value"

    @pytest.mark.unit
    def test_troubleshooting_guide_generation(self):
        """
        Test troubleshooting guide generation for different scenarios.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 5:
        Test troubleshooting guidance in audit logs.
        """
        from app.agents.cascade_monitor import CascadeAuditTrail, CascadeAttempt
        
        # Test fallback scenario
        audit_trail = CascadeAuditTrail("test_agent", "history_limit")
        
        # Add failed attempts
        audit_trail.record_attempt(CascadeAttempt(
            source="agent_config",
            success=False,
            error="Config file not found"
        ))
        
        audit_trail.record_attempt(CascadeAttempt(
            source="global_config", 
            success=False,
            error="Parameter missing"
        ))
        
        audit_trail.record_attempt(CascadeAttempt(
            source="hardcoded_fallback",
            success=True,
            value=50
        ))
        
        # Generate troubleshooting guide
        guide = audit_trail._generate_troubleshooting_guide()
        
        # Verify troubleshooting guidance
        assert "issue" in guide
        assert "check_agent_config" in guide
        assert "check_global_config" in guide
        assert "expected_path" in guide
        assert "failed_sources" in guide
        
        # Verify failed sources are documented
        assert "agent_config" in guide["failed_sources"]
        assert "global_config" in guide["failed_sources"]


class TestCascadeMetrics:
    """Test cascade metrics and monitoring."""

    @pytest.mark.unit
    def test_cascade_performance_logging(self):
        """
        Test cascade performance metrics logging.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 6:
        Test performance metrics collection and logging.
        """
        from app.agents.cascade_monitor import CascadeMetrics
        
        with patch('app.agents.cascade_monitor.logger') as mock_logger:
            # Log performance metric
            CascadeMetrics.log_cascade_performance(
                "test_agent", 
                "history_limit", 
                "agent_config", 
                2.5
            )
            
            # Verify performance logging
            mock_logger.debug.assert_called_once()
            log_data = mock_logger.debug.call_args[0][0]
            
            assert log_data["event"] == "cascade_performance_metric"
            assert log_data["agent_name"] == "test_agent"
            assert log_data["parameter"] == "history_limit"
            assert log_data["source"] == "agent_config"
            assert log_data["duration_ms"] == 2.5

    @pytest.mark.unit
    def test_cascade_health_monitoring(self):
        """
        Test cascade health check logging.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 7:
        Test system health monitoring and reporting.
        """
        from app.agents.cascade_monitor import CascadeMetrics
        
        with patch('app.agents.cascade_monitor.logger') as mock_logger:
            # Log health check
            CascadeMetrics.log_cascade_health_check(
                "test_agent",
                ["history_limit", "model_settings"],
                "healthy"
            )
            
            # Verify health logging
            mock_logger.info.assert_called_once()
            log_data = mock_logger.info.call_args[0][0]
            
            assert log_data["event"] == "cascade_health_check"
            assert log_data["agent_name"] == "test_agent"
            assert log_data["parameters_checked"] == ["history_limit", "model_settings"]
            assert log_data["health_status"] == "healthy"


class TestEnhancedLoggingIntegration:
    """Test integration of enhanced logging with existing cascade system."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enhanced_logging_backward_compatibility(self):
        """
        Test that enhanced logging maintains backward compatibility.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 8:
        Verify enhanced logging doesn't break existing functionality.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        # Mock successful agent config
        with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
            mock_agent_config = MagicMock()
            mock_agent_config.context_management = {"history_limit": 100}
            mock_get_config.return_value = mock_agent_config
            
            # Call function and verify it still returns correct value
            result = await get_agent_history_limit("test_agent")
            assert result == 100

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_logging_level_appropriateness(self):
        """
        Test that different scenarios use appropriate logging levels.

        CHUNK 0017-004-002-03 AUTOMATED-TEST 9:
        Verify logging levels match scenario severity.
        """
        from app.agents.config_loader import get_agent_history_limit
        
        with patch('app.agents.cascade_monitor.logger') as mock_logger:
            # Test successful agent config (should be DEBUG level)
            with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
                mock_agent_config = MagicMock()
                mock_agent_config.context_management = {"history_limit": 100}
                mock_get_config.return_value = mock_agent_config
                
                await get_agent_history_limit("test_agent")
                
                # Should use debug level for successful first-try cascade
                assert mock_logger.debug.called
                
            # Reset mock
            mock_logger.reset_mock()
            
            # Test fallback usage (should be WARNING level)
            with patch('app.agents.config_loader.get_agent_config') as mock_get_config:
                with patch('app.config.load_config') as mock_load_config:
                    mock_get_config.side_effect = Exception("Config not found")
                    mock_load_config.side_effect = Exception("Global config not found")
                    
                    await get_agent_history_limit("test_agent")
                    
                    # Should use warning level for fallback usage
                    assert mock_logger.warning.called
