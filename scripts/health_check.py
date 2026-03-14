#!/usr/bin/env python3
"""
System Health Check

Monitors AI Employee system health and alerts on issues.
Runs every 5 minutes via cron.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class HealthCheck:
    """Monitor system health"""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.logs = self.vault_path / "Logs"
        self.needs_action = self.vault_path / "Needs_Action"
        self.health_log = self.logs / "health_checks.json"

    def check_watchers(self) -> Dict:
        """Check if watcher processes are running"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            output = result.stdout

            watchers = {
                "whatsapp_watcher": "whatsapp_watcher.py" in output,
                "whatsapp_processor": "auto_process_whatsapp.py" in output,
                "gmail_watcher": "gmail_watcher.py" in output
            }

            return {
                "status": "healthy" if all(watchers.values()) else "degraded",
                "watchers": watchers,
                "running_count": sum(watchers.values()),
                "total_count": len(watchers)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_disk_space(self) -> Dict:
        """Check available disk space"""
        try:
            vault_size = sum(
                f.stat().st_size for f in self.vault_path.rglob("*") if f.is_file()
            )
            vault_size_mb = vault_size / (1024 * 1024)

            return {
                "status": "healthy",
                "vault_size_mb": round(vault_size_mb, 2)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_pending_queue(self) -> Dict:
        """Check if pending queue is growing too large"""
        try:
            pending_count = len(list(self.needs_action.glob("*.md")))

            status = "healthy"
            if pending_count > 50:
                status = "warning"
            elif pending_count > 100:
                status = "critical"

            return {
                "status": status,
                "pending_count": pending_count,
                "threshold_warning": 50,
                "threshold_critical": 100
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_recent_activity(self) -> Dict:
        """Check if system has processed anything recently"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.logs / f"{today}.json"

            if not log_file.exists():
                return {
                    "status": "warning",
                    "message": "No activity today"
                }

            with open(log_file, 'r') as f:
                logs = json.load(f)

            recent_logs = [
                log for log in logs
                if (datetime.now() - datetime.fromisoformat(log.get("timestamp", "2000-01-01T00:00:00Z").replace("Z", ""))).seconds < 3600
            ]

            return {
                "status": "healthy" if recent_logs else "warning",
                "activity_last_hour": len(recent_logs),
                "activity_today": len(logs)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_and_run_daily_briefing(self) -> Dict:
        """Check if daily briefing has run today, run it if not (catch-up mechanism)"""
        try:
            dashboard_file = self.vault_path / "Dashboard.md"

            if not dashboard_file.exists():
                return {
                    "status": "skipped",
                    "reason": "Dashboard.md not found"
                }

            # Check when Dashboard.md was last modified
            last_modified = datetime.fromtimestamp(dashboard_file.stat().st_mtime)
            today = datetime.now().date()

            # If Dashboard was modified today, briefing already ran
            if last_modified.date() == today:
                return {
                    "status": "current",
                    "last_updated": last_modified.isoformat(),
                    "message": "Briefing already ran today"
                }

            # Dashboard is outdated, run briefing now (catch-up)
            print("📋 Dashboard outdated, running daily briefing (catch-up)...")

            result = subprocess.run(
                ["uv", "run", "python", "scripts/daily_briefing.py"],
                capture_output=True,
                text=True,
                cwd=self.vault_path.parent
            )

            if result.returncode == 0:
                return {
                    "status": "executed",
                    "message": "Daily briefing catch-up successful",
                    "last_updated": last_modified.isoformat(),
                    "now_updated": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "failed",
                    "error": result.stderr,
                    "message": "Daily briefing catch-up failed"
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def run_health_check(self) -> Dict:
        """Run all health checks"""
        checks = {
            "timestamp": datetime.now().isoformat(),
            "watchers": self.check_watchers(),
            "disk": self.check_disk_space(),
            "queue": self.check_pending_queue(),
            "activity": self.check_recent_activity(),
            "daily_briefing": self.check_and_run_daily_briefing()
        }

        # Determine overall status
        statuses = [
            checks["watchers"]["status"],
            checks["disk"]["status"],
            checks["queue"]["status"],
            checks["activity"]["status"]
        ]

        if "error" in statuses or "critical" in statuses:
            checks["overall_status"] = "critical"
        elif "degraded" in statuses or "warning" in statuses:
            checks["overall_status"] = "warning"
        else:
            checks["overall_status"] = "healthy"

        return checks

    def log_health_check(self, checks: Dict):
        """Log health check results"""
        self.logs.mkdir(exist_ok=True)

        # Load existing health checks
        health_checks = []
        if self.health_log.exists():
            try:
                with open(self.health_log, 'r') as f:
                    health_checks = json.load(f)
            except:
                health_checks = []

        # Add new check
        health_checks.append(checks)

        # Keep only last 1000 checks
        health_checks = health_checks[-1000:]

        # Save
        with open(self.health_log, 'w') as f:
            json.dump(health_checks, f, indent=2)

    def create_alert_if_needed(self, checks: Dict):
        """Create alert file if system is unhealthy"""
        if checks["overall_status"] in ["critical", "warning"]:
            alert_file = self.needs_action / f"ALERT_HEALTH_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            content = f"""---
type: system_alert
severity: {checks['overall_status']}
created: {checks['timestamp']}
---

## System Health Alert

**Status**: {checks['overall_status'].upper()}

### Issues Detected

"""

            # Add specific issues
            if checks["watchers"]["status"] != "healthy":
                content += f"- **Watchers**: {checks['watchers']['running_count']}/{checks['watchers']['total_count']} running\n"

            if checks["queue"]["status"] != "healthy":
                content += f"- **Queue**: {checks['queue']['pending_count']} pending items (threshold: {checks['queue']['threshold_warning']})\n"

            if checks["activity"]["status"] != "healthy":
                content += f"- **Activity**: {checks['activity'].get('message', 'Low activity')}\n"

            content += "\n### Action Required\n\nReview system logs and restart failed components.\n"

            alert_file.write_text(content)
            print(f"⚠️  Alert created: {alert_file.name}")


def main():
    """Main entry point"""
    health = HealthCheck()
    checks = health.run_health_check()

    # Print summary
    print(f"Health Check: {checks['overall_status'].upper()}")
    print(f"  Watchers: {checks['watchers']['running_count']}/{checks['watchers']['total_count']}")
    print(f"  Queue: {checks['queue']['pending_count']} pending")
    print(f"  Activity: {checks['activity'].get('activity_last_hour', 0)} in last hour")

    # Log results
    health.log_health_check(checks)

    # Create alert if needed
    health.create_alert_if_needed(checks)

    # Exit with appropriate code
    if checks["overall_status"] == "critical":
        exit(2)
    elif checks["overall_status"] == "warning":
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
