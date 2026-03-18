"""
Test suite for log rotation and archival.

Tests cover:
- Daily log rotation
- Compression of old logs
- Retention policy cleanup (90 days)
- Emergency rotation based on file size
"""

import pytest
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from scripts.audit_logger import AuditLogger
from scripts.audit_rotate import LogRotator


class TestRotation:
    """Test cases for log rotation and archival."""

    def test_daily_rotation(self, tmp_path):
        """Test daily log rotation creates new log file."""
        config_path = tmp_path / "logging_config.json"
        log_dir = tmp_path / "logs"
        config = {
            "log_directory": str(log_dir),
            "encryption_enabled": False,
            "queue_max_size": 1000,
            "flush_interval_seconds": 5
        }

        log_dir.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create initial log file
        logger = AuditLogger(config_path=str(config_path))
        logger.log_action(
            action_type="test_action",
            actor="test",
            target="test",
            parameters={},
            result="success"
        )
        logger.flush()

        # Get initial log file count
        initial_files = list(log_dir.glob("audit_*.jsonl"))
        initial_count = len(initial_files)

        # Perform rotation
        rotator = LogRotator(log_directory=str(log_dir))
        result = rotator.rotate()

        assert result["status"] == "success"
        assert "rotated" in result

        # Verify new log file structure
        final_files = list(log_dir.glob("audit_*.jsonl"))
        assert len(final_files) >= initial_count

    def test_compression(self, audit_logger_with_old_logs):
        """Test compression of old log files."""
        logger, log_dir, config_path = audit_logger_with_old_logs

        rotator = LogRotator(log_directory=str(log_dir))

        # Compress old logs
        result = rotator._compress_old_logs(days_old=1)

        assert result["compressed_count"] > 0

        # Verify compressed files exist
        compressed_files = list(log_dir.glob("audit_*.jsonl.gz"))
        assert len(compressed_files) > 0

        # Verify original uncompressed files are removed
        old_uncompressed = list(log_dir.glob("audit_*.jsonl"))
        # Should only have today's log file
        today = datetime.utcnow().strftime("%Y-%m-%d")
        for f in old_uncompressed:
            assert today in f.name

    def test_retention_cleanup(self, audit_logger_with_old_logs):
        """Test cleanup of logs older than retention period."""
        logger, log_dir, config_path = audit_logger_with_old_logs

        rotator = LogRotator(log_directory=str(log_dir), retention_days=90)

        # Get initial file count
        initial_files = list(log_dir.glob("audit_*"))
        initial_count = len(initial_files)

        # Cleanup old logs
        result = rotator._cleanup_old_logs()

        assert result["deleted_count"] > 0

        # Verify old files are deleted
        final_files = list(log_dir.glob("audit_*"))
        assert len(final_files) < initial_count

        # Verify only files within retention remain
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        for log_file in final_files:
            filename = log_file.name
            if filename.startswith("audit_"):
                date_str = filename.replace("audit_", "").split(".")[0]
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    assert file_date >= cutoff_date
                except ValueError:
                    pass

    def test_emergency_rotation(self, tmp_path):
        """Test emergency rotation when log file exceeds size limit."""
        config_path = tmp_path / "logging_config.json"
        log_dir = tmp_path / "logs"
        config = {
            "log_directory": str(log_dir),
            "encryption_enabled": False,
            "rotation_max_size_mb": 1,  # 1 MB limit
            "queue_max_size": 1000,
            "flush_interval_seconds": 5
        }

        log_dir.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f)

        rotator = LogRotator(log_directory=str(log_dir), max_size_mb=1)

        # Create a large log file
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = log_dir / f"audit_{today}.jsonl"

        with open(log_file, 'w') as f:
            # Write enough data to exceed 1 MB
            for i in range(50000):
                log_entry = {
                    "id": f"test-{i}",
                    "timestamp": datetime.utcnow().isoformat() + 'Z',
                    "action_type": "test",
                    "actor": "test",
                    "target": "test",
                    "parameters": {"data": "x" * 100},
                    "result": "success"
                }
                f.write(json.dumps(log_entry) + '\n')

        # Check if emergency rotation is needed
        needs_rotation = rotator._check_emergency_rotation()

        assert needs_rotation is True

        # Perform emergency rotation
        result = rotator._emergency_rotate()

        assert result["status"] == "success"
        assert "rotated_file" in result

    def test_rotation_with_checksums(self, audit_logger_with_old_logs):
        """Test that rotation generates checksums for rotated files."""
        logger, log_dir, config_path = audit_logger_with_old_logs

        rotator = LogRotator(log_directory=str(log_dir))

        # Perform rotation with checksum generation
        result = rotator.rotate(generate_checksums=True)

        assert result["status"] == "success"

        # Verify checksum file exists
        checksum_file = log_dir / ".checksums.json"
        assert checksum_file.exists()

        # Verify checksums are valid
        with open(checksum_file, 'r') as f:
            checksums = json.load(f)
            assert "files" in checksums
            assert len(checksums["files"]) > 0

    def test_rotation_preserves_data(self, tmp_path):
        """Test that rotation doesn't lose any log entries."""
        config_path = tmp_path / "logging_config.json"
        log_dir = tmp_path / "logs"
        config = {
            "log_directory": str(log_dir),
            "encryption_enabled": False,
            "queue_max_size": 1000,
            "flush_interval_seconds": 5
        }

        log_dir.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Create log entries
        logger = AuditLogger(config_path=str(config_path))

        entry_ids = []
        for i in range(10):
            log_id = logger.log_action(
                action_type=f"test_{i}",
                actor="test",
                target="test",
                parameters={"index": i},
                result="success"
            )
            entry_ids.append(log_id)

        logger.flush()

        # Count entries before rotation
        log_files = list(log_dir.glob("audit_*.jsonl"))
        entries_before = 0
        for log_file in log_files:
            with open(log_file, 'r') as f:
                entries_before += sum(1 for line in f if line.strip())

        # Perform rotation
        rotator = LogRotator(log_directory=str(log_dir))
        rotator.rotate()

        # Count entries after rotation (including compressed files)
        entries_after = 0
        for log_file in log_dir.glob("audit_*.jsonl*"):
            if log_file.suffix == '.gz':
                with gzip.open(log_file, 'rt') as f:
                    entries_after += sum(1 for line in f if line.strip())
            else:
                with open(log_file, 'r') as f:
                    entries_after += sum(1 for line in f if line.strip())

        # All entries should be preserved
        assert entries_after >= entries_before


@pytest.fixture
def audit_logger_with_old_logs(tmp_path):
    """Fixture that creates logs with old dates."""
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

    # Create old log files
    old_dates = [
        datetime.utcnow() - timedelta(days=100),
        datetime.utcnow() - timedelta(days=50),
        datetime.utcnow() - timedelta(days=10),
        datetime.utcnow() - timedelta(days=2)
    ]

    for old_date in old_dates:
        log_file = log_dir / f"audit_{old_date.strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'w') as f:
            log_entry = {
                "id": f"old-{old_date.strftime('%Y%m%d')}",
                "timestamp": old_date.isoformat() + 'Z',
                "action_type": "old_action",
                "actor": "test",
                "target": "test",
                "parameters": {},
                "result": "success"
            }
            f.write(json.dumps(log_entry) + '\n')

    logger = AuditLogger(config_path=str(config_path))
    yield logger, log_dir, config_path
