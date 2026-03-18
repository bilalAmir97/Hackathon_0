"""
RecoveryState - Persistent state management for error recovery

Handles loading, saving, and managing recovery state including circuit breakers,
service health, and retry counters. Uses atomic writes to prevent corruption.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


class RecoveryState:
    """
    Container for all recovery state with atomic persistence.

    Manages circuit breaker states, service health records, and retry counters.
    State is persisted to disk using atomic writes (temp file + rename).
    """

    VERSION = "1.0.0"
    DEFAULT_STATE_PATH = Path("AI_Employee_Vault/.state/recovery_state.json")

    def __init__(self, state_path: Optional[Path] = None):
        """
        Initialize RecoveryState.

        Args:
            state_path: Path to state file (default: AI_Employee_Vault/.state/recovery_state.json)
        """
        self.state_path = Path(state_path) if state_path else self.DEFAULT_STATE_PATH
        self.version = self.VERSION
        self.last_updated = datetime.utcnow().isoformat() + "Z"
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.service_health: Dict[str, Dict[str, Any]] = {}
        self.retry_counters: Dict[str, int] = {}  # In-memory only, not persisted

    def save(self) -> None:
        """
        Save state to disk using atomic write pattern.

        Uses temp file + rename to ensure atomicity:
        1. Write to temporary file
        2. Flush and sync to disk
        3. Atomic rename to target file

        Raises:
            OSError: If file operations fail
        """
        # Update timestamp
        self.last_updated = datetime.utcnow().isoformat() + "Z"

        # Ensure directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to dict
        state_dict = self.to_dict()

        # Write to temporary file
        temp_path = self.state_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w') as f:
                json.dump(state_dict, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk

            # Atomic rename
            temp_path.replace(self.state_path)
        except Exception as e:
            # Cleanup temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to save recovery state: {e}") from e

    @classmethod
    def load(cls, state_path: Optional[Path] = None) -> 'RecoveryState':
        """
        Load state from disk with corruption recovery.

        Args:
            state_path: Path to state file (default: AI_Employee_Vault/.state/recovery_state.json)

        Returns:
            RecoveryState instance loaded from file, or fresh state if file missing/corrupted
        """
        path = Path(state_path) if state_path else cls.DEFAULT_STATE_PATH

        # If file doesn't exist, return fresh state
        if not path.exists():
            return cls(state_path=path)

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            # Create instance from loaded data
            return cls.from_dict(data, state_path=path)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Corruption detected - create backup and return fresh state
            backup_path = path.with_suffix(f'.json.backup.{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(path, backup_path)

            # Log corruption event (would integrate with audit logger in production)
            print(f"WARNING: Corrupted recovery state detected. Backup created at {backup_path}")
            print(f"Error: {e}")

            # Return fresh state
            return cls(state_path=path)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize state to dictionary.

        Returns:
            Dictionary representation of state (JSON-serializable)
        """
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "circuit_breakers": self.circuit_breakers,
            "service_health": self.service_health,
            # Note: retry_counters are in-memory only, not persisted
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], state_path: Optional[Path] = None) -> 'RecoveryState':
        """
        Deserialize state from dictionary.

        Args:
            data: Dictionary representation of state
            state_path: Path to state file

        Returns:
            RecoveryState instance

        Raises:
            ValueError: If data is invalid or version incompatible
        """
        # Validate version
        version = data.get("version")
        if not version:
            raise ValueError("Missing version field in recovery state")

        # Handle version migrations (currently only 1.0.0 exists)
        if version != cls.VERSION:
            # Future: Add migration logic here
            raise ValueError(f"Unsupported state version: {version} (expected {cls.VERSION})")

        # Create instance
        instance = cls(state_path=state_path)
        instance.version = version
        instance.last_updated = data.get("last_updated", instance.last_updated)
        instance.circuit_breakers = data.get("circuit_breakers", {})
        instance.service_health = data.get("service_health", {})

        return instance

    def get_circuit_breaker(self, service_name: str) -> Dict[str, Any]:
        """
        Get circuit breaker state for a service, creating if not exists.

        Args:
            service_name: Name of the service

        Returns:
            Circuit breaker state dictionary
        """
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                "service_name": service_name,
                "state": "CLOSED",
                "failure_count": 0,
                "last_failure_time": None,
                "cooldown_period": 60.0,
                "failure_threshold": 5,
                "success_threshold": 1
            }
        return self.circuit_breakers[service_name]

    def get_service_health(self, service_name: str, is_critical: bool = True) -> Dict[str, Any]:
        """
        Get service health state, creating if not exists.

        Args:
            service_name: Name of the service
            is_critical: Whether service is critical (default: True)

        Returns:
            Service health state dictionary
        """
        if service_name not in self.service_health:
            self.service_health[service_name] = {
                "service_name": service_name,
                "state": "healthy",
                "is_critical": is_critical,
                "last_check_time": None,
                "consecutive_failures": 0,
                "restart_count": 0,
                "last_restart_time": None,
                "restart_window": 600.0,
                "max_restarts": 3,
                "stability_period": 300.0
            }
        return self.service_health[service_name]
