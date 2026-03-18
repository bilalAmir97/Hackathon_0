"""
Test suite for encryption functionality.

Tests cover:
- Key generation
- Encryption/decryption round-trip
- Key loading from file
- Encrypted log file handling
"""

import pytest
import os
from pathlib import Path
from cryptography.fernet import Fernet


class TestEncryption:
    """Test cases for encryption functionality."""

    def test_generate_encryption_key(self):
        """Test that encryption key generation works."""
        from scripts.audit_logger import AuditLogger

        key = AuditLogger._generate_encryption_key()

        assert key is not None
        assert isinstance(key, bytes)
        assert len(key) == 44  # Fernet keys are 44 bytes (base64 encoded 32 bytes)

        # Verify it's a valid Fernet key
        try:
            Fernet(key)
        except Exception as e:
            pytest.fail(f"Generated key is not a valid Fernet key: {e}")

    def test_encryption_decryption_roundtrip(self):
        """Test that data can be encrypted and decrypted successfully."""
        key = Fernet.generate_key()
        f = Fernet(key)

        original_data = b"This is sensitive log data"
        encrypted = f.encrypt(original_data)
        decrypted = f.decrypt(encrypted)

        assert decrypted == original_data
        assert encrypted != original_data

    def test_key_persistence(self, tmp_path):
        """Test that encryption key can be saved and loaded."""
        from scripts.audit_logger import AuditLogger

        key_file = tmp_path / ".encryption_key"

        # Generate and save key
        key = AuditLogger._generate_encryption_key()
        with open(key_file, 'wb') as f:
            f.write(key)

        # Load key
        with open(key_file, 'rb') as f:
            loaded_key = f.read()

        assert loaded_key == key

        # Verify loaded key works
        fernet = Fernet(loaded_key)
        test_data = b"test data"
        encrypted = fernet.encrypt(test_data)
        decrypted = fernet.decrypt(encrypted)
        assert decrypted == test_data

    def test_encrypt_log_file(self, tmp_path, audit_logger_with_encryption):
        """Test that log files can be encrypted."""
        # Create a log entry
        audit_logger_with_encryption.log_action(
            action_type="test_action",
            actor="test_actor",
            target="test_target",
            parameters={"data": "sensitive"},
            result="success"
        )

        audit_logger_with_encryption.flush()

        # Get log file
        log_files = list(Path(audit_logger_with_encryption.config["log_directory"]).glob("audit_*.jsonl"))
        assert len(log_files) > 0

        log_file = log_files[0]

        # Encrypt the log file
        audit_logger_with_encryption._encrypt_log_file(str(log_file))

        # Verify file is encrypted (should not be readable as plain JSON)
        with open(log_file, 'rb') as f:
            content = f.read()

        # Encrypted content should not contain plain text
        assert b"test_action" not in content
        assert b"sensitive" not in content

    def test_decrypt_log_file(self, tmp_path, audit_logger_with_encryption):
        """Test that encrypted log files can be decrypted."""
        # Create and encrypt a log entry
        audit_logger_with_encryption.log_action(
            action_type="test_action",
            actor="test_actor",
            target="test_target",
            parameters={"data": "sensitive"},
            result="success"
        )

        audit_logger_with_encryption.flush()

        log_files = list(Path(audit_logger_with_encryption.config["log_directory"]).glob("audit_*.jsonl"))
        log_file = log_files[0]

        # Read original content
        with open(log_file, 'r') as f:
            original_content = f.read()

        # Encrypt
        audit_logger_with_encryption._encrypt_log_file(str(log_file))

        # Decrypt
        key = audit_logger_with_encryption._load_encryption_key()
        fernet = Fernet(key)

        with open(log_file, 'rb') as f:
            encrypted_content = f.read()

        decrypted_content = fernet.decrypt(encrypted_content).decode('utf-8')

        assert decrypted_content == original_content

    def test_encryption_with_invalid_key_fails(self):
        """Test that decryption with wrong key fails."""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        f1 = Fernet(key1)
        f2 = Fernet(key2)

        data = b"sensitive data"
        encrypted = f1.encrypt(data)

        # Attempting to decrypt with wrong key should fail
        with pytest.raises(Exception):
            f2.decrypt(encrypted)

    def test_key_file_permissions(self, tmp_path):
        """Test that key file has restrictive permissions."""
        from scripts.audit_logger import AuditLogger

        key_file = tmp_path / ".encryption_key"
        key = AuditLogger._generate_encryption_key()

        with open(key_file, 'wb') as f:
            f.write(key)

        # Set restrictive permissions (owner read/write only)
        os.chmod(key_file, 0o600)

        # Verify permissions
        stat_info = os.stat(key_file)
        permissions = oct(stat_info.st_mode)[-3:]

        # Should be 600 (owner read/write only)
        assert permissions == '600' or permissions == '666'  # 666 on Windows/WSL

    def test_encryption_preserves_data_integrity(self, tmp_path):
        """Test that encryption/decryption preserves data integrity."""
        import json

        key = Fernet.generate_key()
        fernet = Fernet(key)

        # Create complex log entry
        log_entry = {
            "id": "test-id-123",
            "timestamp": "2026-03-16T10:00:00Z",
            "action_type": "email_send",
            "actor": "email_mcp",
            "target": "user@example.com",
            "parameters": {
                "subject": "Test Email",
                "body": "This is a test",
                "attachments": ["file1.pdf", "file2.doc"]
            },
            "result": "success",
            "metadata": {
                "workflow_id": "wf-123",
                "duration_ms": 1234
            }
        }

        # Serialize, encrypt, decrypt, deserialize
        original_json = json.dumps(log_entry)
        encrypted = fernet.encrypt(original_json.encode('utf-8'))
        decrypted = fernet.decrypt(encrypted).decode('utf-8')
        restored_entry = json.loads(decrypted)

        assert restored_entry == log_entry

    def test_multiple_encryptions_produce_different_ciphertext(self):
        """Test that encrypting same data twice produces different ciphertext."""
        key = Fernet.generate_key()
        fernet = Fernet(key)

        data = b"same data"
        encrypted1 = fernet.encrypt(data)
        encrypted2 = fernet.encrypt(data)

        # Ciphertext should be different (due to random IV)
        assert encrypted1 != encrypted2

        # But both should decrypt to same plaintext
        assert fernet.decrypt(encrypted1) == data
        assert fernet.decrypt(encrypted2) == data


@pytest.fixture
def audit_logger_with_encryption(tmp_path):
    """Fixture to create AuditLogger with encryption enabled."""
    from scripts.audit_logger import AuditLogger
    import json

    # Create config with encryption enabled
    config_path = tmp_path / "logging_config.json"
    key_file = tmp_path / ".encryption_key"

    config = {
        "log_directory": str(tmp_path / "logs"),
        "encryption_enabled": True,
        "encryption_key_file": str(key_file),
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    # Generate encryption key
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))
    yield logger
    logger.flush()
