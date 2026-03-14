"""Tests for Gmail Watcher.

This module tests the GmailWatcher class for OAuth authentication,
priority detection, action file creation, and restart idempotency.
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from tests.fixtures.mock_gmail_api import (
    MockGmailService,
    create_mock_email,
    create_mock_credentials
)


class TestGmailWatcherAuthentication:
    """Test OAuth token loading and refresh (T020)."""

    def test_loads_oauth_token_on_initialization(self, tmp_path):
        """Test that GmailWatcher loads OAuth token from file."""
        # This test will fail until we implement GmailWatcher
        from watchers.gmail_watcher import GmailWatcher

        token_file = tmp_path / "token.json"
        token_data = {"token": "mock_access_token", "refresh_token": "mock_refresh"}

        with open(token_file, 'w') as f:
            json.dump(token_data, f)

        watcher = GmailWatcher(token_path=str(token_file))

        assert watcher.credentials is not None
        assert watcher.credentials.token == "mock_access_token"

    def test_refreshes_expired_token_automatically(self, tmp_path):
        """Test that GmailWatcher refreshes expired OAuth token."""
        from watchers.gmail_watcher import GmailWatcher

        token_file = tmp_path / "token.json"

        # Create expired credentials
        expired_creds = create_mock_credentials(expired=True)

        with patch('watchers.gmail_watcher.Credentials') as mock_creds:
            mock_creds.from_authorized_user_file.return_value = expired_creds

            watcher = GmailWatcher(token_path=str(token_file))
            watcher.authenticate()

            # Verify refresh was called
            assert expired_creds.refresh.called

    def test_raises_error_if_token_file_missing(self, tmp_path):
        """Test that GmailWatcher raises error if token file doesn't exist."""
        from watchers.gmail_watcher import GmailWatcher

        token_file = tmp_path / "nonexistent_token.json"

        with pytest.raises(FileNotFoundError):
            watcher = GmailWatcher(token_path=str(token_file))
            watcher.authenticate()


class TestGmailWatcherPriorityDetection:
    """Test keyword matching for urgent emails (T021)."""

    def test_detects_priority_keyword_in_subject(self):
        """Test that _is_priority detects keywords in email subject."""
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher()
        watcher.priority_keywords = ['urgent', 'important', 'critical']

        email = create_mock_email(
            email_id="msg_001",
            from_addr="sender@example.com",
            subject="URGENT: Project deadline",
            snippet="This is an urgent matter."
        )

        assert watcher._is_priority(email) is True

    def test_detects_priority_keyword_in_body(self):
        """Test that _is_priority detects keywords in email body."""
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher()
        watcher.priority_keywords = ['invoice', 'payment']

        email = create_mock_email(
            email_id="msg_002",
            from_addr="billing@vendor.com",
            subject="Monthly statement",
            snippet="Please find the invoice attached for your review."
        )

        assert watcher._is_priority(email) is True

    def test_case_insensitive_keyword_matching(self):
        """Test that keyword matching is case-insensitive."""
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher()
        watcher.priority_keywords = ['urgent']

        email = create_mock_email(
            email_id="msg_003",
            from_addr="sender@example.com",
            subject="URGENT: Please respond",
            snippet="This is urgent."
        )

        assert watcher._is_priority(email) is True

    def test_ignores_non_priority_emails(self):
        """Test that non-priority emails are not flagged."""
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher()
        watcher.priority_keywords = ['urgent', 'important', 'invoice']

        email = create_mock_email(
            email_id="msg_004",
            from_addr="newsletter@company.com",
            subject="Weekly Newsletter",
            snippet="Check out this week's updates."
        )

        assert watcher._is_priority(email) is False

    def test_whole_word_matching_only(self):
        """Test that keyword matching uses whole words only."""
        from watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher()
        watcher.priority_keywords = ['urgent']

        # "urgently" should NOT match "urgent" (whole word matching)
        email = create_mock_email(
            email_id="msg_005",
            from_addr="sender@example.com",
            subject="Please respond urgently",
            snippet="We need this urgently."
        )

        # This should fail with current implementation if not using whole word matching
        assert watcher._is_priority(email) is False


class TestGmailWatcherActionFileCreation:
    """Test action file format and location (T022)."""

    def test_creates_action_file_in_needs_action_folder(self, tmp_path):
        """Test that action files are created in Needs_Action/ folder."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True)

        watcher = GmailWatcher(vault_path=str(vault_path))

        email = create_mock_email(
            email_id="msg_001",
            from_addr="client@example.com",
            subject="Project update",
            snippet="Here's the latest update."
        )

        watcher.create_action_file(email)

        # Verify action file was created
        action_files = list(needs_action.glob("EMAIL_*.md"))
        assert len(action_files) == 1

    def test_action_file_has_correct_naming_convention(self, tmp_path):
        """Test that action files follow EMAIL_YYYYMMDD_HHMMSS_from.md format."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True)

        watcher = GmailWatcher(vault_path=str(vault_path))

        email = create_mock_email(
            email_id="msg_001",
            from_addr="john.doe@example.com",
            subject="Test email",
            snippet="Test content"
        )

        watcher.create_action_file(email)

        # Verify filename format
        action_files = list(needs_action.glob("EMAIL_*.md"))
        assert len(action_files) == 1

        filename = action_files[0].name
        # Should match: EMAIL_20260225_143000_john_doe_at_example_com.md
        assert filename.startswith("EMAIL_")
        assert filename.endswith(".md")
        assert "john_doe_at_example_com" in filename

    def test_action_file_contains_required_metadata(self, tmp_path):
        """Test that action files contain all required metadata fields."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True)

        watcher = GmailWatcher(vault_path=str(vault_path))

        email = create_mock_email(
            email_id="msg_001",
            from_addr="sender@example.com",
            subject="Test Subject",
            snippet="Test snippet content"
        )

        watcher.create_action_file(email)

        # Read action file
        action_files = list(needs_action.glob("EMAIL_*.md"))
        with open(action_files[0], 'r') as f:
            content = f.read()

        # Verify required fields are present
        assert "email_id: msg_001" in content
        assert "from: sender@example.com" in content
        assert "subject: Test Subject" in content
        assert "snippet: Test snippet content" in content
        assert "status: pending" in content


class TestGmailWatcherRestartIdempotency:
    """Test no duplicates after restart (T023)."""

    def test_does_not_create_duplicate_action_files_after_restart(self, tmp_path):
        """Test that restarting watcher doesn't create duplicate action files."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        state_dir = vault_path / ".state"
        needs_action.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        state_file = state_dir / "gmail_watcher_state.json"

        # First run: process email
        watcher1 = GmailWatcher(
            vault_path=str(vault_path),
            state_file=str(state_file)
        )

        email = create_mock_email(
            email_id="msg_001",
            from_addr="sender@example.com",
            subject="Test email",
            snippet="Test content"
        )

        watcher1.create_action_file(email)

        # Verify one action file created
        action_files = list(needs_action.glob("EMAIL_*.md"))
        assert len(action_files) == 1

        # Simulate restart: create new watcher instance
        watcher2 = GmailWatcher(
            vault_path=str(vault_path),
            state_file=str(state_file)
        )

        # Try to process same email again
        watcher2.create_action_file(email)

        # Verify still only one action file (no duplicate)
        action_files = list(needs_action.glob("EMAIL_*.md"))
        assert len(action_files) == 1

    def test_state_persists_across_multiple_restarts(self, tmp_path):
        """Test that processed email IDs persist across multiple restarts."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        state_dir = vault_path / ".state"
        state_dir.mkdir(parents=True)

        state_file = state_dir / "gmail_watcher_state.json"

        # First run: process 3 emails
        watcher1 = GmailWatcher(state_file=str(state_file))
        watcher1.state.mark_processed("msg_001")
        watcher1.state.mark_processed("msg_002")
        watcher1.state.mark_processed("msg_003")
        watcher1.state.save()

        # Second restart
        watcher2 = GmailWatcher(state_file=str(state_file))
        assert watcher2.state.is_processed("msg_001") is True
        assert watcher2.state.is_processed("msg_002") is True
        assert watcher2.state.is_processed("msg_003") is True

        # Third restart
        watcher3 = GmailWatcher(state_file=str(state_file))
        assert watcher3.state.is_processed("msg_001") is True
        assert watcher3.state.is_processed("msg_002") is True
        assert watcher3.state.is_processed("msg_003") is True
