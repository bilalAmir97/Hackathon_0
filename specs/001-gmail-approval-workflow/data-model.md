# Data Model: Gmail Watcher + Approval Workflow

**Feature**: 001-gmail-approval-workflow
**Created**: 2026-02-25
**Purpose**: Define entity schemas for file-based state management

## Entity Definitions

### 1. Email Action Item

**Purpose**: Represents a detected important email requiring human review

**Location**: `AI_Employee_Vault/Needs_Action/EMAIL_{timestamp}_{from}.md`

**Filename Convention (M2 Clarification)**:
- Format: `EMAIL_YYYYMMDD_HHMMSS_{sanitized_from}.md`
- Timestamp: UTC time in compact format (e.g., `20260225_143022`)
- Sanitized from: Email address with special characters replaced
  - Replace `@` with `_at_`
  - Replace `.` with `_`
  - Remove all other special characters
  - Truncate to max 30 characters
  - Example: `john.doe@example.com` → `john_doe_at_example_com`
  - Example: `very.long.email.address@company.co.uk` → `very_long_email_address_at_c` (truncated)
- Max total filename length: 100 characters (including .md extension)
- Collision handling: If file exists, append `_N` where N is incrementing number (e.g., `_2`, `_3`)
- Example full filename: `EMAIL_20260225_143022_john_doe_at_example_com.md`

**Attributes**:
- `email_id` (string, required): Gmail message ID (unique identifier)
- `thread_id` (string, required): Gmail thread ID
- `from` (string, required): Sender email address and name
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject line
- `date` (string, required): Email date in ISO 8601 format
- `snippet` (string, required): Preview text (first 200 chars)
- `body` (string, required): Email body (first 1000 chars)
- `labels` (array, optional): Gmail labels applied to email
- `priority_keywords` (array, optional): Detected priority keywords
- `created_at` (string, required): Action file creation timestamp (ISO 8601)
- `status` (string, required): Workflow state (pending, approved, rejected, done)

**Validation Rules**:
- `email_id` must be unique across all action files
- `date` and `created_at` must be valid ISO 8601 timestamps
- `status` must be one of: pending, approved, rejected, done
- `from` and `to` must contain valid email addresses

**State Transitions**:
- Created → pending (in Needs_Action/)
- pending → awaiting_approval (moved to Pending_Approval/)
- awaiting_approval → approved (moved to Approved/)
- awaiting_approval → rejected (moved to Rejected/)
- approved → done (moved to Done/ after execution)
- rejected → done (moved to Done/ without execution)

**Relationships**:
- One Email Action Item may have one Approval Request
- One Email Action Item may have multiple Log Entries

---

### 2. Approval Request

**Purpose**: Represents a pending decision on a sensitive action

**Location**: `AI_Employee_Vault/Pending_Approval/APPROVAL_{timestamp}_{action_type}.md`

**Attributes**:
- `approval_id` (string, required): Unique approval identifier
- `action_type` (string, required): Type of action (email_send, payment, api_call)
- `email_action_ref` (string, required): Reference to Email Action Item (email_id)
- `action_params` (object, required): Parameters for action execution
  - `recipient` (string): Email recipient
  - `subject` (string): Email subject
  - `body` (string): Email body
  - `attachments` (array): Attachment references
- `risk_assessment` (string, required): Risk level (low, medium, high)
- `reasoning` (string, required): Why this action is needed
- `alternatives_considered` (array, optional): Other approaches evaluated
- `created_at` (string, required): Approval request creation timestamp
- `approved_at` (string, optional): Approval timestamp
- `approved_by` (string, optional): Human approver identifier
- `rejection_reason` (string, optional): Reason for rejection

**Validation Rules**:
- `approval_id` must be unique
- `action_type` must be one of: email_send, payment, api_call
- `email_action_ref` must reference existing Email Action Item
- `risk_assessment` must be one of: low, medium, high
- `action_params` must contain required fields for action_type
- If approved, `approved_at` and `approved_by` are required
- If rejected, `rejection_reason` is required

**State Transitions**:
- Created → pending (in Pending_Approval/)
- pending → approved (moved to Approved/)
- pending → rejected (moved to Rejected/)

**Relationships**:
- One Approval Request references one Email Action Item
- One Approval Request may have multiple Log Entries

---

### 3. Log Entry

**Purpose**: Represents a completed action or system event

**Location**: `AI_Employee_Vault/Logs/YYYY-MM-DD.json` (JSON Lines format)

**Attributes**:
- `timestamp` (string, required): Event timestamp (ISO 8601 with milliseconds)
- `log_id` (string, required): Unique log entry identifier (UUID)
- `action_type` (string, required): Type of action (email_detected, email_sent, approval_granted, approval_rejected, error, system_event)
- `email_id` (string, optional): Reference to Email Action Item
- `approval_id` (string, optional): Reference to Approval Request
- `status` (string, required): Execution status (success, failure, pending)
- `inputs` (object, optional): Action input parameters
- `outputs` (object, optional): Action output/results
- `error_details` (object, optional): Error information if status=failure
  - `error_type` (string): Error classification
  - `error_message` (string): Human-readable error
  - `stack_trace` (string): Technical details
- `retry_count` (integer, optional): Number of retry attempts (0-3)
- `execution_time_ms` (integer, optional): Action duration in milliseconds

**Validation Rules**:
- `timestamp` must be valid ISO 8601 with timezone
- `log_id` must be unique (UUID v4)
- `action_type` must be one of defined types
- `status` must be one of: success, failure, pending
- If `status=failure`, `error_details` is required
- `retry_count` must be 0-3

**Relationships**:
- One Log Entry may reference one Email Action Item
- One Log Entry may reference one Approval Request

---

### 4. Watcher State

**Purpose**: Persistent state for Gmail watcher (idempotency)

**Location**: `AI_Employee_Vault/.state/gmail_watcher_state.json`

**Attributes**:
- `last_poll_timestamp` (string, required): Last successful poll time (ISO 8601)
- `processed_email_ids` (array, required): Set of processed email IDs
- `error_count` (integer, required): Consecutive error count (0-10)
- `last_error` (object, optional): Last error details
  - `timestamp` (string): Error occurrence time
  - `error_type` (string): Error classification
  - `error_message` (string): Error description
- `config` (object, required): Watcher configuration
  - `poll_interval_seconds` (integer): Polling interval (60-600)
  - `priority_keywords` (array): Keywords for priority detection
  - `max_emails_per_poll` (integer): Limit per poll cycle (1-50)

**Validation Rules**:
- `last_poll_timestamp` must be valid ISO 8601
- `processed_email_ids` must be array of strings (email IDs)
- `error_count` must be 0-10
- `poll_interval_seconds` must be 60-600
- `max_emails_per_poll` must be 1-50

**State Management**:
- File is created on first watcher run
- Updated after each successful poll
- `processed_email_ids` grows unbounded (consider archiving after 10,000 entries)
- `error_count` resets to 0 on successful poll
- If `error_count` reaches 10, watcher pauses and alerts human

---

### 5. Action Plan

**Purpose**: Reasoning artifact for MCP execution (constitution requirement)

**Location**: `AI_Employee_Vault/Plans/PLAN_{timestamp}_{action_type}.md`

**Attributes**:
- `plan_id` (string, required): Unique plan identifier
- `approval_ref` (string, required): Reference to Approval Request
- `problem_statement` (string, required): What needs to be done
- `analysis` (string, required): Situation analysis
- `alternatives` (array, required): Options considered
  - `option` (string): Alternative approach
  - `pros` (array): Advantages
  - `cons` (array): Disadvantages
- `chosen_approach` (string, required): Selected solution
- `rationale` (string, required): Why this approach was chosen
- `expected_outcomes` (array, required): Predicted results
- `risk_mitigation` (array, required): Risk handling strategies
- `created_at` (string, required): Plan creation timestamp

**Validation Rules**:
- `plan_id` must be unique
- `approval_ref` must reference existing Approval Request
- `alternatives` must have at least 2 options
- `chosen_approach` must match one of the alternatives
- All required fields must be non-empty

**Relationships**:
- One Action Plan references one Approval Request
- Created before MCP execution (constitution requirement)

---

## Data Flow

```
1. Gmail API → Email detected
2. Gmail Watcher → Email Action Item created (Needs_Action/)
3. Gmail Watcher → Watcher State updated (processed_email_ids)
4. Human → Moves file to Pending_Approval/
5. Orchestrator → Creates Approval Request
6. Human → Moves file to Approved/ or Rejected/
7. Orchestrator → Creates Action Plan (if approved)
8. Orchestrator → Executes MCP action
9. Orchestrator → Creates Log Entry
10. Orchestrator → Moves file to Done/
```

## Storage Estimates

**Per Email Action Item**: ~2 KB (markdown file)
**Per Approval Request**: ~1 KB (markdown file)
**Per Log Entry**: ~500 bytes (JSON line)
**Per Watcher State**: ~10 KB (JSON file, grows with processed_email_ids)
**Per Action Plan**: ~3 KB (markdown file)

**Daily Volume (100 emails/day)**:
- Email Action Items: 200 KB
- Approval Requests: 50 KB (assuming 50% require approval)
- Log Entries: 50 KB
- Action Plans: 150 KB
- **Total**: ~450 KB/day

**90-Day Retention**: ~40 MB

## Archival Strategy

**After 90 days**:
- Move Email Action Items to `AI_Employee_Vault/Archive/YYYY-MM/`
- Compress log files: `Logs/YYYY-MM-DD.json.gz`
- Trim `processed_email_ids` in Watcher State (keep last 30 days only)
- Keep Approval Requests and Action Plans indefinitely (audit trail)
