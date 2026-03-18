"""
Unit tests for ServiceHealth class

Tests health state transitions, service classification,
restart attempt tracking, and restart backoff calculation.
"""

import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path


class TestServiceHealth:
    """Test suite for ServiceHealth"""

    # T067: Test initial state is healthy
    def test_service_health_initial_state_healthy(self):
        """Test that ServiceHealth starts in healthy state"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        assert sh.service_name == "test_service"
        assert sh.state == "healthy"
        assert sh.is_critical is True
        assert sh.consecutive_failures == 0
        assert sh.last_check_time is None

    # T068: Test mark_degraded transitions to degraded state
    def test_mark_service_degraded(self):
        """Test that mark_degraded() transitions service to degraded state"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        # Mark as degraded
        sh.mark_degraded(reason="High latency detected")

        assert sh.state == "degraded"
        assert sh.last_check_time is not None
        assert sh.consecutive_failures == 1

    # T069: Test mark_failed transitions to failed state
    def test_mark_service_failed(self):
        """Test that mark_failed() transitions service to failed state"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=False)

        # Mark as failed
        sh.mark_failed(reason="Service crashed")

        assert sh.state == "failed"
        assert sh.last_check_time is not None
        assert sh.consecutive_failures == 1

    # T070: Test service classification (critical vs non-critical)
    def test_service_classification_critical_vs_noncritical(self):
        """Test that services are correctly classified as critical or non-critical"""
        from scripts.error_recovery.service_health import ServiceHealth, CRITICAL_SERVICES, NON_CRITICAL_SERVICES

        # Verify constants are defined
        assert isinstance(CRITICAL_SERVICES, (list, tuple, set))
        assert isinstance(NON_CRITICAL_SERVICES, (list, tuple, set))

        # Test critical service
        critical_sh = ServiceHealth(service_name="gmail_watcher", is_critical=True)
        assert critical_sh.is_critical is True

        # Test non-critical service
        noncritical_sh = ServiceHealth(service_name="daily_briefing", is_critical=False)
        assert noncritical_sh.is_critical is False

    # T071: Test degradation alert created
    def test_degradation_alert_created(self, tmp_path, mock_audit_logger):
        """Test that alert is created when service enters degraded state"""
        from scripts.error_recovery.service_health import ServiceHealth
        from unittest.mock import patch

        # Use tmp_path for alert directory
        alert_dir = tmp_path / "Needs_Action"
        alert_dir.mkdir(exist_ok=True)

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        # Mock the alert directory
        with patch('scripts.error_recovery.service_health.ALERT_DIR', alert_dir):
            with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
                # Mark as degraded - should create alert
                sh.mark_degraded(reason="High latency detected")

        # Verify alert file was created
        alert_files = list(alert_dir.glob("ALERT_DEGRADATION_*.md"))
        assert len(alert_files) >= 1

        # Verify alert content
        alert_content = alert_files[0].read_text()
        assert "test_service" in alert_content
        assert "degraded" in alert_content.lower()

    # T072: Test automatic recovery from degraded state
    def test_automatic_recovery_from_degraded_state(self):
        """Test that service can recover from degraded to healthy state"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        # Mark as degraded
        sh.mark_degraded(reason="Temporary issue")
        assert sh.state == "degraded"
        assert sh.consecutive_failures == 1

        # Mark as healthy - should reset
        sh.mark_healthy()
        assert sh.state == "healthy"
        assert sh.consecutive_failures == 0

    # T073: Test consecutive failures tracked
    def test_consecutive_failures_tracked(self):
        """Test that consecutive failures are tracked correctly"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        # Record multiple failures
        sh.mark_degraded(reason="Issue 1")
        assert sh.consecutive_failures == 1

        sh.mark_degraded(reason="Issue 2")
        assert sh.consecutive_failures == 2

        sh.mark_failed(reason="Issue 3")
        assert sh.consecutive_failures == 3

        # Recovery should reset counter
        sh.mark_healthy()
        assert sh.consecutive_failures == 0

    # Additional tests for edge cases
    def test_mark_healthy_resets_state(self):
        """Test that mark_healthy() resets all failure tracking"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        # Accumulate failures
        sh.mark_degraded(reason="Issue 1")
        sh.mark_degraded(reason="Issue 2")
        sh.mark_failed(reason="Issue 3")

        assert sh.state == "failed"
        assert sh.consecutive_failures == 3

        # Mark healthy - should reset everything
        sh.mark_healthy()

        assert sh.state == "healthy"
        assert sh.consecutive_failures == 0

    def test_alert_rate_limiting(self, tmp_path, mock_audit_logger):
        """Test that alerts are rate-limited (max 1 per service per 5 minutes)"""
        from scripts.error_recovery.service_health import ServiceHealth
        from unittest.mock import patch

        alert_dir = tmp_path / "Needs_Action"
        alert_dir.mkdir(exist_ok=True)

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        with patch('scripts.error_recovery.service_health.ALERT_DIR', alert_dir):
            with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
                # First degradation - should create alert
                sh.mark_degraded(reason="Issue 1")
                alert_count_1 = len(list(alert_dir.glob("ALERT_DEGRADATION_*.md")))

                # Immediate second degradation - should NOT create another alert (rate limited)
                sh.mark_degraded(reason="Issue 2")
                alert_count_2 = len(list(alert_dir.glob("ALERT_DEGRADATION_*.md")))

                # Should have same number of alerts (rate limited)
                assert alert_count_2 == alert_count_1

    def test_state_transitions_are_logged(self, mock_audit_logger):
        """Test that state transitions are logged to audit trail"""
        from scripts.error_recovery.service_health import ServiceHealth
        from unittest.mock import patch

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
            # Transition to degraded
            sh.mark_degraded(reason="High latency")

            # Verify audit logger was called
            assert mock_audit_logger.log_action.called

            # Verify log contains state transition information
            calls = mock_audit_logger.log_action.call_args_list
            assert len(calls) >= 1

            # Check that the log contains service health information
            first_call = calls[0]
            assert 'service_health' in first_call[1]['action_type'] or 'degraded' in str(first_call[1])

    # Phase 6: Auto-Restart Tests (User Story 4)

    # T086: Test should_restart for critical service
    def test_should_restart_critical_service(self):
        """Test that critical services should be restarted when failed"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="gmail_watcher", is_critical=True)

        # Mark as failed
        sh.mark_failed(reason="Service crashed")

        # Critical service should be eligible for restart
        assert sh.should_restart() is True

    # T087: Test should_not_restart for non-critical service
    def test_should_not_restart_noncritical_service(self):
        """Test that non-critical services should not be auto-restarted"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="daily_briefing", is_critical=False)

        # Mark as failed
        sh.mark_failed(reason="Service crashed")

        # Non-critical service should NOT be restarted
        assert sh.should_restart() is False

    # T088: Test restart backoff delays
    def test_restart_backoff_delays(self):
        """Test that restart backoff follows pattern: 0s, 30s, 60s, 120s"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        # Test backoff calculation
        assert sh.calculate_restart_backoff(0) == 0    # First restart: immediate
        assert sh.calculate_restart_backoff(1) == 30   # Second restart: 30s
        assert sh.calculate_restart_backoff(2) == 60   # Third restart: 60s
        assert sh.calculate_restart_backoff(3) == 120  # Fourth restart: 120s
        assert sh.calculate_restart_backoff(4) == 120  # Cap at 120s

    # T089: Test restart threshold exceeded
    def test_restart_threshold_exceeded(self):
        """Test that restart threshold is enforced (3 restarts in 10 minutes)"""
        from scripts.error_recovery.service_health import ServiceHealth
        from datetime import datetime, timedelta

        sh = ServiceHealth(service_name="test_service", is_critical=True)
        sh.max_restarts = 3
        sh.restart_window = 600.0  # 10 minutes

        # Simulate 3 restarts within window
        now = datetime.utcnow()
        sh.restart_count = 3
        sh.last_restart_time = now - timedelta(seconds=300)  # 5 minutes ago

        # Should exceed threshold
        assert sh.is_restart_threshold_exceeded() is True

        # Should not allow restart
        sh.mark_failed(reason="Crashed again")
        assert sh.should_restart() is False

    # T090: Test restart counter reset after stability
    def test_restart_counter_reset_after_stability(self):
        """Test that restart counter resets after stability period (5 minutes healthy)"""
        from scripts.error_recovery.service_health import ServiceHealth
        from datetime import datetime, timedelta

        sh = ServiceHealth(service_name="test_service", is_critical=True)
        sh.stability_period = 300.0  # 5 minutes

        # Simulate restart
        sh.restart_count = 2
        sh.last_restart_time = datetime.utcnow() - timedelta(seconds=400)  # 6+ minutes ago

        # Mark as healthy - should reset counter if stable
        sh.mark_healthy()

        # After stability period, counter should reset
        sh.reset_restart_counter_if_stable()
        assert sh.restart_count == 0

    # T091: Test restart alert created after threshold
    def test_restart_alert_created_after_threshold(self, tmp_path, mock_audit_logger):
        """Test that alert is created when restart threshold is exceeded"""
        from scripts.error_recovery.service_health import ServiceHealth
        from unittest.mock import patch
        from datetime import datetime, timedelta

        alert_dir = tmp_path / "Needs_Action"
        alert_dir.mkdir(exist_ok=True)

        sh = ServiceHealth(service_name="test_service", is_critical=True)
        sh.max_restarts = 3
        sh.restart_count = 3
        sh.last_restart_time = datetime.utcnow() - timedelta(seconds=300)

        with patch('scripts.error_recovery.service_health.ALERT_DIR', alert_dir):
            with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
                # Mark as failed when threshold exceeded - should create alert
                sh.mark_failed(reason="Service keeps crashing")

                # Check if restart threshold exceeded
                if sh.is_restart_threshold_exceeded():
                    sh.create_restart_threshold_alert()

        # Verify alert file was created
        alert_files = list(alert_dir.glob("ALERT_RESTART_*.md"))
        assert len(alert_files) >= 1

        # Verify alert content
        alert_content = alert_files[0].read_text()
        assert "test_service" in alert_content
        assert "restart" in alert_content.lower()

    # Additional restart tests
    def test_record_restart_increments_counter(self):
        """Test that record_restart() increments restart counter"""
        from scripts.error_recovery.service_health import ServiceHealth

        sh = ServiceHealth(service_name="test_service", is_critical=True)

        assert sh.restart_count == 0

        # Record restart
        sh.record_restart()
        assert sh.restart_count == 1
        assert sh.last_restart_time is not None

        # Record another restart
        sh.record_restart()
        assert sh.restart_count == 2

    def test_restart_window_enforcement(self):
        """Test that restart window is properly enforced"""
        from scripts.error_recovery.service_health import ServiceHealth
        from datetime import datetime, timedelta

        sh = ServiceHealth(service_name="test_service", is_critical=True)
        sh.max_restarts = 3
        sh.restart_window = 600.0  # 10 minutes

        # Restarts outside window should not count
        sh.restart_count = 3
        sh.last_restart_time = datetime.utcnow() - timedelta(seconds=700)  # 11+ minutes ago

        # Should NOT exceed threshold (outside window)
        assert sh.is_restart_threshold_exceeded() is False

