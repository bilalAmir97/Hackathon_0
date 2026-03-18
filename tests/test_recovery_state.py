"""
Unit tests for RecoveryState class

Tests state persistence, atomic writes, corruption recovery,
and schema versioning.
"""

import pytest
import json
from pathlib import Path
from scripts.error_recovery.recovery_state import RecoveryState


class TestRecoveryState:
    """Test suite for RecoveryState"""

    def test_init_creates_fresh_state(self, temp_state_file):
        """Test that initialization creates a fresh state with defaults"""
        state = RecoveryState(state_path=temp_state_file)

        assert state.version == "1.0.0"
        assert state.circuit_breakers == {}
        assert state.service_health == {}
        assert state.retry_counters == {}
        assert state.last_updated is not None

    def test_save_creates_file(self, temp_state_file):
        """Test that save() creates a state file"""
        state = RecoveryState(state_path=temp_state_file)
        state.save()

        assert temp_state_file.exists()

    def test_save_writes_valid_json(self, temp_state_file):
        """Test that save() writes valid JSON"""
        state = RecoveryState(state_path=temp_state_file)
        state.circuit_breakers["test_service"] = {
            "service_name": "test_service",
            "state": "CLOSED",
            "failure_count": 0
        }
        state.save()

        with open(temp_state_file, 'r') as f:
            data = json.load(f)

        assert data["version"] == "1.0.0"
        assert "test_service" in data["circuit_breakers"]

    def test_save_atomic_write_pattern(self, temp_state_file):
        """Test that save() uses atomic write (temp file + rename)"""
        state = RecoveryState(state_path=temp_state_file)
        state.save()

        # Verify no temp file remains after successful save
        temp_file = temp_state_file.with_suffix('.json.tmp')
        assert not temp_file.exists()
        assert temp_state_file.exists()

    def test_load_nonexistent_file_returns_fresh_state(self, temp_state_file):
        """Test that load() returns fresh state when file doesn't exist"""
        state = RecoveryState.load(state_path=temp_state_file)

        assert state.version == "1.0.0"
        assert state.circuit_breakers == {}
        assert state.service_health == {}

    def test_load_existing_file_restores_state(self, temp_state_file, sample_recovery_state):
        """Test that load() restores state from existing file"""
        # Create state file
        with open(temp_state_file, 'w') as f:
            json.dump(sample_recovery_state, f)

        # Load state
        state = RecoveryState.load(state_path=temp_state_file)

        assert state.version == "1.0.0"
        assert "gmail_api" in state.circuit_breakers
        assert "gmail_watcher" in state.service_health

    def test_load_corrupted_file_creates_backup(self, corrupted_state_file, temp_state_dir):
        """Test that load() creates backup when file is corrupted"""
        state = RecoveryState.load(state_path=corrupted_state_file)

        # Should return fresh state
        assert state.circuit_breakers == {}

        # Should create backup file
        backup_files = list(temp_state_dir.glob("*.backup.*"))
        assert len(backup_files) == 1

    def test_load_corrupted_file_returns_fresh_state(self, corrupted_state_file):
        """Test that load() returns fresh state when file is corrupted"""
        state = RecoveryState.load(state_path=corrupted_state_file)

        assert state.version == "1.0.0"
        assert state.circuit_breakers == {}
        assert state.service_health == {}

    def test_to_dict_serializes_state(self, temp_state_file):
        """Test that to_dict() serializes state correctly"""
        state = RecoveryState(state_path=temp_state_file)
        state.circuit_breakers["test"] = {"state": "OPEN"}
        state.service_health["test"] = {"state": "failed"}

        data = state.to_dict()

        assert data["version"] == "1.0.0"
        assert "last_updated" in data
        assert data["circuit_breakers"]["test"]["state"] == "OPEN"
        assert data["service_health"]["test"]["state"] == "failed"

    def test_to_dict_excludes_retry_counters(self, temp_state_file):
        """Test that to_dict() does not persist retry_counters (in-memory only)"""
        state = RecoveryState(state_path=temp_state_file)
        state.retry_counters["test"] = 5

        data = state.to_dict()

        assert "retry_counters" not in data

    def test_from_dict_deserializes_state(self, sample_recovery_state, temp_state_file):
        """Test that from_dict() deserializes state correctly"""
        state = RecoveryState.from_dict(sample_recovery_state, state_path=temp_state_file)

        assert state.version == "1.0.0"
        assert "gmail_api" in state.circuit_breakers
        assert "gmail_watcher" in state.service_health

    def test_from_dict_validates_version(self, temp_state_file):
        """Test that from_dict() validates version field"""
        invalid_data = {"circuit_breakers": {}}

        with pytest.raises(ValueError, match="Missing version field"):
            RecoveryState.from_dict(invalid_data, state_path=temp_state_file)

    def test_from_dict_rejects_incompatible_version(self, temp_state_file):
        """Test that from_dict() rejects incompatible versions"""
        invalid_data = {"version": "2.0.0", "circuit_breakers": {}}

        with pytest.raises(ValueError, match="Unsupported state version"):
            RecoveryState.from_dict(invalid_data, state_path=temp_state_file)

    def test_get_circuit_breaker_creates_if_not_exists(self, temp_state_file):
        """Test that get_circuit_breaker() creates entry if not exists"""
        state = RecoveryState(state_path=temp_state_file)

        cb = state.get_circuit_breaker("new_service")

        assert cb["service_name"] == "new_service"
        assert cb["state"] == "CLOSED"
        assert cb["failure_count"] == 0
        assert cb["failure_threshold"] == 5

    def test_get_circuit_breaker_returns_existing(self, temp_state_file):
        """Test that get_circuit_breaker() returns existing entry"""
        state = RecoveryState(state_path=temp_state_file)
        state.circuit_breakers["existing"] = {"service_name": "existing", "state": "OPEN"}

        cb = state.get_circuit_breaker("existing")

        assert cb["state"] == "OPEN"

    def test_get_service_health_creates_if_not_exists(self, temp_state_file):
        """Test that get_service_health() creates entry if not exists"""
        state = RecoveryState(state_path=temp_state_file)

        health = state.get_service_health("new_service", is_critical=True)

        assert health["service_name"] == "new_service"
        assert health["state"] == "healthy"
        assert health["is_critical"] is True
        assert health["restart_count"] == 0

    def test_get_service_health_returns_existing(self, temp_state_file):
        """Test that get_service_health() returns existing entry"""
        state = RecoveryState(state_path=temp_state_file)
        state.service_health["existing"] = {"service_name": "existing", "state": "degraded"}

        health = state.get_service_health("existing")

        assert health["state"] == "degraded"

    def test_save_and_load_roundtrip(self, temp_state_file):
        """Test that save() and load() work correctly together"""
        # Create and save state
        state1 = RecoveryState(state_path=temp_state_file)
        state1.circuit_breakers["test"] = {"state": "OPEN", "failure_count": 5}
        state1.service_health["test"] = {"state": "failed", "restart_count": 2}
        state1.save()

        # Load state
        state2 = RecoveryState.load(state_path=temp_state_file)

        assert state2.circuit_breakers["test"]["state"] == "OPEN"
        assert state2.circuit_breakers["test"]["failure_count"] == 5
        assert state2.service_health["test"]["state"] == "failed"
        assert state2.service_health["test"]["restart_count"] == 2

    def test_last_updated_changes_on_save(self, temp_state_file):
        """Test that last_updated timestamp is updated on save()"""
        state = RecoveryState(state_path=temp_state_file)
        original_timestamp = state.last_updated

        import time
        time.sleep(0.01)  # Small delay to ensure timestamp changes

        state.save()

        assert state.last_updated != original_timestamp
