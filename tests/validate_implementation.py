#!/usr/bin/env python3
"""
WhatsApp Watcher - Implementation Validation Script

Tests the WhatsApp Watcher implementation without requiring Playwright installation.
Validates core functionality, state management, and file operations.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.whatsapp_watcher import (
    WhatsAppWatcher,
    WhatsAppState,
    DEFAULT_PRIORITY_KEYWORDS,
    retry_with_backoff
)


def test_state_management():
    """Test WhatsAppState class functionality."""
    print("\n" + "="*60)
    print("TEST: State Management")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test_state.json"

        # Test 1: State initialization
        print("\n1. Testing state initialization...")
        state = WhatsAppState(str(state_file))
        assert state_file.exists(), "State file should be created"
        assert len(state.processed_ids) == 0, "Initial processed_ids should be empty"
        assert state.session_status == "unknown", "Initial session status should be unknown"
        print("   ✓ State initialized correctly")

        # Test 2: Mark messages as processed
        print("\n2. Testing mark_processed...")
        state.mark_processed("test_id_1")
        state.mark_processed("test_id_2")
        assert len(state.processed_ids) == 2, "Should have 2 processed IDs"
        assert state.total_messages_processed == 2, "Counter should be 2"
        print("   ✓ Messages marked as processed")

        # Test 3: Check is_processed
        print("\n3. Testing is_processed...")
        assert state.is_processed("test_id_1"), "Should detect processed message"
        assert not state.is_processed("test_id_3"), "Should not detect unprocessed message"
        print("   ✓ Duplicate detection working")

        # Test 4: State persistence
        print("\n4. Testing state persistence...")
        state.save()

        # Load state in new instance
        state2 = WhatsAppState(str(state_file))
        assert len(state2.processed_ids) == 2, "Loaded state should have 2 IDs"
        assert state2.is_processed("test_id_1"), "Loaded state should remember processed IDs"
        print("   ✓ State persists across instances")

        # Test 5: Corrupted state recovery
        print("\n5. Testing corrupted state recovery...")
        state_file.write_text("invalid json {{{")
        state3 = WhatsAppState(str(state_file))
        assert len(state3.processed_ids) == 0, "Corrupted state should reset"
        backup_file = state_file.with_suffix('.json.corrupted')
        assert backup_file.exists(), "Backup should be created"
        print("   ✓ Corrupted state handled gracefully")

    print("\n✅ State Management: ALL TESTS PASSED")
    return True


def test_message_id_generation():
    """Test message ID generation."""
    print("\n" + "="*60)
    print("TEST: Message ID Generation")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = WhatsAppWatcher(vault_path=tmpdir, dry_run=True)

        # Test 1: Basic message ID format
        print("\n1. Testing message ID format...")
        msg_id = watcher._generate_message_id(
            sender="John Doe",
            timestamp="10:30 AM",
            message_text="URGENT: Need invoice"
        )
        assert "John Doe" in msg_id, "Should contain sender"
        assert "10:30 AM" in msg_id, "Should contain timestamp"
        assert "URGENT" in msg_id, "Should contain message preview"
        print(f"   Generated ID: {msg_id}")
        print("   ✓ Message ID format correct")

        # Test 2: Long message truncation
        print("\n2. Testing long message truncation...")
        long_msg = "A" * 100
        msg_id = watcher._generate_message_id("User", "10:00 AM", long_msg)
        preview = msg_id.split("_", 2)[2]
        assert len(preview) == 50, f"Preview should be 50 chars, got {len(preview)}"
        print("   ✓ Long messages truncated to 50 chars")

        # Test 3: Uniqueness
        print("\n3. Testing message ID uniqueness...")
        id1 = watcher._generate_message_id("User1", "10:00 AM", "Message 1")
        id2 = watcher._generate_message_id("User1", "10:00 AM", "Message 2")
        id3 = watcher._generate_message_id("User2", "10:00 AM", "Message 1")
        assert id1 != id2, "Different messages should have different IDs"
        assert id1 != id3, "Different senders should have different IDs"
        print("   ✓ Message IDs are unique")

    print("\n✅ Message ID Generation: ALL TESTS PASSED")
    return True


def test_filename_sanitization():
    """Test filename sanitization."""
    print("\n" + "="*60)
    print("TEST: Filename Sanitization")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = WhatsAppWatcher(vault_path=tmpdir, dry_run=True)

        # Test 1: Special characters removal
        print("\n1. Testing special character removal...")
        result = watcher._sanitize_sender_name("John@Doe#123!")
        assert "@" not in result and "#" not in result and "!" not in result
        print(f"   Input: 'John@Doe#123!' → Output: '{result}'")
        print("   ✓ Special characters removed")

        # Test 2: Space replacement
        print("\n2. Testing space replacement...")
        result = watcher._sanitize_sender_name("John Doe")
        assert result == "john_doe", f"Expected 'john_doe', got '{result}'"
        print(f"   Input: 'John Doe' → Output: '{result}'")
        print("   ✓ Spaces replaced with underscores")

        # Test 3: Lowercase conversion
        print("\n3. Testing lowercase conversion...")
        result = watcher._sanitize_sender_name("JOHN DOE")
        assert result == "john_doe", f"Expected 'john_doe', got '{result}'"
        print(f"   Input: 'JOHN DOE' → Output: '{result}'")
        print("   ✓ Converted to lowercase")

        # Test 4: Empty string handling
        print("\n4. Testing empty string handling...")
        result = watcher._sanitize_sender_name("   ")
        assert result == "unknown", f"Expected 'unknown', got '{result}'"
        print(f"   Input: '   ' → Output: '{result}'")
        print("   ✓ Empty strings handled")

    print("\n✅ Filename Sanitization: ALL TESTS PASSED")
    return True


def test_keyword_matching():
    """Test priority keyword matching."""
    print("\n" + "="*60)
    print("TEST: Keyword Matching")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = WhatsAppWatcher(vault_path=tmpdir, dry_run=True)

        # Test 1: Keyword detection
        print("\n1. Testing keyword detection...")
        assert watcher._is_priority_message("URGENT: Need help"), "Should detect 'urgent'"
        assert watcher._is_priority_message("This is ASAP"), "Should detect 'asap'"
        assert watcher._is_priority_message("Important meeting"), "Should detect 'important'"
        print("   ✓ Keywords detected correctly")

        # Test 2: Case insensitivity
        print("\n2. Testing case insensitivity...")
        assert watcher._is_priority_message("urgent message"), "Should detect lowercase"
        assert watcher._is_priority_message("URGENT MESSAGE"), "Should detect uppercase"
        assert watcher._is_priority_message("Urgent Message"), "Should detect mixed case"
        print("   ✓ Case-insensitive matching works")

        # Test 3: Non-priority messages
        print("\n3. Testing non-priority messages...")
        assert not watcher._is_priority_message("Thanks for the update"), "Should not match"
        assert not watcher._is_priority_message("See you later"), "Should not match"
        print("   ✓ Non-priority messages filtered correctly")

        # Test 4: Custom keywords
        print("\n4. Testing custom keywords...")
        custom_watcher = WhatsAppWatcher(
            vault_path=tmpdir,
            priority_keywords=["custom", "special"],
            dry_run=True
        )
        assert custom_watcher._is_priority_message("This is custom"), "Should detect custom keyword"
        assert not custom_watcher._is_priority_message("This is urgent"), "Should not detect default keyword"
        print("   ✓ Custom keywords work")

    print("\n✅ Keyword Matching: ALL TESTS PASSED")
    return True


def test_action_file_creation():
    """Test action file creation."""
    print("\n" + "="*60)
    print("TEST: Action File Creation")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = WhatsAppWatcher(vault_path=tmpdir, dry_run=False)

        # Test 1: Action file creation
        print("\n1. Testing action file creation...")
        action_file = watcher._create_action_file(
            sender="John Doe",
            message_text="URGENT: Need invoice for last month",
            timestamp="10:30 AM",
            message_id="test_id_1"
        )

        assert action_file is not None, "Action file should be created"
        assert action_file.exists(), "Action file should exist on disk"
        print(f"   Created: {action_file.name}")
        print("   ✓ Action file created")

        # Test 2: YAML frontmatter validation
        print("\n2. Testing YAML frontmatter...")
        content = action_file.read_text()
        assert "---" in content, "Should have YAML frontmatter"
        assert "type: whatsapp_message" in content, "Should have type field"
        assert "from: John Doe" in content, "Should have sender"
        assert "priority: high" in content, "Should have priority"
        assert "status: pending" in content, "Should have status"
        print("   ✓ YAML frontmatter valid")

        # Test 3: Message content
        print("\n3. Testing message content...")
        assert "URGENT: Need invoice for last month" in content, "Should contain message"
        assert "10:30 AM" in content, "Should contain timestamp"
        print("   ✓ Message content included")

        # Test 4: Dry-run mode
        print("\n4. Testing dry-run mode...")
        dry_watcher = WhatsAppWatcher(vault_path=tmpdir, dry_run=True)
        dry_file = dry_watcher._create_action_file(
            sender="Test User",
            message_text="Test message",
            timestamp="11:00 AM",
            message_id="test_id_2"
        )
        assert dry_file is None, "Dry-run should not create file"
        print("   ✓ Dry-run mode works")

    print("\n✅ Action File Creation: ALL TESTS PASSED")
    return True


def test_logging():
    """Test logging functionality."""
    print("\n" + "="*60)
    print("TEST: Logging")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = WhatsAppWatcher(vault_path=tmpdir, dry_run=True)

        # Test 1: Log entry creation
        print("\n1. Testing log entry creation...")
        log_entry = watcher._create_log_entry(
            action_type="test_action",
            status="success",
            inputs={"test": "input"},
            outputs={"test": "output"}
        )

        assert "timestamp" in log_entry, "Should have timestamp"
        assert "log_id" in log_entry, "Should have log_id"
        assert log_entry["action_type"] == "test_action", "Should have action_type"
        assert log_entry["status"] == "success", "Should have status"
        print("   ✓ Log entry structure correct")

        # Test 2: Log writing
        print("\n2. Testing log writing...")
        watcher._write_log(log_entry)

        log_files = list(Path(tmpdir).glob("Logs/*.json"))
        assert len(log_files) == 1, "Should create one log file"

        log_content = log_files[0].read_text()
        log_data = json.loads(log_content)
        assert log_data["action_type"] == "test_action", "Log should contain action_type"
        print(f"   Log file: {log_files[0].name}")
        print("   ✓ Log written correctly")

    print("\n✅ Logging: ALL TESTS PASSED")
    return True


def test_retry_decorator():
    """Test retry decorator with exponential backoff."""
    print("\n" + "="*60)
    print("TEST: Retry Decorator")
    print("="*60)

    # Test 1: Successful operation
    print("\n1. Testing successful operation...")
    call_count = [0]

    @retry_with_backoff(max_retries=3, base_delay=0.1)
    def success_func():
        call_count[0] += 1
        return "success"

    result = success_func()
    assert result == "success", "Should return success"
    assert call_count[0] == 1, "Should only call once"
    print("   ✓ Successful operation (no retries)")

    # Test 2: Retry on failure
    print("\n2. Testing retry on failure...")
    call_count[0] = 0

    @retry_with_backoff(max_retries=3, base_delay=0.1)
    def fail_twice_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Temporary failure")
        return "success"

    result = fail_twice_func()
    assert result == "success", "Should eventually succeed"
    assert call_count[0] == 3, "Should retry twice"
    print("   ✓ Retry logic works (2 retries, then success)")

    # Test 3: Max retries exceeded
    print("\n3. Testing max retries exceeded...")
    call_count[0] = 0

    @retry_with_backoff(max_retries=3, base_delay=0.1)
    def always_fail_func():
        call_count[0] += 1
        raise Exception("Permanent failure")

    try:
        always_fail_func()
        assert False, "Should have raised exception"
    except Exception as e:
        assert call_count[0] == 3, "Should try 3 times"
        print("   ✓ Max retries enforced")

    print("\n✅ Retry Decorator: ALL TESTS PASSED")
    return True


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("WhatsApp Watcher - Implementation Validation")
    print("="*60)

    tests = [
        ("State Management", test_state_management),
        ("Message ID Generation", test_message_id_generation),
        ("Filename Sanitization", test_filename_sanitization),
        ("Keyword Matching", test_keyword_matching),
        ("Action File Creation", test_action_file_creation),
        ("Logging", test_logging),
        ("Retry Decorator", test_retry_decorator),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: FAILED")
            print(f"   Error: {e}")
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Implementation is ready for manual testing.")
        print("\nNext Steps:")
        print("1. Install Playwright: uv run playwright install chromium")
        print("2. Run watcher: uv run python watchers/whatsapp_watcher.py --dry-run")
        print("3. Scan QR code and test with real WhatsApp messages")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
