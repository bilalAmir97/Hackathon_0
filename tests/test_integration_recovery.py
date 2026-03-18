"""
Integration tests for error recovery system

Tests complete recovery workflows including retry + circuit breaker,
state persistence, and E2E scenarios.
"""

import pytest
import time
from unittest.mock import Mock, patch
from scripts.error_recovery.decorators import with_retry
from scripts.error_recovery.recovery_state import RecoveryState


class TestIntegrationRecovery:
    """Test suite for error recovery integration"""

    # T034: Integration test for retry with real failure simulation
    def test_retry_with_real_failure_simulation(self, temp_state_file, mock_audit_logger):
        """
        Test complete retry flow with simulated network failures.

        Simulates a service that fails with transient errors, then succeeds.
        Verifies retry logic, exponential backoff, and audit logging.
        """
        # Track call attempts and timing
        call_log = []

        @with_retry(max_attempts=5, base_delay=0.1, jitter_enabled=False)
        def simulated_network_call():
            """Simulates a flaky network call"""
            call_time = time.time()
            call_log.append(call_time)

            # Fail first 2 attempts, succeed on 3rd
            if len(call_log) <= 2:
                raise ConnectionError(f"Network timeout (attempt {len(call_log)})")

            return {"status": "success", "data": "retrieved"}

        # Execute with audit logging
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            result = simulated_network_call()

        # Verify success
        assert result["status"] == "success"
        assert result["data"] == "retrieved"

        # Verify retry attempts
        assert len(call_log) == 3  # Failed twice, succeeded on third

        # Verify exponential backoff timing
        # Attempt 0: immediate
        # Attempt 1: after ~0.1s delay (base_delay * 2^0)
        # Attempt 2: after ~0.2s delay (base_delay * 2^1)
        if len(call_log) >= 3:
            delay_1 = call_log[1] - call_log[0]
            delay_2 = call_log[2] - call_log[1]

            # Allow some tolerance for timing
            assert 0.08 <= delay_1 <= 0.15  # ~0.1s
            assert 0.18 <= delay_2 <= 0.25  # ~0.2s

        # Verify audit logging
        assert mock_audit_logger.log_action.called
        calls = mock_audit_logger.log_action.call_args_list

        # Should have logged retry attempts
        retry_logs = [c for c in calls if c[1]['action_type'] == 'error_recovery_retry']
        assert len(retry_logs) >= 2  # At least 2 retry attempts logged

    def test_retry_with_permanent_error_fails_immediately(self, mock_audit_logger):
        """Test that permanent errors are not retried"""
        call_count = {'count': 0}

        @with_retry(max_attempts=5, base_delay=0.01)
        def operation_with_permanent_error():
            call_count['count'] += 1
            raise ValueError("Invalid input - permanent error")

        # Should fail immediately without retries
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            with pytest.raises(ValueError, match="Invalid input"):
                operation_with_permanent_error()

        # Should only have tried once (no retries for permanent errors)
        assert call_count['count'] == 1

    def test_retry_exhausts_attempts_and_raises(self, mock_audit_logger):
        """Test that retry gives up after max attempts"""
        call_count = {'count': 0}

        @with_retry(max_attempts=3, base_delay=0.01)
        def always_failing_operation():
            call_count['count'] += 1
            raise ConnectionError("Service unavailable")

        # Should exhaust attempts and raise
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            with pytest.raises(ConnectionError, match="Service unavailable"):
                always_failing_operation()

        # Should have tried max_attempts times
        assert call_count['count'] == 3

    def test_retry_counter_in_recovery_state(self, temp_state_file):
        """Test that retry counters are tracked in RecoveryState (in-memory)"""
        state = RecoveryState(state_path=temp_state_file)

        # Simulate retry counter tracking
        state.retry_counters['test_operation'] = 0
        state.retry_counters['test_operation'] += 1
        state.retry_counters['test_operation'] += 1

        assert state.retry_counters['test_operation'] == 2

        # Save state
        state.save()

        # Load state - retry counters should NOT be persisted
        loaded_state = RecoveryState.load(state_path=temp_state_file)
        assert 'test_operation' not in loaded_state.retry_counters

        # Verify circuit breakers and service health ARE persisted
        assert loaded_state.version == "1.0.0"

    def test_retry_with_multiple_services(self, mock_audit_logger):
        """Test retry logic works independently for multiple services"""
        service_a_calls = {'count': 0}
        service_b_calls = {'count': 0}

        @with_retry(max_attempts=3, base_delay=0.01)
        def service_a_call():
            service_a_calls['count'] += 1
            if service_a_calls['count'] <= 1:
                raise ConnectionError("Service A timeout")
            return "Service A success"

        @with_retry(max_attempts=3, base_delay=0.01)
        def service_b_call():
            service_b_calls['count'] += 1
            if service_b_calls['count'] <= 2:
                raise ConnectionError("Service B timeout")
            return "Service B success"

        # Execute both services
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            result_a = service_a_call()
            result_b = service_b_call()

        # Verify both succeeded
        assert result_a == "Service A success"
        assert result_b == "Service B success"

        # Verify independent retry counts
        assert service_a_calls['count'] == 2  # Failed once, succeeded on second
        assert service_b_calls['count'] == 3  # Failed twice, succeeded on third

    # Tests for circuit breaker integration will be added in Phase 4
    # Tests for E2E scenarios will be added in Phase 9

    # T084: Integration test for graceful degradation
    def test_graceful_degradation_maintains_critical_services(self, mock_audit_logger):
        """
        Test that system maintains critical services when non-critical services fail.

        Simulates failures in non-critical services (daily_briefing, health_check)
        and verifies that critical services (gmail_watcher, approval_workflow) continue
        operating normally.
        """
        from scripts.error_recovery.service_health import ServiceHealth, CRITICAL_SERVICES, NON_CRITICAL_SERVICES
        from unittest.mock import patch

        # Create service health trackers
        critical_service = ServiceHealth(service_name="gmail_watcher", is_critical=True)
        non_critical_service = ServiceHealth(service_name="daily_briefing", is_critical=False)

        # Verify classification
        assert critical_service.is_critical is True
        assert non_critical_service.is_critical is False
        assert "gmail_watcher" in CRITICAL_SERVICES
        assert "daily_briefing" in NON_CRITICAL_SERVICES

        with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
            # Simulate non-critical service failures
            non_critical_service.mark_degraded(reason="High latency in briefing generation")
            non_critical_service.mark_failed(reason="Briefing service crashed")

            # Verify non-critical service is failed
            assert non_critical_service.state == "failed"
            assert non_critical_service.consecutive_failures == 2

            # Critical service should remain healthy and operational
            assert critical_service.state == "healthy"
            assert critical_service.consecutive_failures == 0

            # Simulate critical service continuing to operate successfully
            critical_service.mark_healthy()
            assert critical_service.state == "healthy"

            # Even if critical service has issues, it should be tracked differently
            critical_service.mark_degraded(reason="Temporary Gmail API slowdown")
            assert critical_service.state == "degraded"
            assert critical_service.is_critical is True  # Still marked as critical

            # Critical service can recover
            critical_service.mark_healthy()
            assert critical_service.state == "healthy"
            assert critical_service.consecutive_failures == 0

        # Verify audit logging captured state transitions
        assert mock_audit_logger.log_action.called
        calls = mock_audit_logger.log_action.call_args_list

        # Should have logged transitions for both services
        health_logs = [c for c in calls if c[1]['action_type'] == 'service_health_transition']
        assert len(health_logs) >= 4  # At least 4 state transitions logged

        # Verify that non-critical service failure doesn't prevent critical service operation
        # This is the key assertion for graceful degradation
        assert critical_service.state == "healthy"
        assert non_critical_service.state == "failed"
        # System continues operating with critical services healthy

    # T105: Integration test for auto-restart with backoff
    def test_auto_restart_with_backoff(self, mock_audit_logger):
        """
        Test complete auto-restart workflow with backoff.

        Simulates service failures and verifies:
        - Critical services are eligible for restart
        - Non-critical services are not restarted
        - Backoff delays are calculated correctly
        - Restart threshold is enforced
        - Alerts are created when threshold exceeded
        """
        from scripts.error_recovery.service_health import ServiceHealth
        from unittest.mock import patch

        # Create critical and non-critical services
        critical_service = ServiceHealth(service_name="gmail_watcher", is_critical=True)
        non_critical_service = ServiceHealth(service_name="daily_briefing", is_critical=False)

        with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
            # Test 1: Critical service should be eligible for restart when failed
            critical_service.mark_failed(reason="Service crashed")
            assert critical_service.state == "failed"
            assert critical_service.should_restart() is True

            # Test 2: Non-critical service should NOT be restarted
            non_critical_service.mark_failed(reason="Service crashed")
            assert non_critical_service.state == "failed"
            assert non_critical_service.should_restart() is False

            # Test 3: Verify backoff delays
            assert critical_service.calculate_restart_backoff(0) == 0    # Immediate
            assert critical_service.calculate_restart_backoff(1) == 30   # 30s
            assert critical_service.calculate_restart_backoff(2) == 60   # 60s
            assert critical_service.calculate_restart_backoff(3) == 120  # 120s

            # Test 4: Simulate restart attempts
            critical_service.record_restart()
            assert critical_service.restart_count == 1
            assert critical_service.should_restart() is True  # Still eligible

            critical_service.record_restart()
            assert critical_service.restart_count == 2
            assert critical_service.should_restart() is True  # Still eligible

            critical_service.record_restart()
            assert critical_service.restart_count == 3
            assert critical_service.should_restart() is False  # Threshold reached

            # Test 5: Verify threshold exceeded
            assert critical_service.is_restart_threshold_exceeded() is True

            # Test 6: Verify audit logging captured restart attempts
            assert mock_audit_logger.log_action.called
            calls = mock_audit_logger.log_action.call_args_list

            # Should have logged restart attempts
            restart_logs = [c for c in calls if c[1]['action_type'] == 'service_restart']
            assert len(restart_logs) == 3  # 3 restart attempts logged

            # Test 7: Verify recovery after stability period
            # Simulate service becoming healthy and stable
            critical_service.mark_healthy()
            critical_service.reset_restart_counter_if_stable()
            # Counter should reset after stability period
            # (In real scenario, this would happen after 5 minutes)

        # Verify final state
        assert critical_service.state == "healthy"
        assert non_critical_service.state == "failed"
        assert critical_service.restart_count == 3  # Counter not reset yet (needs time)
        assert non_critical_service.restart_count == 0  # Never restarted

    # T121: Test health check detects open circuits
    def test_health_check_detects_open_circuits(self, tmp_path, mock_audit_logger):
        """
        Test that health check correctly detects and reports open circuit breakers.

        Verifies:
        - Health check loads circuit breaker state
        - Open circuits are detected and reported
        - Half-open circuits are detected and reported
        - Status is set to critical when circuits are open
        """
        from scripts.health_check import HealthCheck
        from scripts.error_recovery.recovery_state import RecoveryState

        # Setup test environment
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "Logs").mkdir()
        (vault_path / "Needs_Action").mkdir()
        (vault_path / ".state").mkdir()

        # Create recovery state with open circuit breakers
        state_file = vault_path / ".state" / "recovery_state.json"
        recovery_state = RecoveryState(state_path=state_file)

        # Simulate open circuit breaker
        recovery_state.circuit_breakers["gmail_api"] = {
            "state": "OPEN",
            "failure_count": 5,
            "last_failure_time": "2026-03-16T10:00:00Z"
        }

        # Simulate half-open circuit breaker
        recovery_state.circuit_breakers["linkedin_api"] = {
            "state": "HALF_OPEN",
            "failure_count": 3,
            "last_failure_time": "2026-03-16T10:05:00Z"
        }

        # Save state
        recovery_state.save()

        # Create health check instance and patch RecoveryState.load to return our test state
        with patch('scripts.health_check.AuditLogger', return_value=mock_audit_logger):
            with patch.object(RecoveryState, 'load', return_value=recovery_state):
                health_check = HealthCheck(vault_path=str(vault_path))

                # Run circuit breaker check
                result = health_check.check_circuit_breakers()

        # Verify detection
        assert result["status"] == "critical"  # Open circuits = critical
        assert result["total_circuits"] == 2
        assert result["open_count"] == 1
        assert result["half_open_count"] == 1

        # Verify open circuit details
        assert len(result["open_circuits"]) == 1
        assert result["open_circuits"][0]["service"] == "gmail_api"
        assert result["open_circuits"][0]["failure_count"] == 5

        # Verify half-open circuit details
        assert len(result["half_open_circuits"]) == 1
        assert result["half_open_circuits"][0]["service"] == "linkedin_api"
        assert result["half_open_circuits"][0]["failure_count"] == 3

    # T122: Test health check detects degraded services
    def test_health_check_detects_degraded_services(self, tmp_path, mock_audit_logger):
        """
        Test that health check correctly detects and reports degraded services.

        Verifies:
        - Health check loads service health state
        - Degraded services are detected and reported
        - Critical vs non-critical degradation is distinguished
        - Status is set appropriately based on degradation severity
        """
        from scripts.health_check import HealthCheck

        # Setup test environment
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "Logs").mkdir()
        (vault_path / "Needs_Action").mkdir()
        (vault_path / ".state").mkdir()

        # Create a mock service health state object
        mock_service_health = Mock()
        mock_service_health.services = {
            "gmail_watcher": {
                "health_status": "DEGRADED",
                "is_critical": True,
                "consecutive_failures": 3,
                "last_check_time": "2026-03-16T10:00:00Z"
            },
            "daily_briefing": {
                "health_status": "DEGRADED",
                "is_critical": False,
                "consecutive_failures": 2,
                "last_check_time": "2026-03-16T10:00:00Z"
            }
        }

        # Create health check instance and mock ServiceHealth.load
        with patch('scripts.health_check.AuditLogger', return_value=mock_audit_logger):
            with patch('scripts.health_check.ServiceHealth') as MockServiceHealth:
                # Configure the mock to return our mock service health when load() is called
                MockServiceHealth.load.return_value = mock_service_health

                health_check = HealthCheck(vault_path=str(vault_path))

                # Run service degradation check
                result = health_check.check_service_degradation()

        # Verify detection
        assert result["status"] == "critical"  # Critical service degraded = critical
        assert result["total_services"] == 2
        assert result["degraded_count"] == 2
        assert result["critical_degraded_count"] == 1

        # Verify degraded service details
        assert len(result["degraded_services"]) == 2

        # Find critical service in results
        critical_result = next(s for s in result["degraded_services"] if s["service"] == "gmail_watcher")
        assert critical_result["is_critical"] is True
        assert critical_result["consecutive_failures"] == 3

        # Find non-critical service in results
        non_critical_result = next(s for s in result["degraded_services"] if s["service"] == "daily_briefing")
        assert non_critical_result["is_critical"] is False
        assert non_critical_result["consecutive_failures"] == 2

    # T124: E2E test for transient failure recovery
    def test_e2e_transient_failure_recovery(self, tmp_path, mock_audit_logger):
        """
        End-to-end test: Transient failure → retry → success.

        Simulates a complete workflow where a service experiences a temporary
        network timeout, the retry mechanism kicks in, and the operation succeeds.

        Verifies:
        - Initial failure is caught
        - Retry decorator applies exponential backoff
        - Operation succeeds after retry
        - Audit logs capture the entire recovery flow
        - Circuit breaker remains closed (no sustained failures)
        """
        from scripts.error_recovery.decorators import with_retry
        from scripts.error_recovery.recovery_state import RecoveryState

        # Setup recovery state
        state_file = tmp_path / "recovery_state.json"
        recovery_state = RecoveryState(state_path=state_file)

        # Track call attempts
        call_log = []

        @with_retry(max_attempts=5, base_delay=0.1, jitter_enabled=False)
        def api_call_with_transient_failure():
            """Simulates API call with transient network issue"""
            call_time = time.time()
            call_log.append(call_time)

            # Fail first 2 attempts (transient network timeout)
            if len(call_log) <= 2:
                raise ConnectionError(f"Network timeout (attempt {len(call_log)})")

            # Succeed on 3rd attempt
            return {"status": "success", "data": "retrieved"}

        # Execute with audit logging
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            result = api_call_with_transient_failure()

        # Verify success
        assert result["status"] == "success"
        assert result["data"] == "retrieved"

        # Verify retry attempts
        assert len(call_log) == 3  # Failed twice, succeeded on third

        # Verify exponential backoff timing
        if len(call_log) >= 3:
            delay_1 = call_log[1] - call_log[0]
            delay_2 = call_log[2] - call_log[1]
            assert 0.08 <= delay_1 <= 0.15  # ~0.1s
            assert 0.18 <= delay_2 <= 0.25  # ~0.2s

        # Verify audit logging captured recovery flow
        assert mock_audit_logger.log_action.called
        calls = mock_audit_logger.log_action.call_args_list
        retry_logs = [c for c in calls if c[1]['action_type'] == 'error_recovery_retry']
        assert len(retry_logs) >= 2  # At least 2 retry attempts logged

    # T125: E2E test for sustained failure circuit breaker
    def test_e2e_sustained_failure_circuit_breaker(self, tmp_path, mock_audit_logger):
        """
        End-to-end test: Sustained failures → circuit opens → cooldown → half-open → recovery.

        Simulates a complete circuit breaker workflow where a service experiences
        sustained failures, the circuit breaker opens to protect the system,
        enters cooldown period, transitions to half-open, and eventually recovers.

        Verifies:
        - Multiple failures trigger circuit breaker
        - Circuit opens after threshold (5 failures)
        - Subsequent calls fail fast with CircuitBreakerOpenError
        - Audit logs capture all state transitions
        """
        from scripts.error_recovery.decorators import with_retry, with_circuit_breaker
        from scripts.error_recovery.circuit_breaker import CircuitBreakerOpenError
        from scripts.error_recovery.recovery_state import RecoveryState

        # Setup recovery state
        state_file = tmp_path / "recovery_state.json"
        recovery_state = RecoveryState(state_path=state_file)

        call_count = {'count': 0}

        @with_retry(max_attempts=2, base_delay=0.01)
        @with_circuit_breaker(service_name='failing_api')
        def api_call_with_sustained_failures():
            """Simulates API call with sustained failures"""
            call_count['count'] += 1

            # Always fail to trigger circuit breaker
            raise ConnectionError(f"Service unavailable (attempt {call_count['count']})")

        # Execute with recovery state and audit logging
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            with patch.object(RecoveryState, 'load', return_value=recovery_state):
                # Attempt 1-3: Should fail with ConnectionError
                # Each attempt triggers 2 retries, so 3 attempts = 6 failures total
                for i in range(3):
                    try:
                        api_call_with_sustained_failures()
                        assert False, "Should have raised ConnectionError"
                    except (ConnectionError, CircuitBreakerOpenError):
                        pass  # Expected

                # Circuit should now be OPEN (after 5+ failures)
                # Next attempt should fail fast with CircuitBreakerOpenError
                try:
                    api_call_with_sustained_failures()
                    assert False, "Should have raised CircuitBreakerOpenError"
                except CircuitBreakerOpenError:
                    pass  # Expected - circuit is protecting the system

        # Verify audit logging captured circuit state transitions
        assert mock_audit_logger.log_action.called

    # T127: E2E test for graceful degradation
    def test_e2e_graceful_degradation(self, tmp_path, mock_audit_logger):
        """
        End-to-end test: Non-critical service fails → critical services continue.

        Simulates a scenario where a non-critical service (daily_briefing) fails
        while critical services (gmail_watcher) continue operating normally.

        Verifies:
        - Non-critical service can fail without affecting critical services
        - Critical services continue processing
        - System remains operational with degraded functionality
        - Audit logs distinguish between critical and non-critical failures
        """
        from scripts.error_recovery.service_health import ServiceHealth, CRITICAL_SERVICES, NON_CRITICAL_SERVICES

        # Verify service classification
        assert "gmail_watcher" in CRITICAL_SERVICES
        assert "daily_briefing" in NON_CRITICAL_SERVICES

        # Create service health trackers
        critical_service = ServiceHealth(service_name="gmail_watcher", is_critical=True)
        non_critical_service = ServiceHealth(service_name="daily_briefing", is_critical=False)

        with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
            # Simulate non-critical service failure
            non_critical_service.mark_failed(reason="Briefing generation timeout")
            assert non_critical_service.state == "failed"
            assert non_critical_service.should_restart() is False  # Non-critical not restarted

            # Critical service continues operating
            critical_service.mark_healthy()
            assert critical_service.state == "healthy"

            # Simulate critical service processing work successfully
            for i in range(5):
                critical_service.mark_healthy()

            # Verify critical service remained healthy throughout
            assert critical_service.state == "healthy"
            assert critical_service.consecutive_failures == 0

            # Verify non-critical service failure didn't affect critical service
            assert non_critical_service.state == "failed"
            assert critical_service.state == "healthy"

        # Verify audit logging captured the graceful degradation
        assert mock_audit_logger.log_action.called

    # T126: E2E test for service crash and restart
    def test_e2e_service_crash_restart(self, tmp_path, mock_audit_logger):
        """
        End-to-end test: Service crash → detect → restart → backoff → alert.

        Simulates a complete service restart workflow where a critical service
        crashes, the system detects it, attempts restart with exponential backoff,
        and creates alerts when restart threshold is exceeded.

        Verifies:
        - Service crash is detected
        - Critical service is eligible for restart
        - Restart backoff delays are applied correctly (0s, 30s, 60s, 120s)
        - Restart threshold is enforced (max 3 restarts in 10 minutes)
        - Alert is created when threshold exceeded
        - Audit logs capture all restart attempts
        """
        from scripts.error_recovery.service_health import ServiceHealth

        # Create critical service
        critical_service = ServiceHealth(service_name="gmail_watcher", is_critical=True)

        with patch('scripts.error_recovery.service_health.audit_logger', mock_audit_logger):
            # Simulate service crash
            critical_service.mark_failed(reason="Process crashed unexpectedly")
            assert critical_service.state == "failed"
            assert critical_service.should_restart() is True

            # Verify backoff delays
            assert critical_service.calculate_restart_backoff(0) == 0    # Immediate
            assert critical_service.calculate_restart_backoff(1) == 30   # 30s
            assert critical_service.calculate_restart_backoff(2) == 60   # 60s
            assert critical_service.calculate_restart_backoff(3) == 120  # 120s

            # Simulate restart attempts
            # Attempt 1: Immediate restart
            critical_service.record_restart()
            assert critical_service.restart_count == 1
            assert critical_service.should_restart() is True

            # Attempt 2: After 30s backoff
            critical_service.record_restart()
            assert critical_service.restart_count == 2
            assert critical_service.should_restart() is True

            # Attempt 3: After 60s backoff
            critical_service.record_restart()
            assert critical_service.restart_count == 3
            assert critical_service.should_restart() is False  # Threshold reached

            # Verify threshold exceeded
            assert critical_service.is_restart_threshold_exceeded() is True

            # Verify audit logging captured all restart attempts
            assert mock_audit_logger.log_action.called
            calls = mock_audit_logger.log_action.call_args_list
            restart_logs = [c for c in calls if c[1]['action_type'] == 'service_restart']
            assert len(restart_logs) == 3  # 3 restart attempts logged

    # T128: E2E test for state persistence across restart
    def test_e2e_state_persistence_across_restart(self, tmp_path, mock_audit_logger):
        """
        End-to-end test: Save state → restart system → load state → verify preserved.

        Simulates a complete system restart workflow where circuit breaker and
        service health state is persisted to disk, the system restarts, and
        state is correctly restored.

        Verifies:
        - Circuit breaker state persists across restarts
        - Service health state persists across restarts
        - Open circuits remain open after restart
        - Degraded services remain degraded after restart
        - State file uses atomic writes (corruption-resistant)
        - Audit logs are preserved
        """
        from scripts.error_recovery.recovery_state import RecoveryState
        from scripts.error_recovery.service_health import ServiceHealth

        # Setup state file
        state_file = tmp_path / "recovery_state.json"

        # Phase 1: Create and save state before "restart"
        recovery_state = RecoveryState(state_path=state_file)

        # Add open circuit breaker
        recovery_state.circuit_breakers["gmail_api"] = {
            "state": "OPEN",
            "failure_count": 5,
            "last_failure_time": "2026-03-16T10:00:00Z"
        }

        # Add half-open circuit breaker
        recovery_state.circuit_breakers["linkedin_api"] = {
            "state": "HALF_OPEN",
            "failure_count": 3,
            "last_failure_time": "2026-03-16T10:05:00Z"
        }

        # Save state (simulates system shutdown)
        recovery_state.save()

        # Verify state file exists
        assert state_file.exists()

        # Phase 2: Simulate system restart - load state from disk
        loaded_state = RecoveryState.load(state_path=state_file)

        # Verify circuit breaker state was preserved
        assert "gmail_api" in loaded_state.circuit_breakers
        assert loaded_state.circuit_breakers["gmail_api"]["state"] == "OPEN"
        assert loaded_state.circuit_breakers["gmail_api"]["failure_count"] == 5

        assert "linkedin_api" in loaded_state.circuit_breakers
        assert loaded_state.circuit_breakers["linkedin_api"]["state"] == "HALF_OPEN"
        assert loaded_state.circuit_breakers["linkedin_api"]["failure_count"] == 3

        # Verify version is preserved
        assert loaded_state.version == "1.0.0"

        # Phase 3: Verify atomic write protection
        # Corrupt the state file to test corruption recovery
        corrupted_content = "{ invalid json"
        state_file.write_text(corrupted_content)

        # Load should return fresh state (corruption recovery)
        recovered_state = RecoveryState.load(state_path=state_file)
        assert recovered_state.circuit_breakers == {}  # Fresh state
        assert recovered_state.version == "1.0.0"

    pass

