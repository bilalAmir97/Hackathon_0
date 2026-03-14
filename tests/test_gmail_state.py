"""Tests for Gmail State Management.

This module tests the GmailState class for persistent state tracking,
ensuring idempotent operation across restarts.
"""

import json
import os
import pytest
from pathlib import Path
from watchers.gmail_state import GmailState


class TestGmailStateInitialization:
    """Test state file creation, loading, and saving (T018)."""

    def test_creates_new_state_file_if_missing(self, tmp_path):
        """Test that GmailState creates a new state file if it doesn't exist."""
        state_file = tmp_path / "test_state.json"

        state = GmailState(str(state_file))

        # State file should be created
        assert state_file.exists()

        # Initial state should be empty
        assert len(state.processed_email_ids) == 0
        assert state.last_poll_timestamp is None
        assert state.error_count == 0

    def test_loads_existing_state_file(self, tmp_path):
        """Test that GmailState loads existing state from file."""
        state_file = tmp_path / "test_state.json"

        # Create existing state file
        existing_state = {
            "last_poll_timestamp": "2026-02-25T14:30:00Z",
            "processed_email_ids": ["msg_001", "msg_002", "msg_003"],
            "error_count": 2,
            "last_error": {"timestamp": "2026-02-25T14:00:00Z", "error_type": "network"},
            "config": {"poll_interval_seconds": 120}
        }

        with open(state_file, 'w') as f:
            json.dump(existing_state, f)

        # Load state
        state = GmailState(str(state_file))

        # Verify loaded state
        assert state.last_poll_timestamp == "2026-02-25T14:30:00Z"
        assert len(state.processed_email_ids) == 3
        assert "msg_001" in state.processed_email_ids
        assert "msg_002" in state.processed_email_ids
        assert "msg_003" in state.processed_email_ids
        assert state.error_count == 2

    def test_saves_state_to_file(self, tmp_path):
        """Test that GmailState saves state to file correctly."""
        state_file = tmp_path / "test_state.json"

        state = GmailState(str(state_file))
        state.processed_email_ids.add("msg_001")
        state.processed_email_ids.add("msg_002")
        state.last_poll_timestamp = "2026-02-25T15:00:00Z"
        state.error_count = 1

        # Save state
        state.save()

        # Verify file contents
        with open(state_file, 'r') as f:
            saved_state = json.load(f)

        assert saved_state["last_poll_timestamp"] == "2026-02-25T15:00:00Z"
        assert len(saved_state["processed_email_ids"]) == 2
        assert "msg_001" in saved_state["processed_email_ids"]
        assert "msg_002" in saved_state["processed_email_ids"]
        assert saved_state["error_count"] == 1


class TestGmailStateIdempotency:
    """Test duplicate email ID detection (T019)."""

    def test_is_processed_returns_false_for_new_email(self, tmp_path):
        """Test that is_processed returns False for unprocessed email."""
        state_file = tmp_path / "test_state.json"
        state = GmailState(str(state_file))

        assert state.is_processed("msg_new_001") is False

    def test_is_processed_returns_true_for_existing_email(self, tmp_path):
        """Test that is_processed returns True for already processed email."""
        state_file = tmp_path / "test_state.json"

        # Create state with processed email
        existing_state = {
            "last_poll_timestamp": "2026-02-25T14:30:00Z",
            "processed_email_ids": ["msg_001", "msg_002"],
            "error_count": 0,
            "last_error": None,
            "config": {}
        }

        with open(state_file, 'w') as f:
            json.dump(existing_state, f)

        state = GmailState(str(state_file))

        assert state.is_processed("msg_001") is True
        assert state.is_processed("msg_002") is True
        assert state.is_processed("msg_003") is False

    def test_mark_processed_adds_email_id(self, tmp_path):
        """Test that mark_processed adds email ID to processed set."""
        state_file = tmp_path / "test_state.json"
        state = GmailState(str(state_file))

        # Mark email as processed
        state.mark_processed("msg_new_001")

        # Verify it's now in processed set
        assert state.is_processed("msg_new_001") is True
        assert "msg_new_001" in state.processed_email_ids

    def test_mark_processed_persists_to_file(self, tmp_path):
        """Test that mark_processed saves state to file."""
        state_file = tmp_path / "test_state.json"
        state = GmailState(str(state_file))

        # Mark email as processed
        state.mark_processed("msg_new_001")

        # Create new state instance (simulates restart)
        state2 = GmailState(str(state_file))

        # Verify email is still marked as processed after restart
        assert state2.is_processed("msg_new_001") is True

    def test_prevents_duplicate_processing_across_restarts(self, tmp_path):
        """Test that duplicate emails are not processed after system restart."""
        state_file = tmp_path / "test_state.json"

        # First run: process emails
        state1 = GmailState(str(state_file))
        state1.mark_processed("msg_001")
        state1.mark_processed("msg_002")
        state1.save()

        # Simulate restart: create new state instance
        state2 = GmailState(str(state_file))

        # Verify previously processed emails are still marked
        assert state2.is_processed("msg_001") is True
        assert state2.is_processed("msg_002") is True

        # New email should not be marked
        assert state2.is_processed("msg_003") is False
