"""
Compliance Reporter - Generate compliance reports for regulatory audits.

Provides functionality to:
- Generate reports in JSON, CSV, and Markdown formats
- Verify 90-day retention policy compliance
- Export user data for GDPR compliance
- Support quarterly and custom date range reporting
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from scripts.audit_search import AuditSearch


class ComplianceReporter:
    """Generate compliance reports for regulatory audits."""

    def __init__(
        self,
        log_directory: str = "AI_Employee_Vault/Logs",
        config_path: Optional[str] = None
    ):
        """
        Initialize ComplianceReporter.

        Args:
            log_directory: Path to audit log directory
            config_path: Optional path to logging config
        """
        self.log_directory = Path(log_directory)
        self.searcher = AuditSearch(log_directory=log_directory, config_path=config_path)

    def generate_report(
        self,
        start_date: str,
        end_date: str,
        format: str = "json",
        output_file: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate compliance report for date range.

        Args:
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)
            format: Output format (json, csv, markdown)
            output_file: Optional output file path

        Returns:
            Report dictionary (for JSON format) or None (for file outputs)
        """
        # Search all logs in date range
        entries = self.searcher.search(
            start_date=start_date,
            end_date=end_date
        )

        # Generate report metadata
        metadata = {
            "report_type": "compliance_audit",
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "format": format,
            "total_entries": len(entries)
        }

        if format == "json":
            report = {
                "metadata": metadata,
                "entries": entries
            }

            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2)
                return None

            return report

        elif format == "csv":
            self._generate_csv_report(entries, metadata, output_file)
            return None

        elif format == "markdown":
            self._generate_markdown_report(entries, metadata, output_file)
            return None

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_csv_report(
        self,
        entries: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        output_file: str
    ):
        """Generate CSV format report."""
        if not entries:
            return

        with open(output_file, 'w', newline='') as f:
            # Get all unique field names
            fieldnames = set()
            for entry in entries:
                fieldnames.update(entry.keys())

            fieldnames = sorted(fieldnames)

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for entry in entries:
                # Flatten nested structures for CSV
                flat_entry = {}
                for key, value in entry.items():
                    if isinstance(value, (dict, list)):
                        flat_entry[key] = json.dumps(value)
                    else:
                        flat_entry[key] = value

                writer.writerow(flat_entry)

    def _generate_markdown_report(
        self,
        entries: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        output_file: str
    ):
        """Generate Markdown format report."""
        with open(output_file, 'w') as f:
            # Header
            f.write("# Compliance Report\n\n")

            # Metadata
            f.write("## Summary\n\n")
            f.write(f"- **Report Type**: {metadata['report_type']}\n")
            f.write(f"- **Generated**: {metadata['generated_at']}\n")
            f.write(f"- **Date Range**: {metadata['date_range']['start']} to {metadata['date_range']['end']}\n")
            f.write(f"- **Total Entries**: {metadata['total_entries']}\n\n")

            # Entries
            f.write("## Log Entries\n\n")

            for i, entry in enumerate(entries, 1):
                f.write(f"### Entry {i}\n\n")
                f.write(f"- **ID**: {entry.get('id', 'N/A')}\n")
                f.write(f"- **Timestamp**: {entry.get('timestamp', 'N/A')}\n")
                f.write(f"- **Action Type**: {entry.get('action_type', 'N/A')}\n")
                f.write(f"- **Actor**: {entry.get('actor', 'N/A')}\n")
                f.write(f"- **Target**: {entry.get('target', 'N/A')}\n")
                f.write(f"- **Result**: {entry.get('result', 'N/A')}\n")

                if entry.get('error'):
                    f.write(f"- **Error**: {entry['error']}\n")

                f.write("\n")

    def verify_retention(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        Verify log retention policy compliance.

        Args:
            retention_days: Number of days to retain logs (default: 90)

        Returns:
            Retention verification report
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Get all log files
        log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))

        files_within_retention = []
        files_beyond_retention = []

        for log_file in log_files:
            # Extract date from filename
            filename = log_file.name
            if filename.startswith("audit_"):
                date_str = filename.replace("audit_", "").split(".")[0]
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        files_beyond_retention.append({
                            "file": filename,
                            "date": file_date.isoformat(),
                            "age_days": (datetime.utcnow() - file_date).days
                        })
                    else:
                        files_within_retention.append({
                            "file": filename,
                            "date": file_date.isoformat(),
                            "age_days": (datetime.utcnow() - file_date).days
                        })
                except ValueError:
                    # Invalid date format, skip
                    continue

        # Determine compliance status
        if files_beyond_retention:
            compliance_status = "action_required"
            message = f"{len(files_beyond_retention)} log file(s) exceed {retention_days}-day retention policy"
        else:
            compliance_status = "compliant"
            message = f"All logs within {retention_days}-day retention policy"

        return {
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat() + 'Z',
            "total_files": len(log_files),
            "files_within_retention": len(files_within_retention),
            "files_beyond_retention": len(files_beyond_retention),
            "compliance_status": compliance_status,
            "message": message,
            "files_to_archive": files_beyond_retention
        }

    def export_user_data(self, user_identifier: str) -> Dict[str, Any]:
        """
        Export all data related to a specific user (GDPR compliance).

        Args:
            user_identifier: User email or identifier

        Returns:
            User data export dictionary
        """
        # Search all log files for entries mentioning the user
        all_entries = self.searcher.search()

        user_entries = []
        for entry in all_entries:
            # Check if user identifier appears anywhere in the entry
            entry_str = json.dumps(entry)
            if user_identifier in entry_str:
                user_entries.append(entry)

        return {
            "user_identifier": user_identifier,
            "export_date": datetime.utcnow().isoformat() + 'Z',
            "total_entries": len(user_entries),
            "entries": user_entries,
            "data_categories": self._categorize_user_data(user_entries)
        }

    def _categorize_user_data(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize user data by action type."""
        categories = {}
        for entry in entries:
            action_type = entry.get("action_type", "unknown")
            categories[action_type] = categories.get(action_type, 0) + 1
        return categories


def main():
    """CLI interface for compliance reporting."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate compliance reports')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--format', choices=['json', 'csv', 'markdown'], default='json', help='Output format')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--verify-retention', action='store_true', help='Verify retention policy')
    parser.add_argument('--retention-days', type=int, default=90, help='Retention period in days')
    parser.add_argument('--export-user', help='Export data for specific user (GDPR)')
    parser.add_argument('--log-dir', default='AI_Employee_Vault/Logs', help='Log directory')

    args = parser.parse_args()

    reporter = ComplianceReporter(log_directory=args.log_dir)

    # Verify retention
    if args.verify_retention:
        retention_report = reporter.verify_retention(retention_days=args.retention_days)
        print(json.dumps(retention_report, indent=2))
        return

    # Export user data
    if args.export_user:
        user_data = reporter.export_user_data(user_identifier=args.export_user)
        print(json.dumps(user_data, indent=2))
        return

    # Generate compliance report
    report = reporter.generate_report(
        start_date=args.start_date,
        end_date=args.end_date,
        format=args.format,
        output_file=args.output
    )

    if report:
        print(json.dumps(report, indent=2))
    else:
        print(f"Report generated: {args.output}")


if __name__ == "__main__":
    main()
