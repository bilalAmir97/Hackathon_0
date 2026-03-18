"""
Test suite for log integrity verification.

Tests cover:
- Calculating checksums for log files
- Verifying integrity (pass case)
- Detecting tampering (fail case)
- Verifying encrypted logs
"""

import pytest
import json
import hashlib
from pathlib import Path
from scripts.audit_logger import AuditLogger
from scripts.audit_verify import IntegrityVerifier


class TestAuditVerify:
    """Test cases for log integrity verification."""

    def test_calculate_checksum(self, audit_logger_with_data):
        """Test calculating SHA-256 checksum for a log file."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Get a log file
        log_files = list(log_dir.glob("audit_*.jsonl"))
        assert len(log_files) > 0

        log_file = log_files[0]

        # Calculate checksum
        checksum = verifier._calculate_checksum(str(log_file))

        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        assert isinstance(checksum, str)

        # Verify checksum is consistent
        checksum2 = verifier._calculate_checksum(str(log_file))
        assert checksum == checksum2

    def test_verify_integrity_pass(self, audit_logger_with_data):
        """Test verifying integrity of unmodified log files."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Generate checksums for all log files
        verifier.generate_checksums()

        # Verify all files
        result = verifier.verify_all()

        assert result["status"] == "pass"
        assert result["total_files"] > 0
        assert result["verified_files"] == result["total_files"]
        assert result["tampered_files"] == 0
        assert len(result["tampered"]) == 0

    def test_verify_integrity_fail(self, audit_logger_with_data):
        """Test detecting tampering when log file is modified."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Generate checksums
        verifier.generate_checksums()

        # Tamper with a log file
        log_files = list(log_dir.glob("audit_*.jsonl"))
        tampered_file = log_files[0]

        with open(tampered_file, 'a') as f:
            f.write('{"tampered": true}\n')

        # Verify - should detect tampering
        result = verifier.verify_all()

        assert result["status"] == "fail"
        assert result["tampered_files"] > 0
        assert len(result["tampered"]) > 0
        assert tampered_file.name in [t["file"] for t in result["tampered"]]

    def test_verify_encrypted_logs(self, audit_logger_with_encryption):
        """Test verifying integrity of encrypted log files."""
        audit_logger, log_dir, config_path = audit_logger_with_encryption

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Generate checksums
        verifier.generate_checksums()

        # Verify encrypted files
        result = verifier.verify_all()

        assert result["status"] == "pass"
        assert result["verified_files"] > 0

    def test_verify_specific_file(self, audit_logger_with_data):
        """Test verifying a specific log file."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Generate checksums
        verifier.generate_checksums()

        # Verify specific file
        log_files = list(log_dir.glob("audit_*.jsonl"))
        log_file = log_files[0]

        result = verifier.verify_file(str(log_file))

        assert result["status"] == "pass"
        assert result["file"] == log_file.name
        assert "checksum" in result

    def test_verify_compressed_logs(self, audit_logger_with_compressed):
        """Test verifying integrity of compressed log files."""
        audit_logger, log_dir, config_path = audit_logger_with_compressed

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Generate checksums for compressed files
        verifier.generate_checksums()

        # Verify compressed files
        result = verifier.verify_all()

        assert result["status"] == "pass"
        assert result["verified_files"] > 0

    def test_checksum_persistence(self, audit_logger_with_data):
        """Test that checksums are saved and loaded correctly."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Generate and save checksums
        verifier.generate_checksums()

        # Create new verifier instance
        verifier2 = IntegrityVerifier(log_directory=str(log_dir))

        # Load checksums
        checksums = verifier2._load_checksums()

        assert checksums is not None
        assert len(checksums) > 0

        # Verify using loaded checksums
        result = verifier2.verify_all()
        assert result["status"] == "pass"

    def test_missing_checksum_file(self, audit_logger_with_data):
        """Test handling when checksum file doesn't exist."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        verifier = IntegrityVerifier(log_directory=str(log_dir))

        # Try to verify without generating checksums first
        result = verifier.verify_all()

        assert result["status"] == "error"
        assert "checksum file not found" in result["message"].lower()


@pytest.fixture
def audit_logger_with_data(tmp_path):
    """Fixture that creates an AuditLogger with sample data."""
    import os

    config_path = tmp_path / "logging_config.json"
    log_dir = tmp_path / "logs"
    config = {
        "log_directory": str(log_dir),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))

    # Create sample log entries
    logger.log_action(
        action_type="test_action",
        actor="test_actor",
        target="test_target",
        parameters={"test": "data"},
        result="success"
    )

    logger.flush()

    yield logger, log_dir, config_path


@pytest.fixture
def audit_logger_with_encryption(tmp_path):
    """Fixture that creates encrypted log files."""
    import os
    from cryptography.fernet import Fernet

    config_path = tmp_path / "logging_config.json"
    log_dir = tmp_path / "logs"
    key_file = tmp_path / ".encryption_key"

    config = {
        "log_directory": str(log_dir),
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

    # Create log entry
    logger.log_action(
        action_type="encrypted_action",
        actor="test_actor",
        target="test_target",
        parameters={"sensitive": "data"},
        result="success"
    )

    logger.flush()

    # Encrypt the log file
    log_files = list(log_dir.glob("audit_*.jsonl"))
    for log_file in log_files:
        logger._encrypt_log_file(str(log_file))

    yield logger, log_dir, config_path


@pytest.fixture
def audit_logger_with_compressed(tmp_path):
    """Fixture that creates compressed log files."""
    import os
    import gzip

    config_path = tmp_path / "logging_config.json"
    log_dir = tmp_path / "logs"
    config = {
        "log_directory": str(log_dir),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))

    # Create log entry
    logger.log_action(
        action_type="compressed_action",
        actor="test_actor",
        target="test_target",
        parameters={"test": "data"},
        result="success"
    )

    logger.flush()

    # Compress the log file
    log_files = list(log_dir.glob("audit_*.jsonl"))
    for log_file in log_files:
        with open(log_file, 'rb') as f_in:
            with gzip.open(str(log_file) + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        log_file.unlink()

    yield logger, log_dir, config_path
