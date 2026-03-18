"""
Pytest fixtures for error recovery tests

Provides mock audit logger, temporary state files, and mock services
for testing error recovery components.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_audit_logger():
    """Mock AuditLogger for testing without actual logging"""
    logger = Mock()
    logger.log_action = Mock(return_value=None)
    return logger


@pytest.fixture
def temp_state_dir(tmp_path):
    """Temporary directory for state files"""
    state_dir = tmp_path / ".state"
    state_dir.mkdir(exist_ok=True)
    return state_dir


@pytest.fixture
def temp_state_file(temp_state_dir):
    """Temporary state file path"""
    return temp_state_dir / "recovery_state.json"


@pytest.fixture
def sample_recovery_state():
    """Sample recovery state data for testing"""
    return {
        "version": "1.0.0",
        "last_updated": "2026-03-16T12:34:56Z",
        "circuit_breakers": {
            "gmail_api": {
                "service_name": "gmail_api",
                "state": "CLOSED",
                "failure_count": 0,
                "last_failure_time": None,
                "cooldown_period": 60.0,
                "failure_threshold": 5,
                "success_threshold": 1
            }
        },
        "service_health": {
            "gmail_watcher": {
                "service_name": "gmail_watcher",
                "state": "healthy",
                "is_critical": True,
                "last_check_time": "2026-03-16T12:34:56Z",
                "consecutive_failures": 0,
                "restart_count": 0,
                "last_restart_time": None,
                "restart_window": 600.0,
                "max_restarts": 3,
                "stability_period": 300.0
            }
        }
    }


@pytest.fixture
def corrupted_state_file(temp_state_file):
    """Create a corrupted state file for testing corruption recovery"""
    with open(temp_state_file, 'w') as f:
        f.write("{ invalid json content }")
    return temp_state_file


@pytest.fixture
def mock_service():
    """Mock service for testing circuit breaker and retry logic"""
    service = Mock()
    service.call = Mock()
    return service


@pytest.fixture
def failing_service():
    """Mock service that always fails"""
    service = Mock()
    service.call = Mock(side_effect=ConnectionError("Service unavailable"))
    return service


@pytest.fixture
def flaky_service():
    """Mock service that fails then succeeds"""
    service = Mock()
    call_count = {'count': 0}

    def flaky_call(*args, **kwargs):
        call_count['count'] += 1
        if call_count['count'] <= 2:
            raise ConnectionError("Temporary failure")
        return "Success"

    service.call = Mock(side_effect=flaky_call)
    return service


@pytest.fixture
def transient_errors():
    """List of transient errors for testing"""
    return [
        ConnectionError("Connection failed"),
        TimeoutError("Request timeout"),
        ConnectionResetError("Connection reset"),
        OSError("Network unreachable"),
    ]


@pytest.fixture
def permanent_errors():
    """List of permanent errors for testing"""
    return [
        ValueError("Invalid input"),
        TypeError("Type mismatch"),
        KeyError("Key not found"),
    ]


@pytest.fixture(autouse=True)
def cleanup_state_files(temp_state_dir):
    """Automatically cleanup state files after each test"""
    yield
    # Cleanup after test
    for file in temp_state_dir.glob("*.json*"):
        file.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset global circuit breaker registry between tests"""
    # Import here to avoid circular imports
    from scripts.error_recovery import decorators

    # Clear global state before test
    decorators._circuit_breakers.clear()
    decorators._recovery_state = None

    yield

    # Clear global state after test
    decorators._circuit_breakers.clear()
    decorators._recovery_state = None


@pytest.fixture(autouse=True)
def reset_service_health_state():
    """Reset global service health state between tests"""
    # Import here to avoid circular imports
    from scripts.error_recovery import service_health

    # Clear global state before test
    service_health._last_alert_time.clear()

    yield

    # Clear global state after test
    service_health._last_alert_time.clear()

