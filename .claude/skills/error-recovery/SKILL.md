# Error Recovery & Graceful Degradation

**Skill Name:** error-recovery
**Category:** Gold Tier - System Resilience & Reliability
**MCP Required:** No

## Purpose

Implement comprehensive error recovery and graceful degradation strategies to ensure the AI Employee continues operating even when components fail. Automatically detects, logs, retries, and recovers from errors while maintaining system stability.

## Prerequisites

- All Silver and Gold Tier skills operational
- Audit logging configured
- Health monitoring system active
- PM2 process manager installed

## Setup

### 1. Configure Error Recovery

Create `config/error_recovery_config.json`:

```json
{
  "retry_policies": {
    "transient_errors": {
      "max_attempts": 3,
      "base_delay_seconds": 1,
      "max_delay_seconds": 60,
      "exponential_backoff": true,
      "jitter": true
    },
    "api_rate_limits": {
      "max_attempts": 5,
      "base_delay_seconds": 60,
      "max_delay_seconds": 900,
      "exponential_backoff": true
    },
    "authentication_errors": {
      "max_attempts": 1,
      "alert_immediately": true,
      "pause_operations": true
    }
  },
  "circuit_breaker": {
    "enabled": true,
    "failure_threshold": 5,
    "timeout_seconds": 60,
    "half_open_attempts": 3
  },
  "graceful_degradation": {
    "enabled": true,
    "fallback_modes": {
      "gmail_api_down": "queue_locally",
      "odoo_api_down": "log_to_file",
      "social_media_api_down": "queue_for_retry",
      "mcp_server_down": "alert_and_pause"
    }
  },
  "health_checks": {
    "interval_seconds": 300,
    "timeout_seconds": 10,
    "services": [
      "gmail_watcher",
      "whatsapp_watcher",
      "linkedin_poster",
      "odoo_connection",
      "mcp_servers"
    ]
  },
  "auto_recovery": {
    "enabled": true,
    "restart_failed_services": true,
    "max_restart_attempts": 3,
    "restart_delay_seconds": 30
  }
}
```

### 2. Initialize Error Recovery Module

Create `scripts/error_recovery.py`:

```python
import time
import logging
from typing import Callable, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
import subprocess
from pathlib import Path

class ErrorRecovery:
    """Comprehensive error recovery and graceful degradation."""

    def __init__(self, config_path: str = "config/error_recovery_config.json"):
        self.config = self._load_config(config_path)
        self.circuit_breakers = {}
        self.failure_counts = {}
        self.logger = logging.getLogger(__name__)

    def with_retry(
        self,
        error_type: str = "transient_errors",
        on_failure: Optional[Callable] = None
    ):
        """Decorator for automatic retry with exponential backoff."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                policy = self.config["retry_policies"][error_type]
                max_attempts = policy["max_attempts"]
                base_delay = policy["base_delay_seconds"]
                max_delay = policy["max_delay_seconds"]

                for attempt in range(max_attempts):
                    try:
                        result = func(*args, **kwargs)
                        # Reset failure count on success
                        self._reset_failure_count(func.__name__)
                        return result

                    except Exception as e:
                        self._increment_failure_count(func.__name__)
                        self.logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}"
                        )

                        if attempt == max_attempts - 1:
                            # Final attempt failed
                            self._handle_final_failure(func.__name__, e)
                            if on_failure:
                                return on_failure(*args, **kwargs)
                            raise

                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (2 ** attempt),
                            max_delay
                        )

                        # Add jitter if configured
                        if policy.get("jitter", False):
                            import random
                            delay *= (0.5 + random.random())

                        self.logger.info(f"Retrying in {delay:.1f}s...")
                        time.sleep(delay)

            return wrapper
        return decorator

    def circuit_breaker(self, service_name: str):
        """Circuit breaker pattern to prevent cascading failures."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self.config["circuit_breaker"]["enabled"]:
                    return func(*args, **kwargs)

                breaker = self._get_circuit_breaker(service_name)

                # Check circuit state
                if breaker["state"] == "open":
                    if self._should_attempt_reset(breaker):
                        breaker["state"] = "half_open"
                    else:
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker open for {service_name}"
                        )

                try:
                    result = func(*args, **kwargs)

                    # Success in half-open state closes circuit
                    if breaker["state"] == "half_open":
                        breaker["state"] = "closed"
                        breaker["failure_count"] = 0

                    return result

                except Exception as e:
                    breaker["failure_count"] += 1

                    # Open circuit if threshold exceeded
                    threshold = self.config["circuit_breaker"]["failure_threshold"]
                    if breaker["failure_count"] >= threshold:
                        breaker["state"] = "open"
                        breaker["opened_at"] = datetime.now()
                        self._create_circuit_breaker_alert(service_name)

                    raise

            return wrapper
        return decorator

    def graceful_degradation(self, service_name: str, fallback_mode: str):
        """Implement graceful degradation when service fails."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(
                        f"{service_name} failed: {e}. "
                        f"Entering fallback mode: {fallback_mode}"
                    )

                    # Execute fallback strategy
                    return self._execute_fallback(
                        service_name,
                        fallback_mode,
                        args,
                        kwargs
                    )

            return wrapper
        return decorator
```

### 3. Environment Variables

Add to `.env`:

```bash
ERROR_RECOVERY_ENABLED=true
AUTO_RESTART_SERVICES=true
CIRCUIT_BREAKER_ENABLED=true
HEALTH_CHECK_INTERVAL=300
ALERT_EMAIL=your_email@example.com
```

## Usage

### Invoke the Skill

```bash
/error-recovery [action] [options]
```

### Available Actions

1. **Check System Health**
   ```
   /error-recovery health-check
   ```

2. **View Error Statistics**
   ```
   /error-recovery stats --period "last-24-hours"
   ```

3. **Restart Failed Service**
   ```
   /error-recovery restart --service "gmail-watcher"
   ```

4. **Test Recovery Mechanisms**
   ```
   /error-recovery test --scenario "api-failure"
   ```

5. **Generate Recovery Report**
   ```
   /error-recovery report --date "2026-03-14"
   ```

## Error Categories

### 1. Transient Errors (Auto-Retry)

Temporary failures that usually resolve on retry:

```python
# Network timeouts
# API temporary unavailability
# Rate limit exceeded (short-term)
# Database connection timeout

# Recovery: Exponential backoff retry (3 attempts)
```

### 2. Authentication Errors (Alert & Pause)

Credential or permission issues:

```python
# Expired OAuth token
# Invalid API key
# Revoked access
# Insufficient permissions

# Recovery: Alert user, pause operations, await manual fix
```

### 3. Logic Errors (Log & Continue)

AI misinterpretation or data issues:

```python
# Claude misunderstands request
# Invalid data format
# Missing required field
# Unexpected response

# Recovery: Log error, create review item, continue with next task
```

### 4. System Errors (Auto-Restart)

Process crashes or system failures:

```python
# Watcher process died
# MCP server crashed
# Disk full
# Memory exhausted

# Recovery: Auto-restart service, alert if repeated failures
```

## Retry Strategies

### Exponential Backoff with Jitter

```python
from scripts.error_recovery import ErrorRecovery

recovery = ErrorRecovery()

@recovery.with_retry(error_type="transient_errors")
def send_email(to, subject, body):
    """Send email with automatic retry on failure."""
    # Attempt 1: Immediate
    # Attempt 2: Wait 1s
    # Attempt 3: Wait 2s
    # If all fail: Alert and log
    return email_mcp.send(to, subject, body)
```

### Circuit Breaker Pattern

```python
@recovery.circuit_breaker(service_name="odoo_api")
def create_invoice(customer, amount):
    """Create invoice with circuit breaker protection."""
    # If Odoo API fails 5 times in a row:
    # - Circuit opens (stops trying)
    # - Wait 60 seconds
    # - Try once (half-open)
    # - If success: Close circuit
    # - If failure: Keep circuit open
    return odoo.create_invoice(customer, amount)
```

### Graceful Degradation

```python
@recovery.graceful_degradation(
    service_name="gmail_api",
    fallback_mode="queue_locally"
)
def send_email_with_fallback(to, subject, body):
    """Send email or queue if Gmail API is down."""
    # Try to send via Gmail API
    # If fails: Save to local queue
    # Retry when API is back online
    return gmail_api.send(to, subject, body)
```

## Health Monitoring

### Automatic Health Checks

Runs every 5 minutes via `scripts/health_check.py`:

```python
def check_service_health():
    """Check health of all critical services."""
    services = {
        "gmail_watcher": check_pm2_service("gmail-watcher"),
        "whatsapp_watcher": check_pm2_service("whatsapp-processor"),
        "linkedin_poster": check_pm2_service("linkedin-poster"),
        "odoo_connection": check_odoo_api(),
        "mcp_email": check_mcp_server("email"),
        "mcp_social": check_mcp_server("social-media"),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }

    # Create alerts for unhealthy services
    for service, healthy in services.items():
        if not healthy:
            create_health_alert(service)
            attempt_auto_recovery(service)

    return services
```

### Health Check Results

```markdown
# System Health Report - 2026-03-14 10:30

## Service Status

| Service | Status | Uptime | Last Check |
|---------|--------|--------|------------|
| Gmail Watcher | ✅ Healthy | 5d 12h | 10:30 AM |
| WhatsApp Watcher | ✅ Healthy | 5d 12h | 10:30 AM |
| LinkedIn Poster | ✅ Healthy | 5d 12h | 10:30 AM |
| Odoo Connection | ✅ Healthy | - | 10:30 AM |
| Email MCP | ✅ Healthy | - | 10:30 AM |
| Social Media MCP | ⚠️ Degraded | - | 10:30 AM |

## System Resources

- **Disk Space:** 45.2 GB free (78%) ✅
- **Memory:** 4.2 GB used / 16 GB (26%) ✅
- **CPU:** 12% average ✅

## Recent Issues

- Social Media MCP: Rate limit exceeded (auto-recovering)
- No critical issues

## Recommendations

- ✅ All services operational
- ⚠️ Social Media MCP experiencing rate limits (will retry in 15 min)
```

## Auto-Recovery Actions

### Service Restart

```python
def auto_restart_service(service_name: str) -> bool:
    """Automatically restart failed service."""
    max_attempts = 3
    restart_delay = 30

    for attempt in range(max_attempts):
        try:
            # Stop service
            subprocess.run(["pm2", "stop", service_name], check=True)
            time.sleep(5)

            # Start service
            subprocess.run(["pm2", "start", service_name], check=True)
            time.sleep(restart_delay)

            # Verify service is running
            if check_service_health(service_name):
                logger.info(f"Successfully restarted {service_name}")
                return True

        except Exception as e:
            logger.error(f"Restart attempt {attempt + 1} failed: {e}")

    # All restart attempts failed
    create_critical_alert(f"Failed to restart {service_name}")
    return False
```

### Token Refresh

```python
def auto_refresh_token(service: str) -> bool:
    """Automatically refresh expired OAuth tokens."""
    try:
        if service == "gmail":
            refresh_gmail_token()
        elif service == "linkedin":
            refresh_linkedin_token()
        elif service == "facebook":
            refresh_facebook_token()
        elif service == "twitter":
            refresh_twitter_token()

        logger.info(f"Successfully refreshed {service} token")
        return True

    except Exception as e:
        logger.error(f"Token refresh failed for {service}: {e}")
        create_auth_alert(service)
        return False
```

## Fallback Modes

### Queue for Retry

When API is temporarily unavailable:

```python
def queue_for_retry(action: str, data: dict):
    """Queue action for retry when service recovers."""
    queue_file = Path("AI_Employee_Vault/.state/retry_queue.json")

    queue_item = {
        "id": generate_id(),
        "action": action,
        "data": data,
        "queued_at": datetime.now().isoformat(),
        "retry_count": 0,
        "max_retries": 10,
        "next_retry": (datetime.now() + timedelta(minutes=15)).isoformat()
    }

    # Append to queue
    queue = load_queue(queue_file)
    queue.append(queue_item)
    save_queue(queue_file, queue)

    logger.info(f"Queued {action} for retry")
```

### Log to File

When database is unavailable:

```python
def log_to_file_fallback(data: dict):
    """Log data to file when database is unavailable."""
    fallback_file = Path("AI_Employee_Vault/Logs/fallback_data.jsonl")

    with open(fallback_file, "a") as f:
        f.write(json.dumps(data) + "\n")

    logger.info("Data logged to fallback file")
```

### Alert and Pause

For critical failures:

```python
def alert_and_pause(service: str, error: Exception):
    """Alert user and pause operations for critical failure."""
    # Create high-priority alert
    create_alert(
        type="critical_failure",
        service=service,
        error=str(error),
        priority="high"
    )

    # Pause service operations
    pause_service(service)

    # Notify user
    send_notification(
        title=f"Critical Failure: {service}",
        message=f"Service paused. Manual intervention required.",
        priority="high"
    )

    logger.critical(f"Service {service} paused due to critical failure")
```

## Error Alerts

### Alert Template

```markdown
---
type: error_alert
priority: high
service: gmail_watcher
error_type: authentication_error
created: 2026-03-14T10:30:00Z
status: needs_attention
---

# Error Alert: Gmail Watcher Authentication Failed

**Service:** Gmail Watcher
**Error Type:** Authentication Error
**Timestamp:** 2026-03-14 10:30:00 UTC
**Consecutive Failures:** 3

## Error Details

```
invalid_grant: Token has been expired or revoked
```

## Impact

- Gmail monitoring paused
- New emails not being processed
- Urgent messages may be missed

## Auto-Recovery Attempted

- ✅ Attempted token refresh (failed)
- ✅ Restarted service (failed)
- ❌ Manual intervention required

## Recommended Actions

1. [ ] Re-authenticate Gmail API
   ```bash
   uv run python scripts/auth/complete_oauth.py
   ```

2. [ ] Verify credentials.json is valid

3. [ ] Restart Gmail watcher
   ```bash
   pm2 restart gmail-watcher
   ```

4. [ ] Verify service is healthy
   ```bash
   /error-recovery health-check
   ```

## Related Logs

- `AI_Employee_Vault/Logs/gmail_watcher_20260314.log`
- `AI_Employee_Vault/Logs/audit_2026-03-14.json`
```

## Recovery Statistics

### Daily Recovery Report

```markdown
# Error Recovery Report - 2026-03-14

## Summary

- **Total Errors:** 23
- **Auto-Recovered:** 20 (87%)
- **Manual Intervention:** 3 (13%)
- **System Uptime:** 99.2%

## Errors by Category

| Category | Count | Recovery Rate |
|----------|-------|---------------|
| Transient | 15 | 100% |
| Rate Limit | 5 | 100% |
| Authentication | 2 | 50% |
| System | 1 | 100% |

## Recovery Actions

| Action | Count | Success Rate |
|--------|-------|--------------|
| Retry with backoff | 15 | 100% |
| Service restart | 3 | 100% |
| Token refresh | 2 | 50% |
| Queue for retry | 5 | 100% |

## Failed Recoveries

1. **Gmail Authentication** - 10:30 AM
   - Error: Token expired
   - Recovery: Token refresh failed
   - Resolution: Manual re-authentication required

2. **Odoo Connection** - 2:45 PM
   - Error: Connection refused
   - Recovery: Service restart failed
   - Resolution: Odoo server was down (external issue)

## Recommendations

- ✅ Auto-recovery working well for transient errors
- ⚠️ Consider implementing automatic OAuth token renewal
- 💡 Add health check for external dependencies (Odoo)
```

## Integration with Audit Logging

All recovery actions are logged:

```json
{
  "timestamp": "2026-03-14T10:30:00Z",
  "action_type": "error_recovery",
  "service": "gmail_watcher",
  "error_type": "authentication_error",
  "recovery_action": "token_refresh",
  "recovery_result": "failed",
  "manual_intervention_required": true,
  "alert_created": true
}
```

## Troubleshooting

**Q: Service keeps restarting**
- Check service logs for root cause
- Verify configuration is correct
- Ensure dependencies are available
- Consider increasing restart delay

**Q: Circuit breaker stuck open**
- Verify underlying issue is resolved
- Manually reset circuit breaker
- Check failure threshold configuration

**Q: Retry queue growing**
- Check if service has recovered
- Verify retry interval is appropriate
- Consider increasing max retries

## References

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Retry Strategies](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Graceful Degradation](https://en.wikipedia.org/wiki/Fault_tolerance)

## Gold Tier Completion Criteria

- ✅ Error recovery module implemented
- ✅ Retry strategies configured
- ✅ Circuit breaker pattern active
- ✅ Graceful degradation enabled
- ✅ Health monitoring automated
- ✅ Auto-recovery for services
- ✅ Alert system for failures
- ✅ Recovery statistics tracked
- ✅ Integration with audit logging
- ✅ Comprehensive documentation
