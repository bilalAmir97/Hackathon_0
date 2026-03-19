# Watcher System Documentation

**Version**: 1.0
**Last Updated**: March 2026

---

## Overview

The Watcher System is the event-driven backbone of the AI Employee system. It monitors file system events and triggers automated actions based on state transitions.

---

## Components

### 1. Gmail Watcher

**File**: `watchers/gmail_watcher.py`

**Purpose**: Monitor Gmail inbox for new emails and process them

**Key Features**:
- Polls Gmail API every 60 seconds
- Processes unread emails
- Creates approval requests for actions
- Marks emails as read after processing
- Error recovery with exponential backoff

**Configuration**:
```python
GMAIL_CHECK_INTERVAL = 60  # seconds
GMAIL_LABEL = "INBOX"
MAX_EMAILS_PER_CHECK = 10
```

**State Management**:
- Tracks last processed email ID
- Persists state to `gmail_state.json`
- Recovers from crashes without reprocessing

### 2. Vault Watcher

**File**: `watchers/vault_watcher.py`

**Purpose**: Monitor vault folders for file movements (approval workflow)

**Monitored Folders**:
- `Pending_Approval/`: New approval requests
- `Approved/`: Approved actions ready for execution
- `Rejected/`: Rejected actions (logged only)

**Key Features**:
- Real-time file system monitoring via `watchdog`
- Atomic file operations (move, not copy)
- Validates file format before processing
- Creates alerts for corrupted files
- Integrates with approval executor

**Event Handling**:
```python
on_moved(event):
    if dest_path in Approved/:
        approval_executor.execute_action()
    elif dest_path in Rejected/:
        approval_executor.log_rejection()
```

---

## File System Events

### Event Types

| Event | Trigger | Action |
|-------|---------|--------|
| `FileMovedEvent` | File moved to Approved/ | Execute approved action |
| `FileMovedEvent` | File moved to Rejected/ | Log rejection |
| `FileCreatedEvent` | New file in Pending_Approval/ | Validate format |

### Event Flow

```
1. File created in Pending_Approval/
   ↓
2. Watcher detects creation
   ↓
3. Validates file format
   ↓
4. Human moves to Approved/ or Rejected/
   ↓
5. Watcher detects movement
   ↓
6. Triggers approval executor
   ↓
7. Action executed or logged
   ↓
8. File moved to Done/
```

---

## State Management

### Gmail State

**File**: `gmail_state.json`

**Structure**:
```json
{
  "last_email_id": "18f3a2b1c4d5e6f7",
  "last_check_time": "2026-03-20T00:00:00Z",
  "processed_count": 42
}
```

**Persistence**:
- Saved after each successful check
- Atomic write (write to temp, then rename)
- Recovers from corruption

### Vault State

**Implicit State**: File locations represent state
- `Pending_Approval/` = Awaiting approval
- `Approved/` = Approved, awaiting execution
- `Rejected/` = Rejected
- `Done/` = Completed

**No explicit state file needed** - file system is the source of truth

---

## Error Handling

### Gmail Watcher Errors

**Network Errors**:
- Retry with exponential backoff (1s, 2s, 4s, 8s, 16s)
- Max 5 retries before alerting
- Circuit breaker after 10 consecutive failures

**API Errors**:
- Rate limit: Wait for reset time
- Auth error: Create alert in Needs_Action/
- Quota exceeded: Create alert and pause

**Recovery**:
```python
try:
    check_gmail()
except NetworkError:
    retry_with_backoff()
except RateLimitError:
    wait_for_reset()
except AuthError:
    create_alert()
    pause_watcher()
```

### Vault Watcher Errors

**Corrupted Files**:
- Move to `.quarantine/`
- Create alert in `Needs_Action/`
- Log error to audit log

**Permission Errors**:
- Create alert
- Skip file
- Continue monitoring

**Validation Errors**:
- Move to `.quarantine/`
- Create detailed alert with validation errors

---

## Performance

### Gmail Watcher

- **Polling Interval**: 60 seconds
- **Emails per Check**: 10 max
- **Processing Time**: ~2-5 seconds per email
- **Memory Usage**: ~50MB

### Vault Watcher

- **Event Latency**: <1 second
- **File Operations**: Atomic (move, not copy)
- **Memory Usage**: ~30MB
- **CPU Usage**: <1% idle, <5% during events

---

## Monitoring

### Health Checks

Both watchers expose health status:

```python
watcher.get_health_status()
# Returns:
{
    "status": "healthy",
    "last_check": "2026-03-20T00:00:00Z",
    "errors_last_hour": 0,
    "uptime_seconds": 3600
}
```

### Alerts

Watchers create alerts in `Needs_Action/` for:
- Authentication failures
- Repeated errors (>5 in 1 hour)
- Circuit breaker activation
- Corrupted files
- Disk space issues

---

## Configuration

### Environment Variables

```bash
# Gmail Watcher
GMAIL_CHECK_INTERVAL=60
GMAIL_MAX_EMAILS=10
GMAIL_CREDENTIALS_PATH=credentials.json

# Vault Watcher
VAULT_PATH=./AI_Employee_Vault
VAULT_WATCH_RECURSIVE=false
```

### PM2 Configuration

```json
{
  "apps": [
    {
      "name": "gmail_watcher",
      "script": "watchers/gmail_watcher.py",
      "interpreter": "python3",
      "autorestart": true,
      "max_restarts": 10,
      "min_uptime": "10s"
    },
    {
      "name": "vault_watcher",
      "script": "watchers/vault_watcher.py",
      "interpreter": "python3",
      "autorestart": true,
      "max_restarts": 10,
      "min_uptime": "10s"
    }
  ]
}
```

---

## Best Practices

### 1. Atomic Operations

Always use atomic file operations:
```python
# Good: Atomic move
shutil.move(src, dst)

# Bad: Copy then delete (not atomic)
shutil.copy(src, dst)
os.remove(src)
```

### 2. State Persistence

Save state after each successful operation:
```python
process_email()
save_state()  # Persist immediately
```

### 3. Error Recovery

Implement graceful degradation:
```python
try:
    critical_operation()
except Exception as e:
    log_error(e)
    create_alert(e)
    continue_monitoring()  # Don't crash
```

### 4. Resource Cleanup

Always clean up resources:
```python
try:
    file = open(path)
    process(file)
finally:
    file.close()
```

---

## Troubleshooting

### Gmail Watcher Not Processing Emails

**Check**:
1. Credentials valid: `python scripts/verify_gmail_setup.py`
2. Watcher running: `pm2 status gmail_watcher`
3. State file not corrupted: `cat gmail_state.json`
4. Logs for errors: `pm2 logs gmail_watcher`

**Fix**:
```bash
# Reset state
rm gmail_state.json

# Restart watcher
pm2 restart gmail_watcher
```

### Vault Watcher Not Detecting Files

**Check**:
1. Watcher running: `pm2 status vault_watcher`
2. File permissions: `ls -la AI_Employee_Vault/`
3. Watchdog working: `python -c "import watchdog; print('OK')"`

**Fix**:
```bash
# Restart watcher
pm2 restart vault_watcher

# Check logs
pm2 logs vault_watcher --lines 50
```

### High CPU Usage

**Cause**: Too many file system events

**Fix**:
```bash
# Reduce polling frequency
export GMAIL_CHECK_INTERVAL=120

# Restart watchers
pm2 restart all
```

---

## Future Enhancements

1. **Webhook Support**: Replace polling with webhooks for Gmail
2. **Distributed Watching**: Multiple watchers for high availability
3. **Event Replay**: Replay missed events after downtime
4. **Advanced Filtering**: Filter events by pattern before processing
5. **Metrics Export**: Prometheus metrics for monitoring

---

## Conclusion

The Watcher System provides reliable, event-driven automation for the AI Employee system. Its atomic operations, error recovery, and state persistence ensure robust operation even under adverse conditions.
