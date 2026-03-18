# Quickstart Guide: Audit Logging System

**Feature**: 001-audit-logging
**Created**: 2026-03-16
**Audience**: Developers and System Administrators

## Overview

This guide walks you through setting up and using the comprehensive audit logging system for the AI Employee. You'll learn how to:

1. Install dependencies
2. Configure the logging system
3. Integrate logging into existing skills
4. Search and analyze logs
5. Generate compliance reports
6. Verify log integrity

**Estimated Setup Time**: 15-20 minutes

---

## Prerequisites

- Python 3.10 or higher
- AI Employee system installed and configured
- File system permissions for `AI_Employee_Vault/Logs/`
- Cron or Task Scheduler access (for automated rotation)

---

## Step 1: Install Dependencies

### Install Python Packages

```bash
# Install cryptography library for encryption
pip install cryptography>=41.0.0

# Install python-dateutil for timestamp parsing
pip install python-dateutil>=2.8.0

# Verify installation
python -c "from cryptography.fernet import Fernet; print('✓ cryptography installed')"
python -c "import dateutil; print('✓ python-dateutil installed')"
```

### Verify Python Version

```bash
python --version
# Should output: Python 3.10.x or higher
```

---

## Step 2: Create Directory Structure

```bash
# Create logs directory
mkdir -p AI_Employee_Vault/Logs

# Create config directory if not exists
mkdir -p config

# Set appropriate permissions (Linux/Mac)
chmod 700 AI_Employee_Vault/Logs
chmod 600 AI_Employee_Vault/Logs/.encryption_key  # After key generation

# Verify directory exists
ls -la AI_Employee_Vault/Logs
```

---

## Step 3: Generate Encryption Key

**⚠️ IMPORTANT**: The encryption key is critical for accessing logs. Store it securely and back it up.

```bash
# Run key generation script
python scripts/audit_logger.py --generate-key

# This creates: AI_Employee_Vault/Logs/.encryption_key
```

**Key Management**:
- ✅ DO: Back up the key to a secure location
- ✅ DO: Add `.encryption_key` to `.gitignore`
- ❌ DON'T: Commit the key to version control
- ❌ DON'T: Share the key via email or chat

**Backup Command**:
```bash
# Backup key to secure location
cp AI_Employee_Vault/Logs/.encryption_key ~/secure_backup/audit_key_backup_$(date +%Y%m%d)

# Verify backup
ls -l ~/secure_backup/audit_key_backup_*
```

---

## Step 4: Configure Logging

### Create Configuration File

Create `config/logging_config.json`:

```json
{
  "log_directory": "AI_Employee_Vault/Logs",
  "encryption_enabled": true,
  "encryption_key_file": "AI_Employee_Vault/Logs/.encryption_key",
  "rotation_time": "00:00",
  "rotation_max_size_mb": 100,
  "retention_days": 90,
  "compression_enabled": true,
  "integrity_checks_enabled": true,
  "queue_max_size": 1000,
  "flush_interval_seconds": 5
}
```

### Create Sensitive Patterns Configuration

Create `config/sensitive_patterns.json`:

```json
{
  "field_name_patterns": [
    "password", "passwd", "pwd", "pass",
    "api_key", "apikey", "api-key",
    "token", "access_token", "refresh_token",
    "secret", "client_secret",
    "credential", "credentials",
    "private_key", "privatekey"
  ],
  "content_patterns": [
    {
      "name": "aws_key",
      "regex": "AKIA[0-9A-Z]{16}",
      "replacement": "***REDACTED_AWS_KEY***"
    },
    {
      "name": "credit_card",
      "regex": "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b",
      "replacement": "****-****-****-XXXX",
      "show_last_n": 4
    },
    {
      "name": "jwt_token",
      "regex": "eyJ[A-Za-z0-9-_]+\\.eyJ[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+",
      "replacement": "***REDACTED_JWT***"
    },
    {
      "name": "generic_token",
      "regex": "[A-Za-z0-9_\\-]{32,}",
      "replacement": "***REDACTED***"
    }
  ]
}
```

---

## Step 5: Test Basic Logging

### Test Script

Create `test_audit_logging.py`:

```python
#!/usr/bin/env python3
"""Test audit logging system."""

from scripts.audit_logger import AuditLogger

def test_basic_logging():
    """Test basic logging functionality."""
    logger = AuditLogger()

    # Test 1: Log a simple action
    log_id = logger.log_action(
        action_type="system_start",
        actor="system",
        target="audit_logging_test",
        parameters={"test": "basic_logging"},
        result="success"
    )
    print(f"✓ Test 1 passed: Logged action with ID {log_id}")

    # Test 2: Log action with sensitive data
    log_id = logger.log_action(
        action_type="email_send",
        actor="email_mcp",
        target="test@example.com",
        parameters={
            "subject": "Test Email",
            "api_key": "sk_test_1234567890abcdef",  # Should be masked
            "password": "secret123"  # Should be masked
        },
        result="success"
    )
    print(f"✓ Test 2 passed: Logged action with sensitive data (ID: {log_id})")

    # Test 3: Log failed action
    log_id = logger.log_action(
        action_type="invoice_create",
        actor="odoo_mcp",
        target="client_123",
        parameters={"amount": 1000},
        result="failure",
        error="Connection timeout to Odoo server"
    )
    print(f"✓ Test 3 passed: Logged failed action (ID: {log_id})")

    # Flush to ensure all logs written
    logger.flush()
    print("\n✓ All tests passed! Check AI_Employee_Vault/Logs/ for log file.")

if __name__ == "__main__":
    test_basic_logging()
```

### Run Test

```bash
python test_audit_logging.py

# Expected output:
# ✓ Test 1 passed: Logged action with ID a1b2c3d4-...
# ✓ Test 2 passed: Logged action with sensitive data (ID: e5f6g7h8-...)
# ✓ Test 3 passed: Logged failed action (ID: i9j0k1l2-...)
# ✓ All tests passed! Check AI_Employee_Vault/Logs/ for log file.
```

### Verify Logs Created

```bash
# Check log file exists
ls -lh AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl

# View log contents (should show masked sensitive data)
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | python -m json.tool
```

---

## Step 6: Integrate with Existing Skills

### Example: Email MCP Server Integration

Edit `mcp_servers/email_mcp_server.py`:

```python
from scripts.audit_logger import AuditLogger

# Initialize logger (at module level)
audit_logger = AuditLogger()

async def send_email(to: str, subject: str, body: str, **kwargs):
    """Send email with audit logging."""

    # Log action start
    log_id = audit_logger.log_action(
        action_type="email_send",
        actor="email_mcp",
        target=to,
        parameters={
            "subject": subject,
            "body_preview": body[:100],  # First 100 chars
            "has_attachments": "attachments" in kwargs,
            **kwargs  # Sensitive data will be masked
        },
        result="pending"  # Will update after send
    )

    try:
        # Actual email sending logic
        result = await gmail_api.send_message(to, subject, body, **kwargs)

        # Update log with success
        audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target=to,
            parameters={"log_id": log_id, "message_id": result.id},
            result="success"
        )

        return result

    except Exception as e:
        # Update log with failure
        audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target=to,
            parameters={"log_id": log_id},
            result="failure",
            error=str(e)
        )
        raise
```

### Example: Orchestrator Integration

Edit `scripts/orchestrator.py`:

```python
from scripts.audit_logger import AuditLogger

class TaskOrchestrator:
    def __init__(self):
        self.audit_logger = AuditLogger()

    def start(self):
        """Start orchestrator with logging."""
        self.audit_logger.log_action(
            action_type="system_start",
            actor="orchestrator",
            target="task_orchestrator",
            parameters={"version": "1.0"},
            result="success"
        )

    def process_task(self, task_file: str):
        """Process task with logging."""
        workflow_id = str(uuid.uuid4())

        self.audit_logger.log_action(
            action_type="file_write",
            actor="orchestrator",
            target=task_file,
            parameters={"workflow_id": workflow_id},
            result="success",
            metadata={"workflow_id": workflow_id}
        )
```

---

## Step 7: Set Up Automated Rotation

### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Add daily rotation at midnight
0 0 * * * /usr/bin/python3 /path/to/scripts/audit_rotate.py >> /path/to/logs/rotation.log 2>&1

# Add weekly integrity check (Sunday at 2 AM)
0 2 * * 0 /usr/bin/python3 /path/to/scripts/audit_verify.py --all >> /path/to/logs/integrity.log 2>&1

# Verify cron jobs
crontab -l
```

### Windows (Task Scheduler)

```powershell
# Create daily rotation task
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\scripts\audit_rotate.py"
$trigger = New-ScheduledTaskTrigger -Daily -At "00:00"
Register-ScheduledTask -TaskName "AuditLogRotation" -Action $action -Trigger $trigger

# Create weekly integrity check
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\scripts\audit_verify.py --all"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "02:00"
Register-ScheduledTask -TaskName "AuditIntegrityCheck" -Action $action -Trigger $trigger
```

---

## Step 8: Search and Query Logs

### Basic Search

```bash
# Search for all email actions
python scripts/audit_search.py --action-type email_send

# Search for failed actions in date range
python scripts/audit_search.py --start-date 2026-03-01 --end-date 2026-03-31 --result failure

# Search by actor
python scripts/audit_search.py --actor email_mcp --limit 50

# Get specific log entry
python scripts/audit_search.py --id a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Advanced Search (Python API)

```python
from scripts.audit_search import AuditSearch

searcher = AuditSearch()

# Search with multiple filters
results = searcher.search(
    start_date="2026-03-01",
    end_date="2026-03-31",
    action_type="email_send",
    result="success",
    limit=100
)

for entry in results:
    print(f"{entry['timestamp']}: {entry['action_type']} -> {entry['target']}")

# Trace complete workflow
workflow = searcher.trace_workflow(workflow_id="wf-abc-123")
for action in workflow:
    print(f"  {action['action_type']} by {action['actor']}")
```

---

## Step 9: Generate Compliance Reports

### Generate Report

```bash
# Generate JSON report for Q1 2026
python scripts/audit_report.py --start-date 2026-01-01 --end-date 2026-03-31 --format json --output q1_2026_audit.json

# Generate CSV report
python scripts/audit_report.py --start-date 2026-03-01 --end-date 2026-03-31 --format csv --output march_2026_audit.csv

# Generate markdown report
python scripts/audit_report.py --start-date 2026-03-01 --end-date 2026-03-31 --format markdown --output march_2026_audit.md
```

### Verify Retention Compliance

```bash
# Check retention policy compliance
python scripts/audit_report.py --verify-retention

# Expected output:
# ✓ Retention policy: 90 days
# ✓ Oldest log: 2025-12-16 (89 days old)
# ✓ Total log files: 90
# ✓ Compliance status: PASS
```

### Export User Data (GDPR)

```bash
# Export all data for specific user
python scripts/audit_report.py --export-user-data user@example.com --output user_data_export.json
```

---

## Step 10: Verify Log Integrity

### Manual Verification

```bash
# Verify all logs
python scripts/audit_verify.py --all

# Verify specific date
python scripts/audit_verify.py --date 2026-03-16

# Verify specific file
python scripts/audit_verify.py --file AI_Employee_Vault/Logs/audit_2026-03-16.jsonl
```

### Expected Output

```
Verifying log integrity...
✓ audit_2026-03-16.jsonl: PASS (checksum matches)
✓ audit_2026-03-15.jsonl.gz: PASS (checksum matches)
✓ audit_2026-03-14.jsonl.gz: PASS (checksum matches)

Summary:
- Total files checked: 3
- Passed: 3
- Failed: 0
- Status: ALL CHECKS PASSED
```

---

## Common Tasks

### View Today's Logs

```bash
# View raw logs
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl

# View formatted (pretty-print)
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | jq '.'

# Count entries
wc -l AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl
```

### Search with grep

```bash
# Find all email actions
grep '"action_type":"email_send"' AI_Employee_Vault/Logs/audit_*.jsonl

# Find failed actions
grep '"result":"failure"' AI_Employee_Vault/Logs/audit_*.jsonl

# Search compressed logs
zcat AI_Employee_Vault/Logs/audit_*.jsonl.gz | grep '"action_type":"invoice_create"'
```

### Monitor Log Size

```bash
# Check current log size
du -h AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl

# Check total logs size
du -sh AI_Employee_Vault/Logs/

# List all log files with sizes
ls -lh AI_Employee_Vault/Logs/audit_*.jsonl*
```

---

## Troubleshooting

### Issue: Logs not being created

**Symptoms**: No log files in `AI_Employee_Vault/Logs/`

**Solutions**:
1. Check directory permissions: `ls -la AI_Employee_Vault/Logs/`
2. Verify logger is initialized: Check import statements
3. Check for errors: Look for exceptions in application logs
4. Test manually: Run `test_audit_logging.py`

### Issue: Sensitive data not masked

**Symptoms**: Plain-text passwords or API keys in logs

**Solutions**:
1. Verify `sensitive_patterns.json` is loaded
2. Check pattern regex syntax: Test with regex tester
3. Add missing field names to `field_name_patterns`
4. Review logs manually: `grep -i "password" AI_Employee_Vault/Logs/*.jsonl`

### Issue: Encryption key lost

**Symptoms**: Cannot decrypt logs, key file missing

**Solutions**:
1. Check backup location: `ls ~/secure_backup/audit_key_backup_*`
2. Restore from backup: `cp ~/secure_backup/audit_key_backup_* AI_Employee_Vault/Logs/.encryption_key`
3. If no backup: Logs are unrecoverable, generate new key and start fresh

### Issue: Disk space full

**Symptoms**: Logging fails, disk space errors

**Solutions**:
1. Check disk space: `df -h`
2. Compress old logs manually: `gzip AI_Employee_Vault/Logs/audit_2026-*.jsonl`
3. Delete oldest logs: `rm AI_Employee_Vault/Logs/audit_2025-*.jsonl.gz`
4. Reduce retention period: Edit `logging_config.json`

### Issue: Rotation not happening

**Symptoms**: Single large log file, no daily rotation

**Solutions**:
1. Check cron job: `crontab -l`
2. Check cron logs: `grep CRON /var/log/syslog`
3. Run rotation manually: `python scripts/audit_rotate.py`
4. Verify rotation script permissions: `ls -l scripts/audit_rotate.py`

---

## Security Best Practices

### 1. Protect Encryption Key
- ✅ Store key outside of version control
- ✅ Back up key to secure location
- ✅ Restrict file permissions (chmod 600)
- ✅ Never share key via insecure channels

### 2. Restrict Log Access
```bash
# Set restrictive permissions
chmod 700 AI_Employee_Vault/Logs/
chmod 600 AI_Employee_Vault/Logs/*

# Verify permissions
ls -la AI_Employee_Vault/Logs/
```

### 3. Regular Integrity Checks
- Run weekly integrity verification
- Investigate any checksum mismatches immediately
- Keep checksums in separate location from logs

### 4. Monitor Log Access
- Audit logging system logs its own access (SR-007)
- Review access logs regularly
- Alert on unusual access patterns

### 5. Secure Backups
- Back up logs to secure, encrypted storage
- Test backup restoration regularly
- Keep backups for compliance period (90+ days)

---

## Performance Optimization

### For High-Volume Logging

If logging more than 10,000 actions per day:

1. **Increase flush interval**:
   ```json
   "flush_interval_seconds": 10
   ```

2. **Increase queue size**:
   ```json
   "queue_max_size": 5000
   ```

3. **Enable emergency rotation**:
   ```json
   "rotation_max_size_mb": 50
   ```

4. **Use SSD for log storage**: Faster writes

### For Faster Searches

1. **Limit date range**: Search specific dates instead of full 90 days
2. **Use grep for simple queries**: Faster than Python parsing
3. **Compress old logs**: Reduces disk I/O
4. **Consider indexing** (future enhancement): For sub-second queries

---

## Next Steps

1. ✅ Complete setup following this guide
2. ✅ Test logging with sample actions
3. ✅ Integrate with all existing skills
4. ✅ Set up automated rotation
5. ✅ Verify compliance requirements met
6. 📖 Read [data-model.md](./data-model.md) for entity details
7. 📖 Read [plan.md](./plan.md) for architecture overview
8. 🧪 Run full test suite: `pytest tests/test_audit_*.py`

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section above
- Review logs in `AI_Employee_Vault/Logs/`
- Check system logs for errors
- Verify configuration in `config/logging_config.json`

---

**Quickstart Status**: ✅ Complete
**Last Updated**: 2026-03-16
**Version**: 1.0
