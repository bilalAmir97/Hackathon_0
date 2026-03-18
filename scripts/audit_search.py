"""
Audit Search - Query and search audit logs.

Provides functionality to:
- Search logs by action type, date range, result status
- Retrieve specific log entries by ID
- Trace complete workflows by workflow_id
- Support both .jsonl and .jsonl.gz compressed files
- Log all search operations for audit trail
"""

import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from scripts.audit_logger import AuditLogger


class AuditSearch:
    """Search and query audit logs."""

    def __init__(
        self,
        log_directory: str = "AI_Employee_Vault/Logs",
        config_path: Optional[str] = None
    ):
        """
        Initialize AuditSearch.

        Args:
            log_directory: Path to audit log directory
            config_path: Optional path to logging config (for AuditLogger)
        """
        self.log_directory = Path(log_directory)
        self.audit_logger = AuditLogger(config_path=config_path) if config_path else AuditLogger()

    def search(
        self,
        action_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        result: Optional[str] = None,
        actor: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters.

        Args:
            action_type: Filter by action type
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)
            result: Filter by result (success/failure)
            actor: Filter by actor
            limit: Maximum number of results

        Returns:
            List of matching log entries
        """
        # Log the search operation for audit trail (SR-007)
        self.audit_logger.log_action(
            action_type="audit_search",
            actor="audit_search",
            target="audit_logs",
            parameters={
                "filters": {
                    "action_type": action_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "result": result,
                    "actor": actor,
                    "limit": limit
                }
            },
            result="success"
        )
        self.audit_logger.flush()

        # Get list of log files in date range
        log_files = self._parse_date_range(start_date, end_date)

        results = []
        for log_file in log_files:
            # Read log file (handles both .jsonl and .jsonl.gz)
            for entry in self._open_log_file(log_file):
                # Apply filters
                if self._matches_filters(entry, action_type, result, actor, start_date, end_date):
                    results.append(entry)

                    # Check limit
                    if limit and len(results) >= limit:
                        return results

        return results

    def get_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific log entry by ID.

        Args:
            log_id: Log entry ID (UUID)

        Returns:
            Log entry dictionary or None if not found
        """
        # Search all log files
        log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))

        for log_file in log_files:
            for entry in self._open_log_file(log_file):
                if entry.get("id") == log_id:
                    return entry

        return None

    def trace_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Trace a complete workflow by workflow_id.

        Args:
            workflow_id: Workflow ID to trace

        Returns:
            List of log entries in chronological order
        """
        # Search all log files
        log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))

        workflow_entries = []
        for log_file in log_files:
            for entry in self._open_log_file(log_file):
                metadata = entry.get("metadata", {})
                if metadata.get("workflow_id") == workflow_id:
                    workflow_entries.append(entry)

        # Sort by timestamp
        workflow_entries.sort(key=lambda e: e.get("timestamp", ""))

        return workflow_entries

    def _open_log_file(self, log_file: Path) -> List[Dict[str, Any]]:
        """
        Open and read log file (handles .jsonl and .jsonl.gz).

        Args:
            log_file: Path to log file

        Returns:
            List of log entries
        """
        entries = []

        try:
            if log_file.suffix == '.gz':
                # Compressed file
                with gzip.open(log_file, 'rt', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            else:
                # Uncompressed file
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to read {log_file}: {e}")

        return entries

    def _parse_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Path]:
        """
        Get list of log files within date range.

        Args:
            start_date: Start date (ISO format YYYY-MM-DD)
            end_date: End date (ISO format YYYY-MM-DD)

        Returns:
            List of log file paths
        """
        all_log_files = sorted(self.log_directory.glob("audit_*.jsonl*"))

        if not start_date and not end_date:
            return all_log_files

        # Parse dates
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None

        filtered_files = []
        for log_file in all_log_files:
            # Extract date from filename: audit_YYYY-MM-DD.jsonl[.gz]
            filename = log_file.name
            if filename.startswith("audit_"):
                date_str = filename.replace("audit_", "").split(".")[0]
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    # Check if file date is in range
                    if start and file_date < start:
                        continue
                    if end and file_date > end:
                        continue

                    filtered_files.append(log_file)
                except ValueError:
                    # Invalid date format, skip
                    continue

        return filtered_files

    def _matches_filters(
        self,
        entry: Dict[str, Any],
        action_type: Optional[str] = None,
        result: Optional[str] = None,
        actor: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bool:
        """
        Check if log entry matches all filters.

        Args:
            entry: Log entry to check
            action_type: Filter by action type
            result: Filter by result
            actor: Filter by actor
            start_date: Start date filter
            end_date: End date filter

        Returns:
            True if entry matches all filters
        """
        # Action type filter
        if action_type and entry.get("action_type") != action_type:
            return False

        # Result filter
        if result and entry.get("result") != result:
            return False

        # Actor filter
        if actor and entry.get("actor") != actor:
            return False

        # Date range filter (already filtered by file, but double-check)
        if start_date or end_date:
            entry_timestamp = entry.get("timestamp", "")
            if entry_timestamp:
                try:
                    entry_date = datetime.fromisoformat(entry_timestamp.replace('Z', '')).date()

                    if start_date:
                        start = datetime.fromisoformat(start_date).date()
                        if entry_date < start:
                            return False

                    if end_date:
                        end = datetime.fromisoformat(end_date).date()
                        if entry_date > end:
                            return False
                except ValueError:
                    pass

        return True


def main():
    """CLI interface for audit search."""
    import argparse

    parser = argparse.ArgumentParser(description='Search audit logs')
    parser.add_argument('--action-type', help='Filter by action type')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--result', choices=['success', 'failure'], help='Filter by result')
    parser.add_argument('--actor', help='Filter by actor')
    parser.add_argument('--limit', type=int, help='Maximum number of results')
    parser.add_argument('--log-id', help='Get specific log entry by ID')
    parser.add_argument('--workflow-id', help='Trace workflow by workflow_id')
    parser.add_argument('--log-dir', default='AI_Employee_Vault/Logs', help='Log directory')

    args = parser.parse_args()

    searcher = AuditSearch(log_directory=args.log_dir)

    # Get by ID
    if args.log_id:
        entry = searcher.get_by_id(args.log_id)
        if entry:
            print(json.dumps(entry, indent=2))
        else:
            print(f"Log entry not found: {args.log_id}")
        return

    # Trace workflow
    if args.workflow_id:
        entries = searcher.trace_workflow(args.workflow_id)
        print(f"Found {len(entries)} entries for workflow {args.workflow_id}:")
        for entry in entries:
            print(json.dumps(entry, indent=2))
        return

    # Search with filters
    results = searcher.search(
        action_type=args.action_type,
        start_date=args.start_date,
        end_date=args.end_date,
        result=args.result,
        actor=args.actor,
        limit=args.limit
    )

    print(f"Found {len(results)} matching entries:")
    for entry in results:
        print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main()
