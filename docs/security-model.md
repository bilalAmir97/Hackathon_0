# Security Model Documentation

**Version**: 1.0
**Last Updated**: March 2026

---

## Overview

The AI Employee system implements a defense-in-depth security model with multiple layers of protection. Security is built into every component, from input validation to audit logging.

---

## Security Principles

### 1. Human-in-the-Loop

**Principle**: All write operations require explicit human approval

**Implementation**:
- AI proposes actions → Creates approval request
- Human reviews → Approves or rejects
- System executes → Only after approval

**Benefits**:
- Prevents unauthorized actions
- Provides accountability
- Allows human judgment for edge cases

### 2. Least Privilege

**Principle**: Each component has minimal necessary permissions

**Implementation**:
- MCP servers: Read-only by default, write requires approval
- Watchers: Read file system, write to specific folders only
- Approval executor: Execute only approved actions

**Benefits**:
- Limits blast radius of compromises
- Reduces attack surface
- Enforces separation of concerns

### 3. Defense in Depth

**Principle**: Multiple layers of security controls

**Layers**:
1. Input validation
2. Approval workflow
3. Rate limiting
4. Audit logging
5. Error quarantine
6. Credential management

---

## Threat Model

### Threats Considered

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Credential theft | Medium | High | Environment variables, never committed |
| API abuse | Medium | Medium | Rate limiting, approval workflow |
| Malicious input | Low | Medium | Input validation, sanitization |
| Unauthorized access | Low | High | Approval workflow, audit logging |
| Data exfiltration | Low | High | Audit logging, access controls |
| Service disruption | Medium | Medium | Error recovery, circuit breakers |

### Threats Not Considered

- Physical access to server
- Insider threats with root access
- Zero-day exploits in dependencies
- Advanced persistent threats (APTs)

---

## Security Controls

### 1. Credential Management

**Storage**:
- All credentials in environment variables
- Never committed to git
- `.env` file in `.gitignore`

**Access**:
- Only application processes can read
- No credentials in logs or error messages
- Masked in audit logs

**Rotation**:
- Manual rotation via environment variable update
- No hardcoded credentials
- Service restart required after rotation

**Example**:
```bash
# .env file (never committed)
GMAIL_CREDENTIALS_PATH=credentials.json
ODOO_PASSWORD=secure_password_here
TWITTER_API_KEY=xxxxx
```

### 2. Input Validation

**All inputs validated before processing**:

```python
def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email or len(email) > 254:
        return False
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False
    return True

def validate_tweet_text(text: str) -> bool:
    """Validate tweet text length."""
    if not text or len(text) > 280:
        return False
    return True
```

**Validation Rules**:
- Length limits enforced
- Format validation (email, URL, date)
- Character encoding checked
- SQL injection prevention (parameterized queries)
- XSS prevention (HTML escaping)

### 3. Approval Workflow

**All write operations require approval**:

```
1. AI proposes action
   ↓
2. Approval request created in Pending_Approval/
   ↓
3. Human reviews request
   ↓
4. Human moves to Approved/ or Rejected/
   ↓
5. System executes (if approved) or logs (if rejected)
   ↓
6. Action moved to Done/
   ↓
7. Audit log records all steps
```

**Approval File Format**:
```yaml
---
approval_id: UNIQUE_ID
action_type: action_name
risk_assessment: low|medium|high
reasoning: Human-readable explanation
created_at: 2026-03-20T00:00:00Z
---

# Action Details
...
```

**Benefits**:
- Human oversight for all writes
- Audit trail of approvals
- Prevents automated abuse
- Allows risk assessment

### 4. Rate Limiting

**Proactive throttling at 80% capacity**:

```python
class RateLimiter:
    def __init__(self, threshold=0.8):
        self.threshold = threshold

    def check_limit(self, endpoint: str):
        usage = self.get_usage(endpoint)
        if usage >= self.threshold:
            raise RateLimitException(
                f"Rate limit threshold ({self.threshold*100}%) reached"
            )
```

**Per-Service Limits**:
- Gmail API: 250 quota units/user/second
- Twitter API: 50 tweets/24h (free tier)
- Facebook API: 200 calls/hour
- Instagram API: 200 calls/hour

**Benefits**:
- Prevents API quota exhaustion
- Protects against abuse
- Ensures service availability

### 5. Audit Logging

**All actions logged with full context**:

```python
audit_logger.log_action(
    action_type='email_send',
    actor='ai_employee',
    target='customer@example.com',
    parameters={'subject': 'Invoice', 'body': '...'},
    result='success',
    approval={
        'required': True,
        'status': 'approved',
        'approver': 'human_admin',
        'approved_at': '2026-03-20T00:00:00Z'
    }
)
```

**Log Format** (JSONL):
```json
{
  "timestamp": "2026-03-20T00:00:00Z",
  "action_type": "email_send",
  "actor": "ai_employee",
  "target": "customer@example.com",
  "parameters": {"subject": "Invoice"},
  "result": "success",
  "approval": {"status": "approved"}
}
```

**Sensitive Data Masking**:
- Passwords: `***`
- API keys: First 8 + last 4 characters
- Email bodies: Truncated to 100 characters
- Credit card numbers: Masked

**Retention**:
- 90-day retention policy
- Automatic rotation
- Compressed archives for long-term storage

### 6. Error Quarantine

**Corrupted or malicious files isolated**:

```python
def handle_corrupted_file(file_path: str):
    # Move to quarantine
    quarantine_path = vault_path / '.quarantine' / file_path.name
    shutil.move(file_path, quarantine_path)

    # Create alert
    create_alert(
        type='corrupted_file',
        severity='warning',
        file=file_path.name,
        location=str(quarantine_path)
    )
```

**Quarantine Process**:
1. Detect corrupted/invalid file
2. Move to `.quarantine/` folder
3. Create alert in `Needs_Action/`
4. Log to audit log
5. Human reviews and decides action

---

## Access Control

### File System Permissions

```bash
# Vault structure
AI_Employee_Vault/
├── Pending_Approval/  # 755 (rwxr-xr-x)
├── Approved/          # 755 (rwxr-xr-x)
├── Rejected/          # 755 (rwxr-xr-x)
├── Done/              # 755 (rwxr-xr-x)
├── Needs_Action/      # 755 (rwxr-xr-x)
├── Logs/              # 700 (rwx------) - Restricted
└── .quarantine/       # 700 (rwx------) - Restricted
```

### Process Permissions

- Watchers: Read file system, write to vault folders
- MCP servers: Read credentials, call APIs
- Approval executor: Read/write vault folders, execute actions
- Audit logger: Write to logs folder only

---

## Compliance

### GDPR Compliance

**Data Minimization**:
- Only collect necessary data
- No unnecessary personal information
- Automatic data deletion after retention period

**Right to Erasure**:
- Manual deletion of user data
- Audit logs can be filtered/redacted
- Approval files can be deleted

**Data Portability**:
- All data in standard formats (JSON, Markdown)
- Easy export and migration
- No vendor lock-in

**Audit Trail**:
- Complete activity log
- Timestamps for all actions
- Actor identification

### SOC 2 Considerations

**Security**:
- Access controls implemented
- Audit logging comprehensive
- Incident response via alerts

**Availability**:
- Error recovery mechanisms
- Health monitoring
- Automatic restarts

**Confidentiality**:
- Credentials protected
- Sensitive data masked
- Logs access-controlled

---

## Incident Response

### Detection

**Automated Alerts**:
- High error rates (>10%)
- Authentication failures
- Rate limit violations
- Corrupted files
- Disk space issues

**Alert Delivery**:
- Files created in `Needs_Action/`
- Health check runs every 5 minutes
- Weekly audit report includes alerts

### Response

**Incident Response Process**:
1. **Detect**: Alert created in `Needs_Action/`
2. **Assess**: Review alert details and audit logs
3. **Contain**: Stop affected services if needed
4. **Remediate**: Fix root cause
5. **Recover**: Restart services
6. **Review**: Update procedures to prevent recurrence

**Example Response**:
```bash
# 1. Detect: Alert for authentication failure
cat AI_Employee_Vault/Needs_Action/ALERT_AUTH_*.md

# 2. Assess: Check audit logs
tail -100 AI_Employee_Vault/Logs/audit_*.jsonl | grep "auth_error"

# 3. Contain: Stop affected service
pm2 stop gmail_watcher

# 4. Remediate: Fix credentials
vim .env  # Update credentials

# 5. Recover: Restart service
pm2 restart gmail_watcher

# 6. Review: Document incident
echo "Incident: Auth failure. Cause: Expired token. Fix: Refreshed token." >> incidents.log
```

---

## Security Best Practices

### For Developers

1. **Never commit credentials**: Use environment variables
2. **Validate all inputs**: Assume all input is malicious
3. **Log all actions**: Comprehensive audit trail
4. **Fail securely**: Default to deny on errors
5. **Use parameterized queries**: Prevent SQL injection
6. **Escape HTML output**: Prevent XSS
7. **Implement rate limiting**: Prevent abuse
8. **Use HTTPS**: Encrypt data in transit

### For Operators

1. **Rotate credentials regularly**: Every 90 days
2. **Monitor audit logs**: Review weekly
3. **Review alerts promptly**: Within 24 hours
4. **Keep dependencies updated**: Security patches
5. **Backup regularly**: Daily backups
6. **Test disaster recovery**: Quarterly
7. **Limit access**: Principle of least privilege
8. **Document incidents**: Learn from failures

### For Users

1. **Review approval requests carefully**: Don't auto-approve
2. **Report suspicious activity**: Use alerts
3. **Keep credentials secure**: Don't share
4. **Use strong passwords**: 16+ characters
5. **Enable 2FA**: Where available
6. **Review audit logs**: Monthly
7. **Update contact info**: For alerts
8. **Follow security policies**: Compliance

---

## Security Roadmap

### Planned Enhancements

1. **Encryption at Rest**: Encrypt audit logs and sensitive data
2. **Multi-Factor Authentication**: For approval workflow
3. **Role-Based Access Control**: Multiple user roles
4. **Intrusion Detection**: Anomaly detection in logs
5. **Security Scanning**: Automated vulnerability scanning
6. **Penetration Testing**: Annual security audits
7. **Compliance Certifications**: SOC 2, ISO 27001
8. **Bug Bounty Program**: Responsible disclosure

---

## Conclusion

The AI Employee system implements comprehensive security controls at every layer. The human-in-the-loop approval workflow, combined with audit logging and error recovery, provides a secure foundation for business automation.

**Key Takeaways**:
- All write operations require human approval
- Every action is logged for audit
- Multiple layers of security controls
- Defense in depth approach
- Compliance-ready architecture

For security issues or questions, contact: security@example.com
