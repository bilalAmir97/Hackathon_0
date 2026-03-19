"""
Audit Log Data Collector

Collects and analyzes audit log data from the AI Employee system.
Retrieves action counts, approval workflow metrics, and system health.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AuditLogCollector:
    """Collects and analyzes audit log data."""

    def __init__(self, vault_path: Optional[str] = None):
        """
        Initialize audit log collector.

        Args:
            vault_path: Path to AI Employee Vault (default: from env)
        """
        self.vault_path = Path(vault_path or os.getenv('VAULT_PATH', './AI_Employee_Vault'))
        self.logs_path = self.vault_path / 'Logs'

    def collect_audit_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Collect and analyze audit log data.

        Args:
            days: Number of days to look back

        Returns:
            Dict with action counts, approval metrics, errors
        """
        if not self.logs_path.exists():
            return {
                'available': False,
                'message': 'Audit logs directory not found'
            }

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Collect log files
            log_files = list(self.logs_path.glob('audit_*.jsonl'))

            # Parse logs
            actions_by_type = defaultdict(int)
            approvals_granted = 0
            approvals_denied = 0
            errors = []
            total_actions = 0

            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())

                                # Check if within date range
                                timestamp = entry.get('timestamp', '')
                                if timestamp:
                                    log_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    if log_date < start_date or log_date > end_date:
                                        continue

                                # Count actions
                                action_type = entry.get('action_type', 'unknown')
                                actions_by_type[action_type] += 1
                                total_actions += 1

                                # Count approvals
                                if action_type == 'approval_granted':
                                    approvals_granted += 1
                                elif action_type == 'approval_denied':
                                    approvals_denied += 1

                                # Collect errors
                                if entry.get('error'):
                                    errors.append({
                                        'timestamp': timestamp,
                                        'action_type': action_type,
                                        'error': entry.get('error')
                                    })

                            except json.JSONDecodeError:
                                continue

                except Exception as e:
                    continue

            # Calculate metrics
            approval_rate = 0.0
            if approvals_granted + approvals_denied > 0:
                approval_rate = approvals_granted / (approvals_granted + approvals_denied)

            return {
                'available': True,
                'period_days': days,
                'summary': {
                    'total_actions': total_actions,
                    'approvals_granted': approvals_granted,
                    'approvals_denied': approvals_denied,
                    'approval_rate': round(approval_rate, 2),
                    'error_count': len(errors)
                },
                'actions_by_type': dict(actions_by_type),
                'recent_errors': errors[-10:],  # Last 10 errors
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }

    def collect_approval_workflow_metrics(self) -> Dict[str, Any]:
        """
        Collect approval workflow metrics.

        Returns:
            Dict with pending, approved, rejected counts
        """
        try:
            pending_path = self.vault_path / 'Pending_Approval'
            approved_path = self.vault_path / 'Approved'
            rejected_path = self.vault_path / 'Rejected'
            done_path = self.vault_path / 'Done'

            return {
                'pending_count': len(list(pending_path.glob('*.md'))) if pending_path.exists() else 0,
                'approved_count': len(list(approved_path.glob('*.md'))) if approved_path.exists() else 0,
                'rejected_count': len(list(rejected_path.glob('*.md'))) if rejected_path.exists() else 0,
                'done_count': len(list(done_path.glob('*.md'))) if done_path.exists() else 0,
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }

    def collect_system_health(self) -> Dict[str, Any]:
        """
        Collect system health indicators.

        Returns:
            Dict with health alerts and system status
        """
        try:
            needs_action_path = self.vault_path / 'Needs_Action'

            alerts = []
            if needs_action_path.exists():
                alert_files = list(needs_action_path.glob('ALERT_*.md'))
                for alert_file in alert_files:
                    alerts.append({
                        'filename': alert_file.name,
                        'created': datetime.fromtimestamp(alert_file.stat().st_mtime).isoformat()
                    })

            return {
                'alert_count': len(alerts),
                'alerts': alerts[-10:],  # Last 10 alerts
                'system_status': 'healthy' if len(alerts) == 0 else 'needs_attention',
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }


def collect_audit_data(days: int = 7) -> Dict[str, Any]:
    """
    Convenience function to collect audit data.

    Args:
        days: Number of days to look back

    Returns:
        Dict with audit logs, workflow metrics, and system health
    """
    collector = AuditLogCollector()

    return {
        'audit_logs': collector.collect_audit_data(days),
        'workflow_metrics': collector.collect_approval_workflow_metrics(),
        'system_health': collector.collect_system_health()
    }


if __name__ == "__main__":
    """Test the collector."""
    print("Collecting audit data...")
    data = collect_audit_data()

    print("\n=== Audit Log Summary ===")
    audit = data.get('audit_logs', {})
    if audit.get('available'):
        summary = audit.get('summary', {})
        print(f"Total Actions: {summary.get('total_actions', 0)}")
        print(f"Approvals Granted: {summary.get('approvals_granted', 0)}")
        print(f"Approvals Denied: {summary.get('approvals_denied', 0)}")
        print(f"Approval Rate: {summary.get('approval_rate', 0):.0%}")
        print(f"Errors: {summary.get('error_count', 0)}")

    print("\n=== Workflow Metrics ===")
    workflow = data.get('workflow_metrics', {})
    print(f"Pending: {workflow.get('pending_count', 0)}")
    print(f"Done: {workflow.get('done_count', 0)}")

    print("\n=== System Health ===")
    health = data.get('system_health', {})
    print(f"Status: {health.get('system_status', 'unknown')}")
    print(f"Alerts: {health.get('alert_count', 0)}")
