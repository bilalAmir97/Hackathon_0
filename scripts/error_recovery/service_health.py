"""
ServiceHealth - Health status tracking and restart management

Tracks service health state (healthy/degraded/failed) and manages
automatic restart attempts with intelligent backoff.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Import audit logger for logging state transitions
try:
    from scripts.audit_logger import AuditLogger
    audit_logger = AuditLogger()
except (ImportError, FileNotFoundError, Exception):
    # Fallback if audit logger not available
    audit_logger = None

# Alert directory for degradation alerts
ALERT_DIR = Path("AI_Employee_Vault/Needs_Action")

# Service classification
CRITICAL_SERVICES = [
    "gmail_watcher",
    "approval_workflow",
    "whatsapp_watcher"
]

NON_CRITICAL_SERVICES = [
    "daily_briefing",
    "health_check",
    "weekly_audit"
]

# Alert rate limiting: track last alert time per service
_last_alert_time = {}
ALERT_RATE_LIMIT_SECONDS = 300  # 5 minutes


class ServiceHealth:
    """
    Health status tracking per service with restart management.

    Tracks service health state (healthy/degraded/failed), consecutive failures,
    and manages automatic restart attempts with intelligent backoff.
    """

    def __init__(self, service_name: str, is_critical: bool = True):
        """
        Initialize ServiceHealth.

        Args:
            service_name: Name of the service to track
            is_critical: Whether service is critical (affects restart behavior)
        """
        self.service_name = service_name
        self.is_critical = is_critical
        self.state = "healthy"  # healthy, degraded, failed
        self.consecutive_failures = 0
        self.last_check_time: Optional[datetime] = None

        # Restart tracking (Phase 6)
        self.restart_count = 0
        self.last_restart_time: Optional[datetime] = None
        self.restart_window = 600.0  # 10 minutes
        self.max_restarts = 3
        self.stability_period = 300.0  # 5 minutes

    def mark_healthy(self):
        """
        Mark service as healthy and reset failure tracking.

        Transitions service to healthy state and resets consecutive failure counter.
        """
        previous_state = self.state
        self.state = "healthy"
        self.consecutive_failures = 0
        self.last_check_time = datetime.utcnow()

        # Log state transition if changed
        if previous_state != "healthy" and audit_logger:
            audit_logger.log_action(
                action_type='service_health_transition',
                actor='error_recovery',
                target=self.service_name,
                parameters={
                    'from_state': previous_state,
                    'to_state': 'healthy',
                    'consecutive_failures': 0
                },
                result='success'
            )

    def mark_degraded(self, reason: str = "Unknown"):
        """
        Mark service as degraded and increment failure counter.

        Args:
            reason: Reason for degradation
        """
        previous_state = self.state
        self.state = "degraded"
        self.consecutive_failures += 1
        self.last_check_time = datetime.utcnow()

        # Log state transition
        if audit_logger:
            audit_logger.log_action(
                action_type='service_health_transition',
                actor='error_recovery',
                target=self.service_name,
                parameters={
                    'from_state': previous_state,
                    'to_state': 'degraded',
                    'reason': reason,
                    'consecutive_failures': self.consecutive_failures
                },
                result='degraded'
            )

        # Create alert if rate limit allows
        self._create_alert_if_allowed(reason, "degraded")

    def mark_failed(self, reason: str = "Unknown"):
        """
        Mark service as failed and increment failure counter.

        Args:
            reason: Reason for failure
        """
        previous_state = self.state
        self.state = "failed"
        self.consecutive_failures += 1
        self.last_check_time = datetime.utcnow()

        # Log state transition
        if audit_logger:
            audit_logger.log_action(
                action_type='service_health_transition',
                actor='error_recovery',
                target=self.service_name,
                parameters={
                    'from_state': previous_state,
                    'to_state': 'failed',
                    'reason': reason,
                    'consecutive_failures': self.consecutive_failures
                },
                result='failed'
            )

        # Create alert if rate limit allows
        self._create_alert_if_allowed(reason, "failed")

    def _create_alert_if_allowed(self, reason: str, alert_type: str):
        """
        Create alert file if rate limit allows.

        Args:
            reason: Reason for alert
            alert_type: Type of alert (degraded or failed)
        """
        global _last_alert_time

        # Check rate limit
        now = datetime.utcnow()
        last_alert = _last_alert_time.get(self.service_name)

        if last_alert:
            time_since_last = (now - last_alert).total_seconds()
            if time_since_last < ALERT_RATE_LIMIT_SECONDS:
                # Rate limited - skip alert creation
                return

        # Create alert
        self._create_alert(reason, alert_type)

        # Update last alert time
        _last_alert_time[self.service_name] = now

    def _create_alert(self, reason: str, alert_type: str):
        """
        Create alert file in Needs_Action directory.

        Args:
            reason: Reason for alert
            alert_type: Type of alert (degraded or failed)
        """
        # Ensure alert directory exists
        ALERT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate alert filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        alert_file = ALERT_DIR / f"ALERT_DEGRADATION_{self.service_name}_{timestamp}.md"

        # Create alert content
        alert_content = f"""# Service Health Alert: {self.service_name}

**Status**: {alert_type.upper()}
**Time**: {datetime.utcnow().isoformat()}Z
**Consecutive Failures**: {self.consecutive_failures}
**Critical Service**: {'Yes' if self.is_critical else 'No'}

## Reason
{reason}

## Recommended Actions
1. Check service logs for errors
2. Verify service dependencies are healthy
3. Review recent changes that may have caused degradation
4. Consider manual restart if service is unresponsive

---
*This alert was automatically generated by the error recovery system.*
"""

        # Write alert file
        alert_file.write_text(alert_content)

    def should_restart(self) -> bool:
        """
        Check if restart should be attempted.

        Only critical services are restarted. Non-critical services are left failed.
        Restart is not attempted if threshold is exceeded.

        Returns:
            True if restart should be attempted, False otherwise
        """
        # Only restart critical services
        if not self.is_critical:
            return False

        # Don't restart if service is healthy
        if self.state == "healthy":
            return False

        # Don't restart if threshold exceeded
        if self.is_restart_threshold_exceeded():
            return False

        return True

    def record_restart(self):
        """
        Record a restart attempt.

        Increments restart counter and updates last restart time.
        """
        self.restart_count += 1
        self.last_restart_time = datetime.utcnow()

        # Log restart attempt
        if audit_logger:
            audit_logger.log_action(
                action_type='service_restart',
                actor='error_recovery',
                target=self.service_name,
                parameters={
                    'restart_count': self.restart_count,
                    'is_critical': self.is_critical
                },
                result='restart_attempted'
            )

    def is_restart_threshold_exceeded(self) -> bool:
        """
        Check if restart threshold is exceeded.

        Threshold: max_restarts (default 3) within restart_window (default 10 minutes).

        Returns:
            True if threshold exceeded, False otherwise
        """
        # No restarts yet
        if self.restart_count == 0 or self.last_restart_time is None:
            return False

        # Check if we're within the restart window
        elapsed = (datetime.utcnow() - self.last_restart_time).total_seconds()

        # If outside window, restarts don't count
        if elapsed > self.restart_window:
            return False

        # Check if count exceeds threshold
        return self.restart_count >= self.max_restarts

    def calculate_restart_backoff(self, attempt: int) -> int:
        """
        Calculate restart backoff delay in seconds.

        Backoff pattern: 0s, 30s, 60s, 120s (capped at 120s)

        Args:
            attempt: Restart attempt number (0-indexed)

        Returns:
            Delay in seconds before restart
        """
        backoff_schedule = [0, 30, 60, 120]

        if attempt < len(backoff_schedule):
            return backoff_schedule[attempt]
        else:
            # Cap at 120s for attempts beyond schedule
            return 120

    def reset_restart_counter_if_stable(self):
        """
        Reset restart counter if service has been stable.

        Stability is defined as: service healthy for stability_period (default 5 minutes)
        since last restart.
        """
        # Only reset if we have restart history
        if self.restart_count == 0 or self.last_restart_time is None:
            return

        # Check if service has been stable
        elapsed = (datetime.utcnow() - self.last_restart_time).total_seconds()

        if elapsed > self.stability_period:
            # Service has been stable - reset counter
            self.restart_count = 0
            self.last_restart_time = None

            # Log reset
            if audit_logger:
                audit_logger.log_action(
                    action_type='service_restart_counter_reset',
                    actor='error_recovery',
                    target=self.service_name,
                    parameters={
                        'reason': 'stability_period_elapsed',
                        'stability_period': self.stability_period
                    },
                    result='success'
                )

    def create_restart_threshold_alert(self):
        """
        Create alert when restart threshold is exceeded.

        Creates ALERT_RESTART_*.md file in Needs_Action directory.
        """
        # Ensure alert directory exists
        ALERT_DIR.mkdir(parents=True, exist_ok=True)

        # Generate alert filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        alert_file = ALERT_DIR / f"ALERT_RESTART_{self.service_name}_{timestamp}.md"

        # Create alert content
        alert_content = f"""# Service Restart Threshold Exceeded: {self.service_name}

**Status**: RESTART_THRESHOLD_EXCEEDED
**Time**: {datetime.utcnow().isoformat()}Z
**Restart Count**: {self.restart_count}
**Restart Window**: {self.restart_window}s ({self.restart_window / 60:.1f} minutes)
**Max Restarts**: {self.max_restarts}
**Critical Service**: {'Yes' if self.is_critical else 'No'}

## Issue
Service has exceeded the maximum restart threshold ({self.max_restarts} restarts within {self.restart_window / 60:.1f} minutes).

This indicates a persistent issue that cannot be resolved by automatic restarts.

## Recommended Actions
1. **Investigate root cause**: Check service logs for recurring errors
2. **Review recent changes**: Identify any recent deployments or configuration changes
3. **Check dependencies**: Verify all service dependencies are healthy
4. **Manual intervention required**: Service will not be automatically restarted until issue is resolved
5. **Reset restart counter**: After fixing the issue, mark service as healthy to reset counter

## Service State
- Current State: {self.state}
- Consecutive Failures: {self.consecutive_failures}
- Last Restart: {self.last_restart_time.isoformat() + 'Z' if self.last_restart_time else 'Never'}

---
*This alert was automatically generated by the error recovery system.*
"""

        # Write alert file
        alert_file.write_text(alert_content)

        # Log alert creation
        if audit_logger:
            audit_logger.log_action(
                action_type='restart_threshold_alert',
                actor='error_recovery',
                target=self.service_name,
                parameters={
                    'restart_count': self.restart_count,
                    'max_restarts': self.max_restarts,
                    'alert_file': str(alert_file)
                },
                result='alert_created'
            )

