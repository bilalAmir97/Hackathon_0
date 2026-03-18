# Data Model: Audit Logging System

**Feature**: 001-audit-logging
**Created**: 2026-03-16
**Status**: Draft

## Overview

This document defines the complete data model for the audit logging system, including all entities, their fields, relationships, validation rules, and state transitions.

---

## Core Entities

### 1. LogEntry

**Purpose**: Represents a single action taken by the AI Employee with complete context for audit trail.

**Schema**:

```json
{
  "id": "uuid",
  "timestamp": "ISO 8601 datetime",
  "action_type": "string (enum)",
  "actor": "string (enum)",
  "target": "string",
  "parameters": {
    "key": "value (masked if sensitive)"
  },
  "approval": {
    "required": "boolean",
    "status": "string (enum)",
    "approver": "string or null",
    "approved_at": "ISO 8601 datetime or null"
  },
  "result": "string (enum)",
  "error": "string or null",
  "metadata": {
    "duration_ms": "integer",
    "workflow_id": "uuid or null",
    "parent_action_id": "uuid or null",
    "tags": ["string"]
  }
}
```

**Field Definitions**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| id | UUID | Yes | Unique identifier for log entry | UUID v4 format |
| timestamp | ISO 8601 | Yes | When action occurred | Valid datetime, not future |
| action_type | String | Yes | Category of action | Must be valid ActionType |
| actor | String | Yes | Component that initiated action | Must be valid Actor |
| target | String | Yes | Recipient or resource | Non-empty string |
| parameters | Object | Yes | Action details (masked) | Valid JSON object |
| approval | Object | No | Approval workflow status | Valid ApprovalRecord |
| result | String | Yes | Outcome of action | "success" or "failure" |
| error | String | No | Error details if failed | Present only if result=failure |
| metadata | Object | No | Additional context | Valid JSON object |

**Validation Rules**:

1. `id` must be unique across all log entries
2. `timestamp` must be in ISO 8601 format with timezone
3. `timestamp` cannot be in the future
4. `action_type` must be a valid ActionType enum value
5. `actor` must be a valid Actor enum value
6. `result` must be either "success" or "failure"
7. If `result` is "failure", `error` should be present
8. If `approval.required` is true, `approval.status` must be present
9. `parameters` must not contain plain-text sensitive data

**Relationships**:

- `metadata.workflow_id`: Links related actions in a workflow
- `metadata.parent_action_id`: Links child actions to parent (e.g., retry attempts)

**Example**:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-03-16T14:30:45.123Z",
  "action_type": "email_send",
  "actor": "email_mcp",
  "target": "client@example.com",
  "parameters": {
    "subject": "Invoice #12345",
    "body_preview": "Please find attached...",
    "attachments": ["invoice_12345.pdf"],
    "api_key": "***REDACTED***"
  },
  "approval": {
    "required": true,
    "status": "approved",
    "approver": "human_admin",
    "approved_at": "2026-03-16T14:25:00.000Z"
  },
  "result": "success",
  "error": null,
  "metadata": {
    "duration_ms": 1234,
    "workflow_id": "workflow-abc-123",
    "parent_action_id": null,
    "tags": ["invoice", "client_communication"]
  }
}
```

---

### 2. ActionType (Enum)

**Purpose**: Categorizes the type of action performed for filtering and reporting.

**Values**:

| Value | Description | Example Use Case |
|-------|-------------|------------------|
| email_send | Send email via Gmail | Responding to client inquiry |
| email_receive | Receive/process email | Detecting important email |
| invoice_create | Create invoice in Odoo | Billing client for services |
| invoice_update | Update existing invoice | Correcting invoice amount |
| payment_record | Record payment in Odoo | Marking invoice as paid |
| social_post | Post to social media | LinkedIn/Facebook/Twitter post |
| social_delete | Delete social media post | Removing incorrect post |
| file_write | Write file to vault | Creating action item |
| file_delete | Delete file from vault | Cleaning up completed tasks |
| file_move | Move file between folders | Approval workflow transition |
| approval_request | Request human approval | Submitting draft for review |
| approval_granted | Approval granted | Human approved action |
| approval_denied | Approval denied | Human rejected action |
| system_start | System/service started | Orchestrator startup |
| system_stop | System/service stopped | Graceful shutdown |
| health_check | Health check performed | Monitoring system status |
| error_recovery | Error recovery attempted | Retrying failed action |

**Validation**:
- Must be one of the defined enum values
- Case-sensitive
- Underscore-separated lowercase

**Extension**:
- New action types can be added as features are implemented
- Should follow naming convention: `{domain}_{verb}`

---

### 3. Actor (Enum)

**Purpose**: Identifies which component or process initiated the action for traceability.

**Values**:

| Value | Description | Responsibility |
|-------|-------------|----------------|
| claude_code | Claude Code agent | Reasoning and decision-making |
| orchestrator | Task orchestrator | Task management and coordination |
| gmail_watcher | Gmail monitoring script | Email detection |
| whatsapp_watcher | WhatsApp monitoring script | Message detection |
| linkedin_poster | LinkedIn posting script | Social media automation |
| email_mcp | Email MCP server | Email sending operations |
| odoo_mcp | Odoo MCP server | Accounting operations |
| social_mcp | Social Media MCP server | Facebook/Instagram operations |
| twitter_mcp | Twitter MCP server | Twitter operations |
| human | Human administrator | Manual actions and approvals |
| system | System-level operations | Startup, shutdown, maintenance |
| audit_logger | Audit logging system | Self-logging (access logs) |

**Validation**:
- Must be one of the defined enum values
- Case-sensitive
- Underscore-separated lowercase

**Extension**:
- New actors added when new components are implemented
- Should follow naming convention: `{component}_{type}`

---

### 4. ApprovalRecord

**Purpose**: Tracks human-in-the-loop approval workflow status for sensitive actions.

**Schema**:

```json
{
  "required": "boolean",
  "status": "string (enum)",
  "approver": "string or null",
  "approved_at": "ISO 8601 datetime or null",
  "approval_file": "string or null"
}
```

**Field Definitions**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| required | Boolean | Yes | Whether action needed approval | true or false |
| status | String | Conditional | Approval status | Required if required=true |
| approver | String | Conditional | Who approved/denied | Required if status!=pending |
| approved_at | ISO 8601 | Conditional | When approved/denied | Required if status!=pending |
| approval_file | String | No | Path to approval file | Valid file path |

**Status Values**:

| Status | Description | Next States |
|--------|-------------|-------------|
| pending | Awaiting approval | approved, denied |
| approved | Approved by human | (terminal) |
| denied | Denied by human | (terminal) |
| expired | Approval timeout | (terminal) |
| bypassed | Executed without approval | (terminal) |

**State Transitions**:

```
pending → approved (human approves)
pending → denied (human denies)
pending → expired (timeout reached)
(any) → bypassed (emergency override)
```

**Validation Rules**:

1. If `required` is false, other fields should be null
2. If `required` is true, `status` must be present
3. If `status` is "approved" or "denied", `approver` and `approved_at` must be present
4. `approved_at` must be after the log entry `timestamp`
5. `approver` should be a valid Actor (typically "human")

**Example**:

```json
{
  "required": true,
  "status": "approved",
  "approver": "human",
  "approved_at": "2026-03-16T14:25:00.000Z",
  "approval_file": "AI_Employee_Vault/Approved/EMAIL_client_response_20260316.md"
}
```

---

### 5. SensitivePattern

**Purpose**: Defines regex patterns and field names for detecting and masking sensitive data.

**Schema**:

```json
{
  "name": "string",
  "regex": "string (regex pattern)",
  "field_names": ["string"],
  "replacement": "string",
  "show_last_n": "integer or null"
}
```

**Field Definitions**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | String | Yes | Pattern identifier | Unique, lowercase_underscore |
| regex | String | Yes | Regular expression | Valid regex pattern |
| field_names | Array | Yes | Field names to check | Non-empty array |
| replacement | String | Yes | Mask text | Non-empty string |
| show_last_n | Integer | No | Show last N characters | 0-8 |

**Validation Rules**:

1. `name` must be unique across all patterns
2. `regex` must be a valid regular expression
3. `field_names` must contain at least one field name
4. `replacement` should clearly indicate redaction (e.g., "***REDACTED***")
5. `show_last_n` if present, must be between 0 and 8

**Built-in Patterns**:

| Name | Regex | Field Names | Replacement |
|------|-------|-------------|-------------|
| password | N/A | password, passwd, pwd, pass | ***REDACTED*** |
| api_key | `[A-Za-z0-9_\-]{20,}` | api_key, apikey, key | ***REDACTED*** |
| token | `[A-Za-z0-9_\-]{32,}` | token, access_token, refresh_token | ***REDACTED*** |
| credit_card | `\b(?:\d{4}[- ]?){3}\d{4}\b` | card_number, credit_card, cc | ****-****-****-XXXX |
| aws_key | `AKIA[0-9A-Z]{16}` | (any field) | ***REDACTED_AWS*** |
| jwt_token | `eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+` | (any field) | ***REDACTED_JWT*** |

**Example**:

```json
{
  "name": "credit_card",
  "regex": "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b",
  "field_names": ["card_number", "credit_card", "cc", "payment_method"],
  "replacement": "****-****-****-XXXX",
  "show_last_n": 4
}
```

---

## Derived Entities

### 6. LogFile

**Purpose**: Represents a physical log file on disk with metadata.

**Schema**:

```json
{
  "filename": "string",
  "path": "string",
  "date": "YYYY-MM-DD",
  "size_bytes": "integer",
  "entry_count": "integer",
  "compressed": "boolean",
  "encrypted": "boolean",
  "checksum": "string (SHA-256)",
  "created_at": "ISO 8601 datetime",
  "rotated_at": "ISO 8601 datetime or null"
}
```

**Naming Convention**:
- Active: `audit_YYYY-MM-DD.jsonl`
- Compressed: `audit_YYYY-MM-DD.jsonl.gz`
- Multiple per day: `audit_YYYY-MM-DD_NNN.jsonl` (emergency rotation)

**Lifecycle**:
1. Created at midnight (or first log of day)
2. Appended to throughout the day
3. Rotated at next midnight
4. Compressed after 1 day
5. Deleted after 90 days

---

### 7. ChecksumRecord

**Purpose**: Stores integrity checksums for tamper detection.

**Schema**:

```json
{
  "file": "string (filename)",
  "checksum": "string (SHA-256 hex)",
  "algorithm": "string",
  "calculated_at": "ISO 8601 datetime",
  "file_size": "integer",
  "entry_count": "integer"
}
```

**Storage**: `.checksums.json` in Logs directory

**Validation**:
- Checksum must be 64-character hex string (SHA-256)
- Algorithm must be "sha256"
- File must exist at time of checksum calculation

---

## Relationships

### Workflow Tracing

**Parent-Child Relationships**:
- `metadata.parent_action_id` links retry attempts to original action
- `metadata.workflow_id` groups related actions in a workflow

**Example Workflow**:
```
1. email_receive (workflow_id: wf-123)
   └─> 2. file_write (workflow_id: wf-123, parent: 1)
       └─> 3. approval_request (workflow_id: wf-123, parent: 2)
           └─> 4. approval_granted (workflow_id: wf-123, parent: 3)
               └─> 5. email_send (workflow_id: wf-123, parent: 4)
```

### Approval Workflow Integration

**File-Based State Transitions**:
```
Needs_Action/ → Pending_Approval/ → Approved/ → Done/
     ↓                  ↓                ↓          ↓
file_write      approval_request  approval_granted  file_move
```

Each file move is logged with:
- `action_type`: file_move
- `target`: destination folder
- `parameters.source`: source file path
- `parameters.destination`: destination file path

---

## Validation Rules Summary

### Entry-Level Validation

1. **Uniqueness**: `id` must be unique
2. **Timestamps**: Must be valid ISO 8601, not in future
3. **Enums**: `action_type`, `actor`, `result` must be valid enum values
4. **Consistency**: If `result=failure`, `error` should be present
5. **Approval**: If `approval.required=true`, approval fields must be valid
6. **Masking**: No plain-text sensitive data in `parameters`

### File-Level Validation

1. **Format**: Valid JSONL (one JSON object per line)
2. **Naming**: Follows `audit_YYYY-MM-DD.jsonl` convention
3. **Integrity**: Checksum matches file contents
4. **Encryption**: Encrypted files can be decrypted with key
5. **Retention**: Files older than 90 days are archived/deleted

### System-Level Validation

1. **Completeness**: All actions have corresponding log entries
2. **Ordering**: Timestamps are monotonically increasing within file
3. **Traceability**: Workflow IDs link related actions
4. **Compliance**: Retention policy enforced, GDPR requirements met

---

## Storage Format

### JSONL (JSON Lines)

**Format**: One JSON object per line, newline-separated

**Example File** (audit_2026-03-16.jsonl):
```jsonl
{"id":"uuid1","timestamp":"2026-03-16T10:00:00Z","action_type":"email_receive",...}
{"id":"uuid2","timestamp":"2026-03-16T10:05:00Z","action_type":"file_write",...}
{"id":"uuid3","timestamp":"2026-03-16T10:10:00Z","action_type":"approval_request",...}
```

**Advantages**:
- Append-only (atomic writes)
- Streamable (constant memory)
- Grep-compatible
- No file rewriting needed

### Compression

**Format**: gzip compression (.gz extension)

**Compression Ratio**: Expected 50-70% reduction

**Access**: Via `zcat` or Python `gzip.open()`

---

## Query Patterns

### Common Queries

1. **All actions by type**:
   ```python
   search(action_type="email_send")
   ```

2. **Failed actions in date range**:
   ```python
   search(start_date="2026-03-01", end_date="2026-03-31", result="failure")
   ```

3. **Actions by specific actor**:
   ```python
   search(actor="email_mcp")
   ```

4. **Workflow trace**:
   ```python
   trace_workflow(workflow_id="wf-123")
   ```

5. **Approval audit**:
   ```python
   search(action_type="approval_granted", start_date="2026-03-01")
   ```

### Performance Considerations

- Date range queries: O(n) where n = entries in range
- Action type filter: O(n) with early termination
- Workflow trace: O(n) but typically small n
- Full scan: ~3-5 seconds for 90 days

---

## Extension Points

### Adding New Action Types

1. Add to ActionType enum
2. Document in this file
3. Update integration code to log new actions
4. No schema changes required

### Adding New Actors

1. Add to Actor enum
2. Document in this file
3. Update component to use audit logger
4. No schema changes required

### Adding New Sensitive Patterns

1. Add to sensitive_patterns.json
2. Test with sample data
3. No code changes required (configuration-driven)

---

**Data Model Status**: ✅ Complete
**Next Steps**: Create API contracts and quickstart guide
