# Error Recovery System - Setup Guide

**Feature**: 005-error-recovery
**Date**: 2026-03-16
**Version**: 1.0.0

---

## Overview

This guide walks you through setting up the error recovery system for the AI Employee project. The system provides automatic retry with exponential backoff, circuit breaker protection, graceful degradation, and auto-restart capabilities.

---

## Prerequisites

### System Requirements

- Python 3.10 or higher
- Linux/macOS/WSL2 (for process management features)
- 50MB disk space for state files and logs

### Python Dependencies

All dependencies are already included in the project:
- No additional packages required (uses Python standard library)
- Existing dependencies: `pytest`, `pytest-cov` (for testing)

---

## Installation

### Step 1: Verify Module Structure

The error recovery module should already be present in your project:

```bash
# Verify module exists
ls -la scripts/error_recovery/

# Expected files:
# __init__.py
# retry_policy.py
# circuit_breaker.py
# service_health.py
# recovery_state.py
# decorators.py
```

If any files are missing, the module is incomplete. Contact the development team.

---

### Step 2: Create State Directory

The error recovery system stores state in `AI_Employee_Vault/.state/`:

```bash
# Create state directory
mkdir -p AI_Employee_Vault/.state

# Verify permissions
chmod 755 AI_Employee_Vault/.state
```

**State Files**:
- `recovery_state.json` - Circuit breaker states, service health, retry counters
- Automatically created on first use
- Atomic writes prevent corruption

---

### Step 3: Configure Environment Variables

Add error recovery configuration to your `.env` file:

```bash
# Copy from .env.example
cat >> .env << 'EOF'

# ============================================================================
# ERROR RECOVERY SYSTEM
# ============================================================================

# Retry Policy Configuration
ERROR_RECOVERY_BASE_DELAY=1.0
ERROR_RECOVERY_MAX_ATTEMPTS=5
ERROR_RECOVERY_MAX_DELAY=60.0
ERROR_RECOVERY_BACKOFF_MULTIPLIER=2.0
ERROR_RECOVERY_JITTER_ENABLED=true
ERROR_RECOVERY_JITTER_MAX=1.0

# Circuit Breaker Configuration
ERROR_RECOVERY_CIRCUIT_FAILURE_THRESHOLD=5
ERROR_RECOVERY_CIRCUIT_COOLDOWN_SECONDS=60

# Service Health Configuration
ERROR_RECOVERY_RESTART_WINDOW_MINUTES=10
ERROR_RECOVERY_MAX_RESTARTS=3
ERROR_RECOVERY_STABILITY_PERIOD_MINUTES=5

# Alert Configuration
ERROR_RECOVERY_ALERT_RATE_LIMIT_MINUTES=5

# State Persistence
ERROR_RECOVERY_STATE_PATH=./AI_Employee_Vault/.state/recovery_state.json
EOF
```

**Configuration Tuning**:

| Parameter | Default | Description | Tuning Guidance |
|-----------|---------|-------------|-----------------|
| `BASE_DELAY` | 1.0s | Initial retry delay | Increase for slow APIs (2.0s) |
| `MAX_ATTEMPTS` | 5 | Max retry attempts | Reduce for fast-fail (3), increase for critical (7) |
| `MAX_DELAY` | 60.0s | Max retry delay cap | Increase for patient retries (120s) |
| `FAILURE_THRESHOLD` | 5 | Failures before circuit opens | Reduce for sensitive services (3) |
| `COOLDOWN_SECONDS` | 60 | Circuit cooldown period | Increase for slow recovery (120s) |
| `MAX_RESTARTS` | 3 | Max restarts in window | Reduce to prevent restart loops (2) |

---

### Step 4: Verify Installation

Run the verification script:

```bash
# Run error recovery tests
uv run pytest tests/test_retry_policy.py -v
uv run pytest tests/test_circuit_breaker.py -v
uv run pytest tests/test_service_health.py -v
uv run pytest tests/test_recovery_state.py -v
uv run pytest tests/test_decorators.py -v

# Expected output: All tests PASS
```

If any tests fail, check:
1. Python version (must be 3.10+)
2. State directory permissions
3. No conflicting processes using state files

---

## Configuration

### Service Classification

Edit `scripts/error_recovery/service_health.py` to classify your services:

```python
# Critical services - auto-restart on failure
CRITICAL_SERVICES = [
    "gmail_watcher",
    "whatsapp_watcher",
    "approval_workflows"
]

# Non-critical services - graceful degradation
NON_CRITICAL_SERVICES = [
    "daily_briefing",
    "health_check",
    "dashboard_updates"
]
```

**Guidelines**:
- **Critical**: User-facing, revenue-impacting, or data-loss-preventing services
- **Non-critical**: Background tasks, reporting, analytics

---

### Circuit Breaker Tuning

Adjust circuit breaker thresholds per service in your code:

```python
from scripts.error_recovery.decorators import with_circuit_breaker

# Sensitive service - open circuit quickly
@with_circuit_breaker(service_name="payment_api")
def process_payment():
    pass

# Tolerant service - allow more failures
@with_circuit_breaker(service_name="analytics_api")
def track_event():
    pass
```

**Note**: Per-service thresholds are not yet implemented. All services use global `FAILURE_THRESHOLD` from environment variables.

---

### Retry Policy Customization

Create custom retry policies for specific operations:

```python
from scripts.error_recovery.retry_policy import RetryPolicy
from scripts.error_recovery.decorators import with_retry

# Fast-fail policy for quick operations
fast_policy = RetryPolicy(
    base_delay=0.5,
    max_attempts=3,
    max_delay=10.0
)

@with_retry(policy=fast_policy)
def quick_check():
    pass

# Patient policy for critical operations
patient_policy = RetryPolicy(
    base_delay=2.0,
    max_attempts=7,
    max_delay=120.0
)

@with_retry(policy=patient_policy)
def critical_operation():
    pass
```

---

## Integration

### Migrating Existing Code

**Step 1**: Identify operations requiring error recovery

```bash
# Find external API calls
grep -r "requests\." watchers/
grep -r "\.execute()" watchers/
grep -r "api\." scripts/
```

**Step 2**: Add decorator imports

```python
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker
```

**Step 3**: Apply decorators

```python
# Before
def fetch_data():
    return api.get("/data")

# After
@with_circuit_breaker(service_name="external_api")
@with_retry(max_attempts=5, base_delay=1.0)
def fetch_data():
    return api.get("/data")
```

**Step 4**: Handle circuit breaker exceptions

```python
from scripts.error_recovery.circuit_breaker import CircuitBreakerOpenError

try:
    result = fetch_data()
except CircuitBreakerOpenError:
    # Circuit is open, service is failing
    logger.warning("Circuit breaker open for external_api")
    # Use cached data or return graceful error
```

---

## Verification

### Test 1: Retry Behavior

```python
# Create test script: test_retry_manual.py
from scripts.error_recovery.decorators import with_retry
import time

call_count = 0

@with_retry(max_attempts=3, base_delay=1.0)
def flaky_function():
    global call_count
    call_count += 1
    print(f"Attempt {call_count}")
    if call_count < 3:
        raise ConnectionError("Simulated failure")
    return "Success!"

# Run test
result = flaky_function()
print(f"Result: {result}, Total attempts: {call_count}")
# Expected: "Success!", 3 attempts
```

---

### Test 2: Circuit Breaker

```python
# Create test script: test_circuit_manual.py
from scripts.error_recovery.decorators import with_circuit_breaker
from scripts.error_recovery.circuit_breaker import CircuitBreakerOpenError

@with_circuit_breaker(service_name="test_service")
def failing_function():
    raise ConnectionError("Service down")

# Trigger circuit breaker (5 failures)
for i in range(6):
    try:
        failing_function()
    except (ConnectionError, CircuitBreakerOpenError) as e:
        print(f"Attempt {i+1}: {type(e).__name__}")

# Expected: First 5 raise ConnectionError, 6th raises CircuitBreakerOpenError
```

---

### Test 3: State Persistence

```bash
# Check state file exists
cat AI_Employee_Vault/.state/recovery_state.json | jq '.'

# Expected output:
# {
#   "version": "1.0.0",
#   "circuit_breakers": {},
#   "service_health": {},
#   "last_updated": "2026-03-16T..."
# }
```

---

### Test 4: Health Check Integration

```bash
# Run health check
uv run python scripts/health_check.py

# Expected output:
# Health Check: HEALTHY
#   Watchers: 3/3
#   Queue: 0 pending
#   Activity: 5 in last hour
```

---

## Monitoring

### View Circuit Breaker Status

```bash
# Check all circuit breakers
cat AI_Employee_Vault/.state/recovery_state.json | jq '.circuit_breakers'

# Find open circuits
cat AI_Employee_Vault/.state/recovery_state.json | jq '.circuit_breakers | to_entries[] | select(.value.state == "OPEN")'
```

---

### View Service Health

```bash
# Check all services
cat AI_Employee_Vault/.state/recovery_state.json | jq '.service_health'

# Find degraded services
cat AI_Employee_Vault/.state/recovery_state.json | jq '.service_health | to_entries[] | select(.value.health_status != "HEALTHY")'
```

---

### View Audit Logs

```bash
# View today's error recovery actions
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | jq 'select(.action_type | startswith("error_recovery"))'

# View circuit breaker state changes
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | jq 'select(.action_type == "circuit_breaker_state_change")'

# View retry attempts
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | jq 'select(.action_type == "error_recovery_retry")'
```

---

## Troubleshooting

### Issue 1: State File Corruption

**Symptom**: `JSONDecodeError` when loading recovery state

**Solution**:
```bash
# Check for backup
ls -la AI_Employee_Vault/.state/recovery_state.json.backup

# Restore from backup
cp AI_Employee_Vault/.state/recovery_state.json.backup AI_Employee_Vault/.state/recovery_state.json

# Or reset state
rm AI_Employee_Vault/.state/recovery_state.json
# State will be recreated on next use
```

---

### Issue 2: Circuit Breaker Not Opening

**Symptom**: Circuit remains closed despite failures

**Diagnosis**:
```bash
# Check failure count
cat AI_Employee_Vault/.state/recovery_state.json | jq '.circuit_breakers.SERVICE_NAME.failure_count'

# Check threshold
echo $ERROR_RECOVERY_CIRCUIT_FAILURE_THRESHOLD
```

**Solution**:
- Verify decorator is applied: `@with_circuit_breaker(service_name="...")`
- Check failure count increments on each failure
- Verify threshold is set correctly (default: 5)

---

### Issue 3: Too Many Retries

**Symptom**: Operations taking too long

**Solution**:
```python
# Reduce max_attempts
@with_retry(max_attempts=3, base_delay=1.0)  # Instead of 5
def operation():
    pass
```

Or adjust environment variable:
```bash
ERROR_RECOVERY_MAX_ATTEMPTS=3
```

---

### Issue 4: Alerts Not Created

**Symptom**: No alert files in `Needs_Action/` when circuit opens

**Diagnosis**:
```bash
# Check Needs_Action directory exists
ls -la AI_Employee_Vault/Needs_Action/

# Check permissions
ls -ld AI_Employee_Vault/Needs_Action/
```

**Solution**:
```bash
# Create directory if missing
mkdir -p AI_Employee_Vault/Needs_Action
chmod 755 AI_Employee_Vault/Needs_Action
```

---

### Issue 5: Service Not Auto-Restarting

**Symptom**: Failed service not restarting automatically

**Diagnosis**:
```bash
# Check if service is classified as critical
grep -A 10 "CRITICAL_SERVICES" scripts/error_recovery/service_health.py

# Check restart count
cat AI_Employee_Vault/.state/recovery_state.json | jq '.service_health.SERVICE_NAME.restart_count'
```

**Solution**:
- Add service to `CRITICAL_SERVICES` list
- Verify restart threshold not exceeded (default: 3 in 10 minutes)
- Check health_check.py is running (cron job)

---

## Maintenance

### Regular Tasks

**Daily**:
- Review circuit breaker alerts in `Needs_Action/`
- Check audit logs for unusual retry patterns

**Weekly**:
- Review circuit breaker open/close frequency
- Tune retry policies based on success rates
- Clean up old alert files

**Monthly**:
- Analyze service health trends
- Adjust service classifications
- Review and update failure thresholds

---

### State File Cleanup

```bash
# Backup current state
cp AI_Employee_Vault/.state/recovery_state.json AI_Employee_Vault/.state/recovery_state.json.$(date +%Y%m%d)

# Reset circuit breakers (if needed)
cat AI_Employee_Vault/.state/recovery_state.json | jq '.circuit_breakers = {}' > /tmp/state.json
mv /tmp/state.json AI_Employee_Vault/.state/recovery_state.json

# Reset service health (if needed)
cat AI_Employee_Vault/.state/recovery_state.json | jq '.service_health = {}' > /tmp/state.json
mv /tmp/state.json AI_Employee_Vault/.state/recovery_state.json
```

---

## Uninstallation

To remove the error recovery system:

```bash
# 1. Remove decorators from code
# Manually remove @with_retry and @with_circuit_breaker decorators

# 2. Remove state files
rm -rf AI_Employee_Vault/.state/recovery_state.json*

# 3. Remove environment variables
# Edit .env and remove ERROR_RECOVERY_* variables

# 4. Remove module (optional)
# rm -rf scripts/error_recovery/
```

**Warning**: Uninstalling will remove all circuit breaker states and service health tracking. Backup state files before uninstalling.

---

## Support

### Documentation

- **Quickstart Guide**: `specs/005-error-recovery/quickstart.md`
- **Data Model**: `specs/005-error-recovery/data-model.md`
- **Architecture**: `specs/005-error-recovery/plan.md`
- **Requirements**: `specs/005-error-recovery/spec.md`

### Logs

- **Audit Logs**: `AI_Employee_Vault/Logs/audit_YYYY-MM-DD.jsonl`
- **Health Checks**: `AI_Employee_Vault/Logs/health_checks.json`
- **Alerts**: `AI_Employee_Vault/Needs_Action/ALERT_*.md`

### Testing

```bash
# Run full test suite
uv run pytest tests/test_*_recovery.py -v --cov=scripts/error_recovery

# Run specific test category
uv run pytest tests/test_retry_policy.py -v
uv run pytest tests/test_circuit_breaker.py -v
uv run pytest tests/test_integration_recovery.py -v
```

---

## Next Steps

After completing setup:

1. **Integrate with existing watchers** - See `quickstart.md` for migration examples
2. **Configure service classification** - Edit `service_health.py`
3. **Set up monitoring** - Add circuit breaker checks to health_check.py
4. **Test error scenarios** - Simulate failures to verify behavior
5. **Review audit logs** - Monitor recovery actions

---

## Version History

- **1.0.0** (2026-03-16): Initial release
  - Automatic retry with exponential backoff
  - Circuit breaker pattern
  - Graceful degradation
  - Auto-restart for failed services
  - State persistence
  - Audit logging
