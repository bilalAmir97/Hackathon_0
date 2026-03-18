# Audit Logging System - Setup Guide

Quick setup guide for the comprehensive audit logging system.

## Prerequisites

- Python 3.10+
- 10GB+ free disk space for logs
- Write permissions to `AI_Employee_Vault/Logs/`

## Quick Start (5 minutes)

### 1. Create Log Directory

```bash
mkdir -p AI_Employee_Vault/Logs
```

### 2. Create Configuration File

Create `AI_Employee_Vault/Logs/logging_config.json`:

```json
{
  "log_directory": "AI_Employee_Vault/Logs",
  "encryption_enabled": false,
  "queue_max_size": 1000,
  "flush_interval_seconds": 5,
  "rotation_max_size_mb": 100,
  "retention_days": 90
}
```

### 3. Test the System

```bash
# Run all tests to verify installation
python -m pytest tests/test_audit_*.py -v

# Should see all tests passing
```

### 4. Log Your First Action

```python
from scripts.audit_logger import AuditLogger

logger = AuditLogger()

action_id = logger.log_action(
    action_type="test_action",
    actor="setup_test",
    target="system",
    parameters={"test": "hello world"},
    result="success"
)

logger.flush()
print(f"Logged action: {action_id}")
```

### 5. Verify Log Created

```bash
# Check log file exists
ls -lh AI_Employee_Vault/Logs/

# View log content
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl
```

## Configuration Options

### Basic Configuration

Minimal config for development:

```json
{
  "log_directory": "AI_Employee_Vault/Logs",
  "encryption_enabled": false,
  "queue_max_size": 1000,
  "flush_interval_seconds": 5
}
```

### Production Configuration

Recommended for production:

```json
{
  "log_directory": "AI_Employee_Vault/Logs",
  "encryption_enabled": true,
  "encryption_key": "your-32-byte-encryption-key-here",
  "queue_max_size": 5000,
  "flush_interval_seconds": 10,
  "rotation_max_size_mb": 100,
  "retention_days": 90
}
```

### High-Volume Configuration

For systems with >1000 actions/day:

```json
{
  "log_directory": "AI_Employee_Vault/Logs",
  "encryption_enabled": false,
  "queue_max_size": 10000,
  "flush_interval_seconds": 30,
  "rotation_max_size_mb": 500,
  "retention_days": 90
}
```

## Automated Log Rotation

### Setup Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add daily rotation at midnight
0 0 * * * cd /path/to/AI_Employee && python scripts/audit_rotate.py --scheduled >> /tmp/audit-rotate.log 2>&1

# Add weekly integrity check on Sundays at 2 AM
0 2 * * 0 cd /path/to/AI_Employee && python scripts/audit_verify.py --verify-all >> /tmp/audit-verify.log 2>&1
```

### Setup Task Scheduler (Windows)

Create `rotate_logs.bat`:

```batch
@echo off
cd C:\path\to\AI_Employee
python scripts\audit_rotate.py --scheduled >> C:\temp\audit-rotate.log 2>&1
```

Schedule in Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Audit Log Rotation"
4. Trigger: Daily at 12:00 AM
5. Action: Start a program
6. Program: `C:\path\to\AI_Employee\rotate_logs.bat`

## Integration with Existing Components

### Add to Email MCP

```python
# In your email MCP server
from scripts.audit_logger import AuditLogger

class EmailMCP:
    def __init__(self):
        self.audit_logger = AuditLogger()

    def send_email(self, to, subject, body):
        try:
            # Send email
            result = self._send_via_smtp(to, subject, body)

            # Log success
            self.audit_logger.log_action(
                action_type="email_send",
                actor="email_mcp",
                target=to,
                parameters={
                    "subject": subject,
                    "body_preview": body[:100]
                },
                result="success",
                metadata={"message_id": result.message_id}
            )

            return result

        except Exception as e:
            # Log failure
            self.audit_logger.log_action(
                action_type="email_send",
                actor="email_mcp",
                target=to,
                parameters={"subject": subject},
                result="failure",
                error=str(e)
            )
            raise
```

### Add to Orchestrator

```python
# In scripts/orchestrator.py
from scripts.audit_logger import AuditLogger
import uuid

class Orchestrator:
    def __init__(self):
        self.audit_logger = AuditLogger()

    def process_email(self, email):
        # Generate workflow ID for traceability
        workflow_id = f"wf-email-{uuid.uuid4()}"

        # Log email received
        step1_id = self.audit_logger.log_action(
            action_type="email_receive",
            actor="orchestrator",
            target="inbox",
            parameters={"from": email.sender},
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Create action item
        step2_id = self.audit_logger.log_action(
            action_type="file_write",
            actor="orchestrator",
            target="Needs_Action/EMAIL_item.md",
            parameters={"content_preview": email.subject},
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step1_id
            }
        )
```

## Searching and Analysis

### Command Line Search

```bash
# Search by action type
python scripts/audit_search.py --action-type email_send

# Search by date range
python scripts/audit_search.py --start-date 2024-03-01 --end-date 2024-03-15

# Search failed actions
python scripts/audit_search.py --result failure

# Trace workflow
python scripts/audit_search.py --workflow-id wf-email-001
```

### Python Search API

```python
from scripts.audit_search import AuditSearch

searcher = AuditSearch(log_directory="AI_Employee_Vault/Logs")

# Find all failed actions today
from datetime import datetime
today = datetime.utcnow().strftime("%Y-%m-%d")
failed = searcher.search(
    result="failure",
    start_date=today,
    end_date=today
)

print(f"Found {len(failed)} failed actions today")
for action in failed:
    print(f"  - {action['action_type']}: {action['error']}")
```

## Integrity Verification

### Generate Checksums

```bash
# Generate checksums for all log files
python scripts/audit_verify.py --generate
```

### Verify Integrity

```bash
# Verify all logs
python scripts/audit_verify.py --verify-all

# Verify specific date range
python scripts/audit_verify.py --verify-date 2024-03-01 2024-03-15
```

### Automated Verification

Add to cron (weekly check):

```bash
# Every Sunday at 2 AM
0 2 * * 0 cd /path/to/AI_Employee && python scripts/audit_verify.py --verify-all
```

## Security Setup

### 1. Protect Log Directory

```bash
# Restrict access to logs
chmod 700 AI_Employee_Vault/Logs
chown your_user:your_group AI_Employee_Vault/Logs
```

### 2. Add to .gitignore

```bash
# Add to .gitignore
echo "AI_Employee_Vault/Logs/*.jsonl" >> .gitignore
echo "AI_Employee_Vault/Logs/*.jsonl.gz" >> .gitignore
echo "AI_Employee_Vault/Logs/.encryption_key" >> .gitignore
echo "AI_Employee_Vault/Logs/.checksums.json" >> .gitignore
```

### 3. Enable Encryption (Optional)

```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to config
# "encryption_enabled": true,
# "encryption_key": "your-generated-key-here"
```

### 4. Backup Encryption Key

```bash
# Store key securely (NOT in git)
echo "your-encryption-key" > ~/.ai_employee_encryption_key
chmod 600 ~/.ai_employee_encryption_key
```

## Monitoring and Alerts

### Check Log Health

```bash
# Check disk usage
du -sh AI_Employee_Vault/Logs/

# Count log entries today
wc -l AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl

# Check for errors
grep '"result": "failure"' AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl
```

### Monitor Failed Actions

```python
from scripts.audit_search import AuditSearch
from datetime import datetime

searcher = AuditSearch()
today = datetime.utcnow().strftime("%Y-%m-%d")

failed = searcher.search(
    result="failure",
    start_date=today,
    end_date=today
)

if len(failed) > 10:
    print(f"WARNING: {len(failed)} failed actions today!")
    # Send alert email or notification
```

## Troubleshooting

### Logs Not Being Created

**Check 1: Directory exists and writable**
```bash
ls -la AI_Employee_Vault/Logs/
touch AI_Employee_Vault/Logs/test.txt && rm AI_Employee_Vault/Logs/test.txt
```

**Check 2: Config file valid**
```bash
python -c "import json; json.load(open('AI_Employee_Vault/Logs/logging_config.json'))"
```

**Check 3: Force flush**
```python
logger.flush()  # Force immediate write
```

### Disk Space Full

**Check disk usage**
```bash
df -h
du -sh AI_Employee_Vault/Logs/
```

**Emergency cleanup**
```bash
# Compress old logs
python scripts/audit_rotate.py --compress

# Delete logs older than 30 days
python scripts/audit_rotate.py --cleanup --retention-days 30
```

### Search Performance Slow

**Solution 1: Compress old logs**
```bash
python scripts/audit_rotate.py --compress
```

**Solution 2: Use date filters**
```python
# Instead of searching all logs
results = searcher.search(action_type="email_send")

# Search specific date range
results = searcher.search(
    action_type="email_send",
    start_date="2024-03-15",
    end_date="2024-03-16"
)
```

### Integrity Check Fails

**Regenerate checksums**
```bash
python scripts/audit_verify.py --generate
```

**Investigate tampering**
```bash
python scripts/audit_verify.py --verify-all
# Check output for tampered files
```

## Performance Tuning

### For High-Volume Systems

```json
{
  "queue_max_size": 10000,
  "flush_interval_seconds": 30,
  "rotation_max_size_mb": 500
}
```

### For Low-Latency Requirements

```json
{
  "queue_max_size": 100,
  "flush_interval_seconds": 1,
  "rotation_max_size_mb": 50
}
```

## Testing Your Setup

### Run Full Test Suite

```bash
# Run all audit logging tests
python -m pytest tests/test_audit_*.py tests/test_e2e_*.py tests/test_compliance.py -v

# Should see 50+ tests passing
```

### Manual Integration Test

```python
from scripts.audit_logger import AuditLogger
from scripts.audit_search import AuditSearch
import uuid

# 1. Log a workflow
logger = AuditLogger()
workflow_id = f"test-{uuid.uuid4()}"

step1 = logger.log_action(
    action_type="test_start",
    actor="setup_test",
    target="system",
    parameters={"test": "integration"},
    result="success",
    metadata={"workflow_id": workflow_id}
)

step2 = logger.log_action(
    action_type="test_complete",
    actor="setup_test",
    target="system",
    parameters={"test": "integration"},
    result="success",
    metadata={
        "workflow_id": workflow_id,
        "parent_action_id": step1
    }
)

logger.flush()

# 2. Search for workflow
searcher = AuditSearch()
workflow = searcher.trace_workflow(workflow_id)

# 3. Verify
assert len(workflow) == 2
assert workflow[0]["action_type"] == "test_start"
assert workflow[1]["action_type"] == "test_complete"
assert workflow[1]["metadata"]["parent_action_id"] == step1

print("✓ Integration test passed!")
```

## Next Steps

1. ✓ Complete setup (you're done!)
2. Integrate with your components (see Integration section)
3. Set up automated rotation (see Cron Job section)
4. Configure monitoring (see Monitoring section)
5. Review logs regularly for insights

## Support

- Documentation: `.claude/skills/audit-logging/SKILL.md`
- Specification: `specs/004-audit-logging/spec.md`
- Tests: `tests/test_audit_*.py`
- Implementation: `scripts/audit_*.py`

## Quick Reference

```bash
# Log action
python -c "from scripts.audit_logger import AuditLogger; logger = AuditLogger(); logger.log_action('test', 'user', 'target', {}, 'success'); logger.flush()"

# Search logs
python scripts/audit_search.py --action-type email_send

# Rotate logs
python scripts/audit_rotate.py --rotate

# Verify integrity
python scripts/audit_verify.py --verify-all

# Run tests
python -m pytest tests/test_audit_*.py -v
```
