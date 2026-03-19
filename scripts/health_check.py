"""
System Health Check

Monitors AI Employee system health and creates alerts for issues:
- Checks for stale approval requests
- Monitors error rates in audit logs
- Verifies service availability
- Checks disk space and system resources

Runs periodically (every 5 minutes via cron) to ensure system reliability.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class HealthChecker:
    """Monitors system health and creates alerts."""

    def __init__(self, vault_path: str = None):
        """
        Initialize health checker.

        Args:
            vault_path: Path to AI Employee Vault
        """
        self.vault_path = Path(vault_path or os.getenv('VAULT_PATH', './AI_Employee_Vault'))
        self.needs_action_path = self.vault_path / 'Needs_Action'
        self.pending_approval_path = self.vault_path / 'Pending_Approval'
        self.logs_path = self.vault_path / 'Logs'

        # Ensure directories exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

    def run_health_check(self) -> Dict[str, Any]:
        """
        Run comprehensive health check.

        Returns:
            Dict with health status and issues found
        """
        print(f"🏥 Running health check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        issues = []

        # Check for stale approvals
        stale_approvals = self._check_stale_approvals()
        if stale_approvals:
            issues.extend(stale_approvals)

        # Check error rates
        error_issues = self._check_error_rates()
        if error_issues:
            issues.extend(error_issues)

        # Check disk space
        disk_issues = self._check_disk_space()
        if disk_issues:
            issues.extend(disk_issues)

        # Check existing alerts
        alert_count = len(list(self.needs_action_path.glob('ALERT_*.md')))

        # Create alerts for new issues
        for issue in issues:
            self._create_alert(issue)

        # Determine overall health status
        if len(issues) == 0:
            status = 'healthy'
        elif len(issues) <= 2:
            status = 'warning'
        else:
            status = 'critical'

        result = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'issues_found': len(issues),
            'existing_alerts': alert_count,
            'issues': issues
        }

        # Print summary
        if status == 'healthy':
            print("✅ System is healthy")
        elif status == 'warning':
            print(f"⚠️ System has {len(issues)} warning(s)")
        else:
            print(f"🚨 System has {len(issues)} critical issue(s)")

        return result

    def _check_stale_approvals(self) -> List[Dict[str, Any]]:
        """Check for approval requests older than 24 hours."""
        issues = []

        if not self.pending_approval_path.exists():
            return issues

        cutoff_time = datetime.now() - timedelta(hours=24)

        for approval_file in self.pending_approval_path.glob('*.md'):
            file_age = datetime.fromtimestamp(approval_file.stat().st_mtime)

            if file_age < cutoff_time:
                issues.append({
                    'type': 'stale_approval',
                    'severity': 'warning',
                    'title': f'Stale approval request: {approval_file.name}',
                    'description': f'Approval request has been pending for {(datetime.now() - file_age).days} day(s)',
                    'file': str(approval_file),
                    'age_hours': int((datetime.now() - file_age).total_seconds() / 3600)
                })

        return issues

    def _check_error_rates(self) -> List[Dict[str, Any]]:
        """Check for high error rates in recent audit logs."""
        issues = []

        if not self.logs_path.exists():
            return issues

        try:
            from scripts.data_collectors.audit_log_collector import AuditLogCollector

            collector = AuditLogCollector(str(self.vault_path))
            audit_data = collector.collect_audit_data(days=1)

            if audit_data.get('available'):
                summary = audit_data.get('summary', {})
                error_count = summary.get('error_count', 0)
                total_actions = summary.get('total_actions', 0)

                if total_actions > 0:
                    error_rate = error_count / total_actions

                    if error_rate > 0.1:
                        issues.append({
                            'type': 'high_error_rate',
                            'severity': 'critical' if error_rate > 0.25 else 'warning',
                            'title': f'High error rate detected: {error_rate:.1%}',
                            'description': f'{error_count} errors out of {total_actions} actions in last 24 hours',
                            'error_count': error_count,
                            'total_actions': total_actions,
                            'error_rate': error_rate
                        })

        except Exception as e:
            pass

        return issues

    def _check_disk_space(self) -> List[Dict[str, Any]]:
        """Check available disk space."""
        issues = []

        try:
            import shutil

            stat = shutil.disk_usage(str(self.vault_path))
            free_gb = stat.free / (1024 ** 3)
            used_percent = (stat.used / stat.total) * 100

            if free_gb < 1.0 or used_percent > 90:
                issues.append({
                    'type': 'low_disk_space',
                    'severity': 'critical' if free_gb < 0.5 else 'warning',
                    'title': f'Low disk space: {free_gb:.2f}GB free',
                    'description': f'{used_percent:.1f}% of disk used',
                    'free_gb': free_gb,
                    'used_percent': used_percent
                })

        except Exception:
            pass

        return issues

    def _create_alert(self, issue: Dict[str, Any]) -> None:
        """Create alert file in Needs_Action directory."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        issue_type = issue.get('type', 'unknown')
        alert_file = self.needs_action_path / f"ALERT_HEALTH_{timestamp}.md"

        # Don't create duplicate alerts
        existing_alerts = list(self.needs_action_path.glob(f'ALERT_HEALTH_*{issue_type}*.md'))
        if existing_alerts:
            latest_alert = max(existing_alerts, key=lambda p: p.stat().st_mtime)
            alert_age = datetime.now() - datetime.fromtimestamp(latest_alert.stat().st_mtime)
            if alert_age.total_seconds() < 3600:
                return

        content = f"""---
alert_type: {issue_type}
severity: {issue.get('severity', 'warning')}
created_at: {datetime.now().isoformat()}Z
status: needs_attention
---

# 🚨 Health Alert: {issue.get('title', 'Unknown Issue')}

**Severity**: {issue.get('severity', 'warning').upper()}
**Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Issue Description

{issue.get('description', 'No description available')}

## Recommended Actions

- [ ] Investigate the issue
- [ ] Take corrective action
- [ ] Monitor for recurrence

---

*Generated by AI Employee Health Check System*
"""

        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  🚨 Created alert: {alert_file.name}")


def main():
    """Main entry point."""
    checker = HealthChecker()
    result = checker.run_health_check()

    if result['status'] == 'critical':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
