# Implementation Plan: Comprehensive Audit Logging System

**Feature Branch**: `001-audit-logging`
**Created**: 2026-03-16
**Status**: Draft
**Spec**: [spec.md](./spec.md)

## Summary

Implement a comprehensive audit logging system that captures all AI Employee actions with sensitive data masking, encryption at rest (AES-256), 90-day retention policy, log integrity verification, and GDPR/SOC 2 compliance features. The system will integrate with all existing skills (email, Odoo, social media, file operations) to provide complete visibility and accountability.

**Key Deliverables**:
- Core audit logger module with sensitive data masking
- Encryption and integrity verification system
- Log rotation and archival automation
- Search and reporting utilities
- Integration hooks for all existing skills
- Compliance reporting tools

## Technical Context

### Technology Stack

- **Language**: Python 3.10+
- **Encryption**: `cryptography` library (Fernet symmetric encryption for AES-256)
- **Storage Format**: JSON Lines (JSONL) for append-only log files
- **File System**: Local file system (AI_Employee_Vault/Logs/)
- **Compression**: gzip for archived logs
- **Scheduling**: System cron jobs for rotation and archival
- **Pattern Matching**: Python `re` module for sensitive data detection

### Key Technical Decisions

**Decision 1: JSON Lines (JSONL) vs Single JSON Array**
- **Chosen**: JSON Lines (one JSON object per line)
- **Rationale**: Append-only writes are atomic, no need to rewrite entire file, easier to stream and search
- **Alternatives**: Single JSON array (requires rewriting entire file), SQLite (adds complexity)

**Decision 2: Fernet (Symmetric) vs Asymmetric Encryption**
- **Chosen**: Fernet symmetric encryption (built on AES-128 CBC with HMAC)
- **Rationale**: Simpler key management for single-instance system, includes integrity verification, sufficient for local storage
- **Alternatives**: AES-256 GCM (more complex), RSA (overkill for local storage)

**Decision 3: In-Process Logging vs Separate Service**
- **Chosen**: In-process logging library imported by all skills
- **Rationale**: Lower latency, simpler deployment, no network overhead, suitable for single-instance system
- **Alternatives**: Separate logging service (adds complexity), remote logging (out of scope)

**Decision 4: Daily Rotation vs Size-Based Rotation**
- **Chosen**: Daily rotation at midnight with size-based emergency rotation
- **Rationale**: Predictable file naming, aligns with compliance reporting periods, emergency rotation prevents disk issues
- **Alternatives**: Size-only rotation (unpredictable file counts), hourly rotation (too many files)

### Dependencies

**External Libraries**:
- `cryptography>=41.0.0` - Encryption and key management
- `python-dateutil>=2.8.0` - ISO 8601 timestamp parsing
- Standard library: `json`, `gzip`, `hashlib`, `re`, `uuid`, `pathlib`

**Internal Dependencies**:
- All existing skills must import and use the audit logger
- Orchestrator must log system-level actions
- Approval workflow must provide approval context
- MCP servers must log external actions

**System Dependencies**:
- File system permissions for AI_Employee_Vault/Logs/
- Cron or Task Scheduler for automated rotation
- Sufficient disk space (1-5 GB for 90 days)

## Constitution Check

Verifying compliance with project principles from `.specify/memory/constitution.md`:

### ✅ Principle 1: Local-First Architecture
- **Compliance**: All logs stored locally in AI_Employee_Vault/Logs/
- **Evidence**: No remote logging, no cloud dependencies, file-based storage

### ✅ Principle 2: Safety Before Autonomy
- **Compliance**: Logging failures do not block primary actions (FR-012)
- **Evidence**: Graceful degradation with in-memory queue, system continues operating

### ✅ Principle 3: File-Based State Management
- **Compliance**: Logs stored as JSONL files, searchable via file system
- **Evidence**: No database required, compatible with Obsidian vault structure

### ✅ Principle 4: Human-in-the-Loop for Sensitive Actions
- **Compliance**: Logs capture approval workflow status (FR-010)
- **Evidence**: Approval records tracked in log entries, audit trail for approvals

### ✅ Principle 5: Perception → Reasoning → Action Pipeline
- **Compliance**: Logging integrated at Action layer, captures all outputs
- **Evidence**: All MCP server actions logged, orchestrator actions logged

### ✅ Principle 6: Secrets Management
- **Compliance**: Sensitive data automatically masked (SR-005), encryption keys stored separately (SR-002)
- **Evidence**: Regex-based masking, key file separate from logs, never log credentials

### ✅ Principle 7: Error Recovery and Resilience
- **Compliance**: Logging failures handled gracefully (FR-012), atomic writes prevent corruption
- **Evidence**: In-memory queue for temporary failures, atomic file operations

### ✅ Principle 8: Observability and Debugging
- **Compliance**: Complete action logging (FR-001), searchable by multiple criteria (FR-009)
- **Evidence**: Full context capture, trace IDs for workflows, error details for failures

### ✅ Principle 9: Compliance and Audit Trail
- **Compliance**: GDPR and SOC 2 compliance (SR-008, SR-009), 90-day retention (FR-006)
- **Evidence**: Compliance reporting tools, data minimization, right to erasure support

### ✅ Principle 10: Minimal External Dependencies
- **Compliance**: Only cryptography library required, standard library for everything else
- **Evidence**: No database, no external services, no cloud dependencies

**Constitution Verdict**: ✅ ALL PRINCIPLES SATISFIED

## Project Structure

```
AI_Employee_Vault/
├── Logs/
│   ├── audit_2026-03-16.jsonl          # Daily log file (current)
│   ├── audit_2026-03-15.jsonl          # Previous day
│   ├── audit_2026-03-14.jsonl.gz       # Compressed older logs
│   ├── .checksums.json                 # Integrity checksums for all logs
│   └── .encryption_key                 # Fernet encryption key (gitignored)
│
scripts/
├── audit_logger.py                     # Core logging module (NEW)
├── audit_search.py                     # Search and query utility (NEW)
├── audit_rotate.py                     # Log rotation script (NEW)
├── audit_report.py                     # Compliance reporting (NEW)
├── audit_verify.py                     # Integrity verification (NEW)
└── orchestrator.py                     # Modified to use audit logger

config/
├── logging_config.json                 # Logging configuration (NEW)
└── sensitive_patterns.json             # Regex patterns for masking (NEW)

tests/
├── test_audit_logger.py                # Unit tests for logger (NEW)
├── test_sensitive_masking.py           # Tests for data masking (NEW)
├── test_encryption.py                  # Tests for encryption (NEW)
├── test_rotation.py                    # Tests for rotation (NEW)
└── test_compliance.py                  # Compliance verification tests (NEW)

.claude/skills/
└── audit-logging/
    └── SKILL.md                        # Agent skill documentation (NEW)
```

## Phase 0: Research & Investigation

### Research Task 1: Encryption Library Selection

**Question**: Which Python encryption library best meets our requirements for AES-256, key management, and integrity verification?

**Investigation**:
- Evaluate `cryptography` library (Fernet, AES-GCM)
- Evaluate `pycryptodome` (AES implementation)
- Compare key management approaches
- Assess integrity verification options (HMAC, GCM)

**Decision Criteria**:
- Industry standard and well-maintained
- Built-in integrity verification
- Simple key management for single-instance
- Compatible with Python 3.10+

**Expected Outcome**: Select `cryptography` library with Fernet (includes AES-128 CBC + HMAC) or AES-256 GCM for encryption.

### Research Task 2: Log Rotation Strategies

**Question**: What is the best approach for daily log rotation with 90-day retention and compression?

**Investigation**:
- Python `logging.handlers.RotatingFileHandler` vs custom rotation
- Cron-based rotation vs in-process rotation
- Compression timing (immediate vs deferred)
- File naming conventions for date-based logs

**Decision Criteria**:
- Atomic rotation (no log loss during rotation)
- Predictable file naming for compliance reports
- Minimal performance impact on logging
- Compatible with encryption and integrity checks

**Expected Outcome**: Custom rotation script triggered by cron at midnight, with emergency size-based rotation in-process.

### Research Task 3: Sensitive Data Pattern Matching

**Question**: What regex patterns effectively detect and mask sensitive data (passwords, API keys, tokens, credit cards)?

**Investigation**:
- Common API key formats (AWS, Google, GitHub, etc.)
- Credit card number patterns (Luhn algorithm validation)
- Password field detection in JSON structures
- Token formats (JWT, OAuth, session tokens)
- SSN and other PII patterns

**Decision Criteria**:
- High detection rate (minimize false negatives)
- Low false positive rate (don't mask legitimate data)
- Configurable and extensible
- Performance impact on logging throughput

**Expected Outcome**: JSON configuration file with regex patterns for common sensitive data types, with field name heuristics (e.g., any field named "password", "api_key", "token").

### Research Task 4: JSONL Performance and Searchability

**Question**: Can JSONL format support fast searching for 90 days of logs without indexing?

**Investigation**:
- JSONL read performance for large files (100MB+)
- Grep-based searching vs Python parsing
- Memory usage for streaming large files
- Compression impact on search performance

**Decision Criteria**:
- Search completes in under 5 seconds (SC-003)
- Memory-efficient for large log files
- Compatible with standard Unix tools (grep, zcat)
- No external indexing required

**Expected Outcome**: JSONL with streaming search, compressed archives searched via zcat + grep, Python utility for structured queries.

### Research Task 5: Integrity Verification Approach

**Question**: How should we implement tamper detection for log files?

**Investigation**:
- SHA-256 checksums per file vs per entry
- Merkle tree for incremental verification
- HMAC for authenticated integrity
- Storage location for checksums

**Decision Criteria**:
- Detects any modification to log files
- Verification completes in under 10 seconds per day (SC-004)
- Checksums protected from tampering
- Simple to implement and maintain

**Expected Outcome**: SHA-256 checksum per log file stored in separate `.checksums.json`, verified on rotation and on-demand.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Core Entities**:

1. **LogEntry**
   - `id` (UUID): Unique identifier
   - `timestamp` (ISO 8601): When action occurred
   - `action_type` (string): Category of action
   - `actor` (string): Component that initiated action
   - `target` (string): Recipient or resource
   - `parameters` (dict): Action details (masked)
   - `approval` (ApprovalRecord): Approval status
   - `result` (string): success/failure
   - `error` (string): Error details if failed
   - `metadata` (dict): Additional context

2. **ActionType** (enum)
   - email_send, email_receive, invoice_create, invoice_update
   - social_post, social_delete, file_write, file_delete
   - approval_granted, approval_denied, system_start, system_stop

3. **Actor** (enum)
   - claude_code, gmail_watcher, whatsapp_watcher, orchestrator
   - email_mcp, odoo_mcp, social_mcp, twitter_mcp, human

4. **ApprovalRecord**
   - `required` (bool): Whether approval was needed
   - `status` (string): pending/approved/denied
   - `approver` (string): Who approved
   - `approved_at` (ISO 8601): When approved

5. **SensitivePattern**
   - `name` (string): Pattern identifier
   - `regex` (string): Regular expression
   - `field_names` (list): Field names to check
   - `replacement` (string): Mask text

### API Contracts

**Logging API** (Python module interface):

```python
# scripts/audit_logger.py

class AuditLogger:
    """Core audit logging interface."""

    def log_action(
        self,
        action_type: str,
        actor: str,
        target: str,
        parameters: dict,
        result: str = "success",
        error: str = None,
        approval: dict = None,
        metadata: dict = None
    ) -> str:
        """
        Log an action taken by the AI Employee.

        Returns: Log entry ID (UUID)
        Raises: Never raises - failures are queued
        """
        pass

    def log_approval(
        self,
        action_id: str,
        approver: str,
        status: str,
        timestamp: str = None
    ) -> None:
        """Update approval status for an action."""
        pass

    def flush(self) -> None:
        """Force write of queued log entries."""
        pass
```

**Search API**:

```python
# scripts/audit_search.py

class AuditSearch:
    """Search and query audit logs."""

    def search(
        self,
        start_date: str = None,
        end_date: str = None,
        action_type: str = None,
        actor: str = None,
        target: str = None,
        result: str = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Search logs by criteria.

        Returns: List of matching log entries
        """
        pass

    def get_by_id(self, log_id: str) -> dict:
        """Retrieve specific log entry by ID."""
        pass

    def trace_workflow(self, initial_id: str) -> list[dict]:
        """Trace complete workflow from initial action."""
        pass
```

**Compliance API**:

```python
# scripts/audit_report.py

class ComplianceReporter:
    """Generate compliance reports."""

    def generate_report(
        self,
        start_date: str,
        end_date: str,
        format: str = "json"
    ) -> str:
        """
        Generate compliance report for date range.

        Formats: json, csv, markdown
        Returns: Report content or file path
        """
        pass

    def verify_retention(self) -> dict:
        """Verify 90-day retention policy compliance."""
        pass

    def export_user_data(self, user_identifier: str) -> dict:
        """Export all data for specific user (GDPR right to access)."""
        pass
```

### Integration Points

**1. All Existing Skills**
- Import `AuditLogger` from `scripts.audit_logger`
- Call `log_action()` before and after each external action
- Provide complete context (action type, target, parameters)
- Handle approval status from approval workflow

**2. MCP Servers**
- Email MCP: Log all send/receive operations
- Odoo MCP: Log invoice creation, payment recording
- Social Media MCP: Log all posts, deletes
- Twitter MCP: Log tweets, mentions

**3. Orchestrator**
- Log system start/stop events
- Log task assignment and completion
- Log error recovery actions
- Provide workflow trace IDs

**4. Approval Workflow**
- Log approval requests (pending status)
- Update log entries when approved/denied
- Include approver identity and timestamp

**5. Watchers**
- Gmail watcher: Log email detection
- WhatsApp watcher: Log message detection
- Log watcher start/stop events

### Configuration

**logging_config.json**:
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

**sensitive_patterns.json**:
```json
{
  "patterns": [
    {
      "name": "api_key",
      "regex": "(?i)(api[_-]?key|apikey)\\s*[:=]\\s*['\"]?([a-zA-Z0-9_\\-]{20,})['\"]?",
      "field_names": ["api_key", "apiKey", "key", "token"],
      "replacement": "***REDACTED***"
    },
    {
      "name": "password",
      "regex": "(?i)(password|passwd|pwd)\\s*[:=]\\s*['\"]?(.+?)['\"]?",
      "field_names": ["password", "passwd", "pwd"],
      "replacement": "***REDACTED***"
    },
    {
      "name": "credit_card",
      "regex": "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b",
      "field_names": ["card_number", "credit_card", "cc"],
      "replacement": "****-****-****-XXXX"
    }
  ]
}
```

## Phase 2: Implementation Tasks

Tasks will be generated in [tasks.md](./tasks.md) using `/sp.tasks` command.

**High-Level Task Breakdown**:

1. **Core Logger Implementation** (P1)
   - Implement AuditLogger class with sensitive data masking
   - Implement in-memory queue for failure resilience
   - Implement atomic file writes
   - Unit tests for all core functionality

2. **Encryption & Integrity** (P1)
   - Implement encryption using cryptography library
   - Implement key generation and management
   - Implement checksum generation and verification
   - Unit tests for encryption and integrity

3. **Log Rotation & Archival** (P1)
   - Implement daily rotation script
   - Implement compression for old logs
   - Implement 90-day retention cleanup
   - Cron job configuration

4. **Search & Query** (P2)
   - Implement AuditSearch class
   - Implement streaming search for large files
   - Implement workflow tracing
   - Performance tests for search speed

5. **Compliance Reporting** (P2)
   - Implement ComplianceReporter class
   - Implement GDPR data export
   - Implement retention verification
   - Generate sample reports

6. **Integration** (P1)
   - Integrate with all existing skills
   - Integrate with MCP servers
   - Integrate with orchestrator
   - Integrate with approval workflow

7. **Testing & Validation** (P1)
   - End-to-end tests for all user stories
   - Performance tests for success criteria
   - Security tests for sensitive data masking
   - Compliance tests for GDPR/SOC 2

8. **Documentation** (P2)
   - Create agent skill documentation
   - Create setup and configuration guide
   - Create compliance guide
   - Create troubleshooting guide

## Testing Strategy

### Unit Tests
- Test sensitive data masking with various patterns
- Test encryption/decryption round-trip
- Test checksum generation and verification
- Test log rotation logic
- Test search query parsing

### Integration Tests
- Test logging from all skills
- Test approval workflow integration
- Test orchestrator integration
- Test MCP server integration

### End-to-End Tests
- Test complete workflows (email → log → search → report)
- Test failure scenarios (disk full, permissions error)
- Test concurrent logging from multiple processes
- Test log rotation during active logging

### Performance Tests
- Verify search completes in under 5 seconds (SC-003)
- Verify integrity check completes in under 10 seconds (SC-004)
- Verify logging throughput (1000+ entries/second)
- Verify compression ratio (>50% reduction)

### Security Tests
- Verify no sensitive data in logs (manual review + automated scan)
- Verify encryption keys not in logs
- Verify file permissions restrict access
- Verify integrity detection catches tampering

### Compliance Tests
- Verify all actions logged (100% coverage)
- Verify 90-day retention enforced
- Verify GDPR data export works
- Verify compliance reports include required fields

## Risk Analysis

### Risk 1: Performance Impact on Actions
- **Probability**: Medium
- **Impact**: High (could slow down all AI actions)
- **Mitigation**: Asynchronous logging with in-memory queue, flush in background
- **Contingency**: Make logging optional with feature flag

### Risk 2: Disk Space Exhaustion
- **Probability**: Low
- **Impact**: High (system failure)
- **Mitigation**: Automatic rotation and compression, disk space monitoring
- **Contingency**: Emergency cleanup of oldest logs, alert administrator

### Risk 3: Sensitive Data Leakage
- **Probability**: Medium
- **Impact**: Critical (compliance violation, security breach)
- **Mitigation**: Comprehensive regex patterns, field name heuristics, manual review
- **Contingency**: Immediate log purge, incident response, pattern updates

### Risk 4: Encryption Key Loss
- **Probability**: Low
- **Impact**: High (cannot read logs)
- **Mitigation**: Key backup instructions, key rotation procedure
- **Contingency**: Accept data loss, regenerate key, start fresh

### Risk 5: Log Tampering
- **Probability**: Low
- **Impact**: Medium (audit trail compromised)
- **Mitigation**: Integrity checksums, file permissions, regular verification
- **Contingency**: Detect tampering, investigate, restore from backup

## Success Metrics

Tracking against success criteria from spec:

- **SC-001**: 100% action coverage → Verify with integration tests
- **SC-002**: 100% sensitive data masked → Automated scanning + manual review
- **SC-003**: Search < 5 seconds → Performance benchmarks
- **SC-004**: Integrity check < 10 seconds → Performance benchmarks
- **SC-005**: Graceful failure handling → Failure injection tests
- **SC-006**: Reports < 30 seconds → Performance benchmarks
- **SC-007**: Compression > 50% → Measure actual compression ratios
- **SC-008**: Retention enforced within 24 hours → Automated verification
- **SC-009**: Zero security incidents → Manual review + security audit
- **SC-010**: 100% workflow traceability → End-to-end tests

## Next Steps

1. Run `/sp.tasks` to generate detailed implementation tasks
2. Create research.md with findings from Phase 0 investigations
3. Create data-model.md with complete entity definitions
4. Begin implementation with P1 tasks (Core Logger, Encryption, Integration)
5. Run tests continuously during implementation (TDD approach)
6. Document as you build (agent skill, setup guide)
7. Final validation against all success criteria before completion

## Open Questions

None - all technical decisions documented in research phase. Implementation can proceed.

---

**Plan Status**: ✅ Ready for Task Generation
**Next Command**: `/sp.tasks`
**Estimated Effort**: 4-6 hours (per roadmap)
