"""
Audit Verify - Log integrity verification using checksums.

Provides functionality to:
- Calculate SHA-256 checksums for log files
- Store checksums in .checksums.json
- Verify log files against stored checksums
- Detect tampering and modifications
- Support both regular and compressed log files
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class IntegrityVerifier:
    """Verify integrity of audit log files using checksums."""

    def __init__(self, log_directory: str = "AI_Employee_Vault/Logs"):
        """
        Initialize IntegrityVerifier.

        Args:
            log_directory: Path to audit log directory
        """
        self.log_directory = Path(log_directory)
        self.checksum_file = self.log_directory / ".checksums.json"

    def _calculate_checksum(self, file_path: str) -> str:
        """
        Calculate SHA-256 checksum for a file.

        Args:
            file_path: Path to file

        Returns:
            SHA-256 checksum as hex string
        """
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _load_checksums(self) -> Optional[Dict[str, Any]]:
        """
        Load checksums from .checksums.json file.

        Returns:
            Checksums dictionary or None if file doesn't exist
        """
        if not self.checksum_file.exists():
            return None

        try:
            with open(self.checksum_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading checksums: {e}")
            return None

    def _save_checksums(self, checksums: Dict[str, Any]):
        """
        Save checksums to .checksums.json file.

        Args:
            checksums: Checksums dictionary to save
        """
        try:
            with open(self.checksum_file, 'w') as f:
                json.dump(checksums, f, indent=2)
        except Exception as e:
            print(f"Error saving checksums: {e}")

    def generate_checksums(self) -> Dict[str, Any]:
        """
        Generate checksums for all log files.

        Returns:
            Dictionary with generation results
        """
        log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))

        checksums = {
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "files": {}
        }

        for log_file in log_files:
            try:
                checksum = self._calculate_checksum(str(log_file))
                checksums["files"][log_file.name] = {
                    "checksum": checksum,
                    "size": log_file.stat().st_size,
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
            except Exception as e:
                print(f"Error calculating checksum for {log_file.name}: {e}")

        # Save checksums
        self._save_checksums(checksums)

        return {
            "status": "success",
            "total_files": len(checksums["files"]),
            "checksum_file": str(self.checksum_file)
        }

    def verify_file(self, file_path: str) -> Dict[str, Any]:
        """
        Verify integrity of a specific log file.

        Args:
            file_path: Path to log file

        Returns:
            Verification result dictionary
        """
        file_path = Path(file_path)
        filename = file_path.name

        # Load stored checksums
        stored_checksums = self._load_checksums()
        if not stored_checksums:
            return {
                "status": "error",
                "file": filename,
                "message": "Checksum file not found. Run generate_checksums() first."
            }

        # Check if file has a stored checksum
        if filename not in stored_checksums["files"]:
            return {
                "status": "error",
                "file": filename,
                "message": "No stored checksum found for this file"
            }

        # Calculate current checksum
        try:
            current_checksum = self._calculate_checksum(str(file_path))
            stored_checksum = stored_checksums["files"][filename]["checksum"]

            if current_checksum == stored_checksum:
                return {
                    "status": "pass",
                    "file": filename,
                    "checksum": current_checksum,
                    "message": "File integrity verified"
                }
            else:
                return {
                    "status": "fail",
                    "file": filename,
                    "stored_checksum": stored_checksum,
                    "current_checksum": current_checksum,
                    "message": "File has been modified (checksum mismatch)"
                }
        except Exception as e:
            return {
                "status": "error",
                "file": filename,
                "message": f"Error verifying file: {str(e)}"
            }

    def verify_all(self) -> Dict[str, Any]:
        """
        Verify integrity of all log files.

        Returns:
            Verification report dictionary
        """
        # Load stored checksums
        stored_checksums = self._load_checksums()
        if not stored_checksums:
            return {
                "status": "error",
                "message": "Checksum file not found. Run generate_checksums() first.",
                "total_files": 0,
                "verified_files": 0,
                "tampered_files": 0,
                "tampered": []
            }

        # Get all log files
        log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))

        verified_count = 0
        tampered_count = 0
        tampered_files = []

        for log_file in log_files:
            result = self.verify_file(str(log_file))

            if result["status"] == "pass":
                verified_count += 1
            elif result["status"] == "fail":
                tampered_count += 1
                tampered_files.append({
                    "file": result["file"],
                    "stored_checksum": result["stored_checksum"],
                    "current_checksum": result["current_checksum"]
                })

        # Determine overall status
        if tampered_count > 0:
            status = "fail"
            message = f"Tampering detected: {tampered_count} file(s) modified"
        else:
            status = "pass"
            message = f"All {verified_count} file(s) verified successfully"

        return {
            "status": status,
            "message": message,
            "verified_at": datetime.utcnow().isoformat() + 'Z',
            "total_files": len(log_files),
            "verified_files": verified_count,
            "tampered_files": tampered_count,
            "tampered": tampered_files
        }

    def verify_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Verify integrity of log files within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Verification report for date range
        """
        from datetime import datetime as dt

        start = dt.fromisoformat(start_date).date()
        end = dt.fromisoformat(end_date).date()

        # Get log files in date range
        log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))
        filtered_files = []

        for log_file in log_files:
            # Extract date from filename
            filename = log_file.name
            if filename.startswith("audit_"):
                date_str = filename.replace("audit_", "").split(".")[0]
                try:
                    file_date = dt.strptime(date_str, "%Y-%m-%d").date()
                    if start <= file_date <= end:
                        filtered_files.append(log_file)
                except ValueError:
                    continue

        # Verify filtered files
        verified_count = 0
        tampered_count = 0
        tampered_files = []

        for log_file in filtered_files:
            result = self.verify_file(str(log_file))

            if result["status"] == "pass":
                verified_count += 1
            elif result["status"] == "fail":
                tampered_count += 1
                tampered_files.append({
                    "file": result["file"],
                    "stored_checksum": result["stored_checksum"],
                    "current_checksum": result["current_checksum"]
                })

        status = "fail" if tampered_count > 0 else "pass"

        return {
            "status": status,
            "date_range": {"start": start_date, "end": end_date},
            "total_files": len(filtered_files),
            "verified_files": verified_count,
            "tampered_files": tampered_count,
            "tampered": tampered_files
        }


def main():
    """CLI interface for integrity verification."""
    import argparse

    parser = argparse.ArgumentParser(description='Verify audit log integrity')
    parser.add_argument('--generate', action='store_true', help='Generate checksums for all log files')
    parser.add_argument('--verify-all', action='store_true', help='Verify all log files')
    parser.add_argument('--verify-file', help='Verify specific log file')
    parser.add_argument('--verify-date', nargs=2, metavar=('START', 'END'), help='Verify logs in date range (YYYY-MM-DD)')
    parser.add_argument('--log-dir', default='AI_Employee_Vault/Logs', help='Log directory')

    args = parser.parse_args()

    verifier = IntegrityVerifier(log_directory=args.log_dir)

    # Generate checksums
    if args.generate:
        result = verifier.generate_checksums()
        print(json.dumps(result, indent=2))
        return

    # Verify all files
    if args.verify_all:
        result = verifier.verify_all()
        print(json.dumps(result, indent=2))
        return

    # Verify specific file
    if args.verify_file:
        result = verifier.verify_file(args.verify_file)
        print(json.dumps(result, indent=2))
        return

    # Verify date range
    if args.verify_date:
        start_date, end_date = args.verify_date
        result = verifier.verify_date_range(start_date, end_date)
        print(json.dumps(result, indent=2))
        return

    # No action specified
    parser.print_help()


if __name__ == "__main__":
    main()
