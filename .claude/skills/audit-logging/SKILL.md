# Comprehensive Audit Logging

**Skill Name:** audit-logging
**Category:** Gold Tier - Security & Compliance
**MCP Required:** No

## Purpose

Implement comprehensive audit logging for all AI Employee actions, ensuring full traceability, compliance, and security. Every action taken by the system is logged with complete context for review, debugging, and accountability.

## Prerequisites

- All Silver and Gold Tier skills operational
- Sufficient disk space for logs (minimum 10GB)
- Log rotation configured
- Basic understanding of security compliance

## Setup

### 1. Configure Logging System

Create `config/logging_config.json`:

```json
{
  "version": 1,
  "log_level": "INFO",
  "retention_days": 90,
  "max_file_size_mb": 100,
  "rotation_policy": "daily",
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256"
  },
  "destinations": [
    {
      "type": "file",
      "path": "AI_Employee_Vault/Logs/",
      "format": "json"
    },
    {
      "type": "database",
      "enabled": false,
      "connection": "sqlite:///logs.db"
    }
  ],
  "sensitive_fields": [
    "password",
    "api_key",
    "token",
    "credit_card",
    "ssn"
  ],
  "alert_on": [
    "authentication_failure",
    "unauthorized_access",
    "data_deletion",
    "payment_action",
    "approval_override"
  ]
}
```

### 2. Initialize Logging Module

Create `scripts/audit_logger.py`:

```python
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

class AuditLogger:
    """Comprehensive audit logging for AI Employee actions."""

    def __init__(self, config_path: str = "config/logging_config.json"):
        self.config = self._load_config(config_path)
        self.log_dir = Path("AI_Employee_Vault/Logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_action(
        self,
        action_type: str,
        actor: str,
        target: Optional[str] = None,
        parameters: Optional[Dict] = None,
        result: str = "success",
        approval_status: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log an action with full context.

        Returns: log_id (unique identifier for this log entry)
        """
        log_entry = {
            "log_id": self._generate_log_id(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "parameters": self._sanitize_sensitive_data(parameters or {}),
            "result": result,
            "approval_status": approval_status,
            "metadata": metadata or {},
            "session_id": self._get_session_id(),
            "ip_address": self._get_ip_address(),
            "user_agent": "AI_Employee/1.0"
        }

        # Write to log file
        self._write_log(log_entry)

        # Check if alert needed
        if action_type in self.config.get("alert_on", []):
            self._create_alert(log_entry)

        return log_entry["log_id"]

    def _generate_log_id(self) -> str:
        """Generate unique log ID."""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]

    def _sanitize_sensitive_data(self, data: Dict) -> Dict:
        """Remove or mask sensitive fields."""
        sensitive_fields = self.config.get("sensitive_fields", [])
        sanitized = data.copy()

        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "***REDACTED***"

        return sanitized

    def _write_log(self, log_entry: Dict):
        """Write log entry to file."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{date_str}.json"

        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

### 3. Environment Variables

Add to `.env`:

```bash
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=90
AUDIT_LOG_ENCRYPTION=true
AUDIT_ALERT_EMAIL=your_email@example.com
```

## Usage

### Invoke the Skill

```bash
/audit-logging [action] [options]
```

### Available Actions

1. **View Recent Logs**
   ```
   /audit-logging view --last 50
   ```

2. **Search Logs**
   ```
   /audit-logging search --action "email_send" --date "2026-03-14"
   ```

3. **Generate Audit Report**
   ```
   /audit-logging report --period "last-30-days" --format "pdf"
   ```

4. **Export Logs**
   ```
   /audit-logging export --start "2026-03-01" --end "2026-03-14" --format "csv"
   ```

5. **Verify Log Integrity**
   ```
   /audit-logging verify --date "2026-03-14"
   ```

## Log Entry Schema

Every action is logged with this structure:

```json
{
  "log_id": "a1b2c3d4e5f6g7h8",
  "timestamp": "2026-03-14T10:30:00.123Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {
    "subject": "Invoice #123",
    "attachment": "invoice_123.pdf",
    "cc": [],
    "bcc": []
  },
  "result": "success",
  "approval_status": "approved",
  "approval_by": "human",
  "approval_timestamp": "2026-03-14T10:25:00Z",
  "metadata": {
    "email_id": "msg_123456",
    "size_bytes": 45678,
    "delivery_status": "sent"
  },
  "session_id": "session_abc123",
  "ip_address": "192.168.1.100",
  "user_agent": "AI_Employee/1.0",
  "error_details": null,
  "retry_count": 0,
  "duration_ms": 1234
}
```

## Action Types

All logged action types:

### Communication Actions
- `email_send` - Email sent via MCP
- `email_draft` - Email draft created
- `whatsapp_message` - WhatsApp message sent
- `social_post` - Social media post published
- `social_reply` - Reply to social media mention

### Financial Actions
- `invoice_create` - Invoice created in Odoo
- `payment_record` - Payment recorded
- `expense_create` - Expense logged
- `financial_report` - Report generated
- `subscription_cancel` - Subscription cancelled

### File Operations
- `file_read` - File accessed
- `file_write` - File created/modified
- `file_delete` - File deleted
- `file_move` - File moved between folders

### System Actions
- `watcher_start` - Watcher process started
- `watcher_stop` - Watcher process stopped
- `approval_request` - Approval requested
- `approval_granted` - Approval granted
- `approval_denied` - Approval denied
- `error_occurred` - Error logged
- `authentication` - Authentication attempt

## Integration with All Skills

Every skill automatically logs actions:

### Example: Email Send

```python
# In send-email skill
from scripts.audit_logger import AuditLogger

logger = AuditLogger()

# Before sending email
log_id = logger.log_action(
    action_type="email_send",
    actor="claude_code",
    target="client@example.com",
    parameters={
        "subject": "Invoice #123",
        "attachment": "invoice_123.pdf"
    },
    approval_status="approved",
    metadata={
        "approval_file": "APPROVAL_email_123.md",
        "approval_timestamp": "2026-03-14T10:25:00Z"
    }
)

# Send email via MCP
result = send_email(...)

# Update log with result
logger.update_log(
    log_id=log_id,
    result="success" if result else "failure",
    metadata={
        "email_id": result.message_id,
        "delivery_status": "sent"
    }
)
```

### Example: Odoo Invoice

```python
# In odoo-accounting skill
log_id = logger.log_action(
    action_type="invoice_create",
    actor="claude_code",
    target="Client A",
    parameters={
        "amount": 1500.00,
        "description": "January Services",
        "due_date": "2026-04-14"
    },
    approval_status="approved"
)

# Create invoice in Odoo
invoice = odoo.create_invoice(...)

# Update log
logger.update_log(
    log_id=log_id,
    result="success",
    metadata={
        "invoice_id": invoice.id,
        "invoice_number": "INV-2026-123"
    }
)
```

## Audit Reports

### Daily Summary

Generated automatically at midnight:

```markdown
# Audit Summary - 2026-03-14

## Activity Overview

- **Total Actions:** 127
- **Successful:** 124 (97.6%)
- **Failed:** 3 (2.4%)
- **Requiring Approval:** 15
- **Approved:** 14
- **Denied:** 1

## Actions by Type

| Action Type | Count | Success Rate |
|-------------|-------|--------------|
| email_send | 23 | 100% |
| social_post | 8 | 100% |
| file_write | 45 | 97.8% |
| invoice_create | 2 | 100% |
| payment_record | 1 | 100% |

## Security Events

- **Authentication Attempts:** 5 (all successful)
- **Unauthorized Access:** 0
- **Approval Overrides:** 0
- **Data Deletions:** 2 (both approved)

## Failed Actions

1. **email_send** - 10:45 AM - Network timeout (retried successfully)
2. **file_write** - 2:30 PM - Permission denied (resolved)
3. **social_post** - 4:15 PM - API rate limit (queued for retry)

## Recommendations

- ✅ All critical actions properly approved
- ✅ No security incidents
- ⚠️ Consider increasing API rate limits for social media
```

### Monthly Compliance Report

```markdown
# Monthly Compliance Report - March 2026

## Executive Summary

All actions properly logged and audited. 100% approval compliance for sensitive actions. No security incidents.

## Compliance Metrics

- **Total Actions Logged:** 3,456
- **Approval Compliance:** 100%
- **Log Integrity:** ✅ Verified
- **Retention Policy:** ✅ Compliant (90 days)
- **Encryption:** ✅ Enabled

## Sensitive Actions

| Action Type | Count | Approval Rate | Average Response Time |
|-------------|-------|---------------|----------------------|
| Payment | 12 | 100% | 2.3 hours |
| Invoice | 45 | 100% | 1.8 hours |
| Data Deletion | 8 | 100% | 4.5 hours |
| Subscription Cancel | 2 | 100% | 12 hours |

## Security Audit

- **Authentication Failures:** 0
- **Unauthorized Access Attempts:** 0
- **Suspicious Activity:** 0
- **Data Breaches:** 0

## Recommendations

1. ✅ Continue current security practices
2. ✅ Maintain approval workflow for sensitive actions
3. 💡 Consider implementing 2FA for high-value transactions
```

## Log Rotation

Automatic log rotation configured:

```bash
# scripts/rotate_logs.sh
#!/bin/bash

LOG_DIR="AI_Employee_Vault/Logs"
RETENTION_DAYS=90
ARCHIVE_DIR="AI_Employee_Vault/Logs/archive"

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Find logs older than retention period
find "$LOG_DIR" -name "audit_*.json" -mtime +$RETENTION_DAYS -exec gzip {} \;

# Move compressed logs to archive
find "$LOG_DIR" -name "audit_*.json.gz" -exec mv {} "$ARCHIVE_DIR/" \;

# Delete archives older than 1 year
find "$ARCHIVE_DIR" -name "audit_*.json.gz" -mtime +365 -delete

echo "Log rotation complete: $(date)"
```

Schedule in crontab:

```bash
# Rotate logs weekly on Sunday at 11 PM
0 23 * * 0 cd $PROJECT_DIR && bash scripts/rotate_logs.sh >> /tmp/ai-employee-cron.log 2>&1
```

## Security Features

### 1. Sensitive Data Masking

Automatically masks sensitive fields:

```json
{
  "action_type": "payment_record",
  "parameters": {
    "amount": 1500.00,
    "credit_card": "***REDACTED***",
    "cvv": "***REDACTED***",
    "account_number": "***REDACTED***"
  }
}
```

### 2. Log Integrity Verification

Each log file includes checksum:

```python
def verify_log_integrity(log_file: Path) -> bool:
    """Verify log file hasn't been tampered with."""
    with open(log_file, 'r') as f:
        content = f.read()

    # Calculate checksum
    checksum = hashlib.sha256(content.encode()).hexdigest()

    # Compare with stored checksum
    checksum_file = log_file.with_suffix('.sha256')
    if checksum_file.exists():
        stored_checksum = checksum_file.read_text().strip()
        return checksum == stored_checksum

    return False
```

### 3. Encryption at Rest

Logs encrypted using AES-256:

```python
from cryptography.fernet import Fernet

def encrypt_log_file(log_file: Path, key: bytes):
    """Encrypt log file for secure storage."""
    f = Fernet(key)

    with open(log_file, 'rb') as file:
        data = file.read()

    encrypted = f.encrypt(data)

    with open(log_file.with_suffix('.encrypted'), 'wb') as file:
        file.write(encrypted)
```

## Alert System

Automatic alerts for critical events:

```markdown
---
type: security_alert
priority: high
created: 2026-03-14T10:30:00Z
---

# Security Alert: Unauthorized Access Attempt

**Event:** Unauthorized file access attempt
**Timestamp:** 2026-03-14 10:30:00 UTC
**Actor:** unknown
**Target:** AI_Employee_Vault/.env
**Result:** Blocked

## Details

An attempt was made to access the .env file containing sensitive credentials. Access was denied due to insufficient permissions.

## Actions Taken

- ✅ Access blocked
- ✅ Event logged
- ✅ Alert created
- ✅ Admin notified

## Recommended Actions

- [ ] Review system access logs
- [ ] Verify no other unauthorized attempts
- [ ] Consider changing credentials if breach suspected
```

## Compliance Features

### GDPR Compliance

- Right to access: Export all logs for specific user
- Right to erasure: Securely delete logs on request
- Data minimization: Only log necessary information
- Retention limits: Automatic deletion after 90 days

### SOC 2 Compliance

- Access controls: Role-based log access
- Audit trails: Complete action history
- Encryption: Data encrypted at rest and in transit
- Monitoring: Real-time security monitoring

## Troubleshooting

**Q: Logs not being created**
- Check disk space availability
- Verify log directory permissions
- Review audit_logger.py for errors

**Q: Log file too large**
- Reduce retention period
- Enable log compression
- Implement more aggressive rotation

**Q: Cannot verify log integrity**
- Check if checksum file exists
- Verify encryption key is correct
- Review for potential tampering

## References

- [GDPR Compliance Guide](https://gdpr.eu)
- [SOC 2 Requirements](https://www.aicpa.org/soc2)
- [Security Logging Best Practices](https://owasp.org/www-project-logging-guide/)

## Gold Tier Completion Criteria

- ✅ Audit logging implemented for all actions
- ✅ Log rotation configured
- ✅ Sensitive data masking enabled
- ✅ Log integrity verification working
- ✅ Encryption at rest enabled
- ✅ Alert system operational
- ✅ Daily and monthly reports generated
- ✅ Compliance features implemented
- ✅ 90-day retention policy enforced
