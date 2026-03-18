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
from scripts.audit_logger import AuditLogger
from scripts.error_recovery.recovery_state import RecoveryState
from scripts.error_recovery.service_health import ServiceHealth


class HealthCheck:
    """Monitor system health"""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.logs = self.vault_path / "Logs"
        self.needs_action = self.vault_path / "Needs_Action"
        self.health_log = self.logs / "health_checks.json"
        self.audit_logger = AuditLogger()

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

    def check_circuit_breakers(self) -> Dict:
        """Check circuit breaker states for all services"""
        try:
            # Load recovery state
            recovery_state = RecoveryState.load()

            circuit_breakers = recovery_state.circuit_breakers

            if not circuit_breakers:
                return {
                    "status": "healthy",
                    "message": "No circuit breakers registered",
                    "open_circuits": [],
                    "half_open_circuits": []
                }

            open_circuits = []
            half_open_circuits = []

            for service_name, cb_state in circuit_breakers.items():
                state = cb_state.get("state", "CLOSED")
                if state == "OPEN":
                    open_circuits.append({
                        "service": service_name,
                        "failure_count": cb_state.get("failure_count", 0),
                        "last_failure": cb_state.get("last_failure_time")
                    })
                elif state == "HALF_OPEN":
                    half_open_circuits.append({
                        "service": service_name,
                        "failure_count": cb_state.get("failure_count", 0)
                    })

            # Determine status
            if open_circuits:
                status = "critical"
            elif half_open_circuits:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "total_circuits": len(circuit_breakers),
                "open_circuits": open_circuits,
                "half_open_circuits": half_open_circuits,
                "open_count": len(open_circuits),
                "half_open_count": len(half_open_circuits)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_service_degradation(self) -> Dict:
        """Check for degraded services"""
        try:
            # Load service health
            service_health = ServiceHealth.load()

            services = service_health.services

            if not services:
                return {
                    "status": "healthy",
                    "message": "No services registered",
                    "degraded_services": []
                }

            degraded_services = []
            critical_degraded = []

            for service_name, health_data in services.items():
                health_status = health_data.get("health_status", "HEALTHY")
                is_critical = health_data.get("is_critical", False)

                if health_status == "DEGRADED":
                    service_info = {
                        "service": service_name,
                        "is_critical": is_critical,
                        "consecutive_failures": health_data.get("consecutive_failures", 0),
                        "last_check": health_data.get("last_check_time")
                    }
                    degraded_services.append(service_info)

                    if is_critical:
                        critical_degraded.append(service_info)

            # Determine status
            if critical_degraded:
                status = "critical"
            elif degraded_services:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "total_services": len(services),
                "degraded_services": degraded_services,
                "degraded_count": len(degraded_services),
                "critical_degraded_count": len(critical_degraded)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_restart_attempts(self) -> Dict:
        """Check for excessive restart attempts"""
        try:
            # Load service health
            service_health = ServiceHealth.load()

            services = service_health.services

            if not services:
                return {
                    "status": "healthy",
                    "message": "No services registered",
                    "services_with_restarts": []
                }

            services_with_restarts = []
            excessive_restarts = []

            for service_name, health_data in services.items():
                restart_count = health_data.get("restart_count", 0)

                if restart_count > 0:
                    service_info = {
                        "service": service_name,
                        "restart_count": restart_count,
                        "last_restart": health_data.get("last_restart_time")
                    }
                    services_with_restarts.append(service_info)

                    # Threshold: more than 3 restarts is excessive
                    if restart_count > 3:
                        excessive_restarts.append(service_info)

            # Determine status
            if excessive_restarts:
                status = "critical"
            elif services_with_restarts:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "services_with_restarts": services_with_restarts,
                "restart_count": len(services_with_restarts),
                "excessive_restart_count": len(excessive_restarts)
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
            "daily_briefing": self.check_and_run_daily_briefing(),
            "circuit_breakers": self.check_circuit_breakers(),
            "service_degradation": self.check_service_degradation(),
            "restart_attempts": self.check_restart_attempts()
        }

        # Determine overall status
        statuses = [
            checks["watchers"]["status"],
            checks["disk"]["status"],
            checks["queue"]["status"],
            checks["activity"]["status"],
            checks["circuit_breakers"]["status"],
            checks["service_degradation"]["status"],
            checks["restart_attempts"]["status"]
        ]

        if "error" in statuses or "critical" in statuses:
            checks["overall_status"] = "critical"
        elif "degraded" in statuses or "warning" in statuses:
            checks["overall_status"] = "warning"
        else:
            checks["overall_status"] = "healthy"

        # Log health check to audit trail
        self.audit_logger.log_action(
            action_type="health_check",
            actor="health_check",
            target="system",
            parameters={
                "overall_status": checks["overall_status"],
                "watchers_running": checks["watchers"].get("running_count", 0),
                "pending_count": checks["queue"].get("pending_count", 0),
                "open_circuits": checks["circuit_breakers"].get("open_count", 0),
                "degraded_services": checks["service_degradation"].get("degraded_count", 0),
                "restart_attempts": checks["restart_attempts"].get("restart_count", 0)
            },
            result="success" if checks["overall_status"] == "healthy" else "warning"
        )

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

            # Add circuit breaker issues
            if checks["circuit_breakers"]["status"] != "healthy":
                open_count = checks["circuit_breakers"].get("open_count", 0)
                half_open_count = checks["circuit_breakers"].get("half_open_count", 0)
                content += f"- **Circuit Breakers**: {open_count} OPEN, {half_open_count} HALF_OPEN\n"

                for circuit in checks["circuit_breakers"].get("open_circuits", []):
                    content += f"  - {circuit['service']}: {circuit['failure_count']} failures\n"

            # Add service degradation issues
            if checks["service_degradation"]["status"] != "healthy":
                degraded_count = checks["service_degradation"].get("degraded_count", 0)
                critical_count = checks["service_degradation"].get("critical_degraded_count", 0)
                content += f"- **Service Degradation**: {degraded_count} degraded ({critical_count} critical)\n"

                for service in checks["service_degradation"].get("degraded_services", []):
                    critical_marker = " [CRITICAL]" if service["is_critical"] else ""
                    content += f"  - {service['service']}{critical_marker}: {service['consecutive_failures']} consecutive failures\n"

            # Add restart attempt issues
            if checks["restart_attempts"]["status"] != "healthy":
                restart_count = checks["restart_attempts"].get("restart_count", 0)
                excessive_count = checks["restart_attempts"].get("excessive_restart_count", 0)
                content += f"- **Restart Attempts**: {restart_count} services restarted ({excessive_count} excessive)\n"

                for service in checks["restart_attempts"].get("services_with_restarts", []):
                    content += f"  - {service['service']}: {service['restart_count']} restarts\n"

            content += "\n### Action Required\n\nReview system logs and restart failed components. Check circuit breaker states and service health.\n"

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
