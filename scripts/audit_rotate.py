"""
Audit Rotate - Automated log rotation, compression, and retention.

Provides functionality to:
- Daily log rotation
- Compress old logs (gzip)
- Enforce 90-day retention policy
- Emergency rotation based on file size
- Generate checksums after rotation
"""

import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class LogRotator:
    """Manage log rotation, compression, and retention."""

    def __init__(
        self,
        log_directory: str = "AI_Employee_Vault/Logs",
        retention_days: int = 90,
        max_size_mb: int = 100
    ):
        """
        Initialize LogRotator.

        Args:
            log_directory: Path to audit log directory
            retention_days: Number of days to retain logs (default: 90)
            max_size_mb: Maximum log file size in MB before emergency rotation
        """
        self.log_directory = Path(log_directory)
        self.retention_days = retention_days
        self.max_size_mb = max_size_mb

    def _get_current_log_file(self) -> Optional[Path]:
        """
        Get the current day's log file.

        Returns:
            Path to current log file or None
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self.log_directory / f"audit_{today}.jsonl"

        if log_file.exists():
            return log_file
        return None

    def _rotate_log(self) -> Dict[str, Any]:
        """
        Rotate current log file (close and create new).

        Returns:
            Rotation result dictionary
        """
        current_log = self._get_current_log_file()

        if not current_log:
            return {
                "status": "success",
                "message": "No current log file to rotate"
            }

        # Current log file will be handled by compression
        # New log file will be created automatically by AuditLogger on next write

        return {
            "status": "success",
            "rotated_file": current_log.name,
            "message": "Log rotation completed"
        }

    def _compress_old_logs(self, days_old: int = 1) -> Dict[str, Any]:
        """
        Compress log files older than specified days.

        Args:
            days_old: Compress files older than this many days

        Returns:
            Compression result dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Get uncompressed log files
        log_files = sorted(self.log_directory.glob("audit_*.jsonl"))

        compressed_count = 0
        compressed_files = []

        for log_file in log_files:
            # Extract date from filename
            filename = log_file.name
            if filename.startswith("audit_"):
                date_str = filename.replace("audit_", "").replace(".jsonl", "")
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        # Compress the file
                        compressed_path = Path(str(log_file) + '.gz')

                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        # Remove original file
                        log_file.unlink()

                        compressed_count += 1
                        compressed_files.append(compressed_path.name)

                except ValueError:
                    # Invalid date format, skip
                    continue

        return {
            "status": "success",
            "compressed_count": compressed_count,
            "compressed_files": compressed_files
        }

    def _cleanup_old_logs(self) -> Dict[str, Any]:
        """
        Delete log files older than retention period.

        Returns:
            Cleanup result dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)

        # Get all log files (compressed and uncompressed)
        log_files = sorted(self.log_directory.glob("audit_*"))

        deleted_count = 0
        deleted_files = []

        for log_file in log_files:
            # Extract date from filename
            filename = log_file.name
            if filename.startswith("audit_"):
                date_str = filename.replace("audit_", "").split(".")[0]
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        # Delete the file
                        log_file.unlink()

                        deleted_count += 1
                        deleted_files.append(filename)

                except ValueError:
                    # Invalid date format, skip
                    continue

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "deleted_files": deleted_files,
            "retention_days": self.retention_days
        }

    def _check_emergency_rotation(self) -> bool:
        """
        Check if emergency rotation is needed based on file size.

        Returns:
            True if emergency rotation needed
        """
        current_log = self._get_current_log_file()

        if not current_log:
            return False

        # Check file size
        file_size_mb = current_log.stat().st_size / (1024 * 1024)

        return file_size_mb >= self.max_size_mb

    def _emergency_rotate(self) -> Dict[str, Any]:
        """
        Perform emergency rotation due to file size limit.

        Returns:
            Emergency rotation result
        """
        current_log = self._get_current_log_file()

        if not current_log:
            return {
                "status": "error",
                "message": "No current log file found"
            }

        # Rename current log with timestamp suffix
        timestamp = datetime.utcnow().strftime("%H%M%S")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        rotated_name = f"audit_{today}_{timestamp}.jsonl"
        rotated_path = self.log_directory / rotated_name

        # Rename the file
        current_log.rename(rotated_path)

        # Compress the rotated file immediately
        compressed_path = Path(str(rotated_path) + '.gz')

        with open(rotated_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove original
        rotated_path.unlink()

        return {
            "status": "success",
            "rotated_file": rotated_name,
            "compressed_file": compressed_path.name,
            "message": "Emergency rotation completed"
        }

    def rotate(self, generate_checksums: bool = False) -> Dict[str, Any]:
        """
        Perform complete log rotation process.

        Args:
            generate_checksums: Generate checksums after rotation

        Returns:
            Rotation result dictionary
        """
        results = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "operations": []
        }

        # 1. Rotate current log
        rotate_result = self._rotate_log()
        results["operations"].append({
            "operation": "rotate",
            "result": rotate_result
        })
        results["rotated"] = rotate_result.get("rotated_file")

        # 2. Compress old logs (older than 1 day)
        compress_result = self._compress_old_logs(days_old=1)
        results["operations"].append({
            "operation": "compress",
            "result": compress_result
        })
        results["compressed_count"] = compress_result["compressed_count"]

        # 3. Cleanup logs beyond retention
        cleanup_result = self._cleanup_old_logs()
        results["operations"].append({
            "operation": "cleanup",
            "result": cleanup_result
        })
        results["deleted_count"] = cleanup_result["deleted_count"]

        # 4. Generate checksums if requested
        if generate_checksums:
            from scripts.audit_verify import IntegrityVerifier

            verifier = IntegrityVerifier(log_directory=str(self.log_directory))
            checksum_result = verifier.generate_checksums()

            results["operations"].append({
                "operation": "checksums",
                "result": checksum_result
            })
            results["checksums_generated"] = True

        return results

    def run_scheduled(self):
        """
        Run scheduled rotation (called by cron/scheduler).

        This is the main entry point for automated rotation.
        """
        print(f"Starting scheduled log rotation at {datetime.utcnow().isoformat()}")

        # Check for emergency rotation first
        if self._check_emergency_rotation():
            print("Emergency rotation needed (file size limit exceeded)")
            emergency_result = self._emergency_rotate()
            print(f"Emergency rotation result: {emergency_result}")

        # Perform regular rotation
        result = self.rotate(generate_checksums=True)

        print(f"Rotation completed:")
        print(f"  - Compressed: {result.get('compressed_count', 0)} files")
        print(f"  - Deleted: {result.get('deleted_count', 0)} files")
        print(f"  - Checksums: {'Generated' if result.get('checksums_generated') else 'Skipped'}")

        return result


def main():
    """CLI interface for log rotation."""
    import argparse

    parser = argparse.ArgumentParser(description='Rotate and manage audit logs')
    parser.add_argument('--rotate', action='store_true', help='Perform log rotation')
    parser.add_argument('--compress', action='store_true', help='Compress old logs')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old logs')
    parser.add_argument('--emergency', action='store_true', help='Emergency rotation (size-based)')
    parser.add_argument('--scheduled', action='store_true', help='Run scheduled rotation (full process)')
    parser.add_argument('--retention-days', type=int, default=90, help='Retention period in days')
    parser.add_argument('--max-size-mb', type=int, default=100, help='Max file size in MB')
    parser.add_argument('--log-dir', default='AI_Employee_Vault/Logs', help='Log directory')
    parser.add_argument('--checksums', action='store_true', help='Generate checksums after rotation')

    args = parser.parse_args()

    rotator = LogRotator(
        log_directory=args.log_dir,
        retention_days=args.retention_days,
        max_size_mb=args.max_size_mb
    )

    # Scheduled rotation (full process)
    if args.scheduled:
        result = rotator.run_scheduled()
        print(json.dumps(result, indent=2))
        return

    # Emergency rotation
    if args.emergency:
        if rotator._check_emergency_rotation():
            result = rotator._emergency_rotate()
            print(json.dumps(result, indent=2))
        else:
            print("Emergency rotation not needed")
        return

    # Compress old logs
    if args.compress:
        result = rotator._compress_old_logs()
        print(json.dumps(result, indent=2))
        return

    # Cleanup old logs
    if args.cleanup:
        result = rotator._cleanup_old_logs()
        print(json.dumps(result, indent=2))
        return

    # Full rotation
    if args.rotate:
        result = rotator.rotate(generate_checksums=args.checksums)
        print(json.dumps(result, indent=2))
        return

    # No action specified
    parser.print_help()


if __name__ == "__main__":
    main()
