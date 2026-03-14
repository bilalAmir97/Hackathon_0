# Feature Specification: Gmail Watcher + Approval Workflow

**Feature Branch**: `001-gmail-approval-workflow`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "Silver Tier – Gmail Watcher + Human-in-the-Loop Approval Workflow"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Email Detection and Action Creation (Priority: P1)

As a business owner, I want the system to automatically detect important incoming emails and create structured action items in my workspace, so I can review and respond to critical communications without manually checking my inbox.

**Why this priority**: This is the foundation of the automation pipeline. Without reliable email detection and action creation, no other workflow can function. This delivers immediate value by surfacing important emails that require attention.

**Independent Test**: Send a test email with priority keywords (e.g., "urgent client request") to the monitored Gmail account. Verify that a structured action file appears in the Needs_Action folder within the configured polling interval (default 2 minutes). The file should contain email metadata, preview, and suggested actions.

**Acceptance Scenarios**:

1. **Given** the system is monitoring an inbox with 3 unread emails (2 routine, 1 marked urgent), **When** the watcher completes a polling cycle, **Then** exactly 1 action file is created in Needs_Action folder for the urgent email only
2. **Given** an action file already exists for email ID "abc123", **When** the system restarts and polls the same inbox, **Then** no duplicate action file is created for email ID "abc123"
3. **Given** the Gmail OAuth token has expired, **When** the watcher attempts to poll, **Then** the system pauses polling, creates an alert in Needs_Action, and waits for token refresh without crashing
4. **Given** 5 new important emails arrive simultaneously, **When** the watcher polls, **Then** 5 separate action files are created with unique identifiers and timestamps
5. **Given** the system has been offline for 2 hours, **When** it comes back online and polls, **Then** all important emails received during downtime are detected and action files created without duplicates

---

### User Story 2 - Human Approval Workflow (Priority: P2)

As a business owner, I want all sensitive actions (like sending emails or making payments) to require my explicit approval before execution, so I maintain control over critical business communications and prevent automated mistakes.

**Why this priority**: Safety is paramount for autonomous systems. This story implements the human-in-the-loop safeguard that prevents the system from taking irreversible actions without oversight. It's the second priority because it must exist before any action execution capability.

**Independent Test**: Create a draft email response action file in Needs_Action. Move it to Pending_Approval folder. Verify the system detects it and waits for human decision. Move to Approved folder and verify execution is triggered. Alternatively, move to Rejected folder and verify no execution occurs and file moves to Done.

**Acceptance Scenarios**:

1. **Given** an email draft action file in Needs_Action, **When** I move it to Pending_Approval, **Then** the system recognizes it as awaiting approval and does not execute any action
2. **Given** an approval request in Pending_Approval folder, **When** I move it to Approved, **Then** the system executes the requested action within 30 seconds and logs the execution
3. **Given** an approval request in Pending_Approval folder, **When** I move it to Rejected, **Then** the system skips execution, moves the file to Done, and logs the rejection
4. **Given** an approval file with corrupted or missing required fields, **When** the system attempts to process it, **Then** an error is logged, the file is moved to a quarantine location, and an alert is created
5. **Given** multiple approval requests in Approved folder, **When** the system processes them, **Then** each is executed in order, with individual success/failure logging for each action

---

### User Story 3 - Action Execution and Logging (Priority: P3)

As a business owner, I want approved actions to be executed automatically and all activities logged with complete audit trails, so I can verify what the system did and troubleshoot any issues.

**Why this priority**: This completes the automation loop by actually performing approved actions. It's third priority because it depends on both detection (P1) and approval (P2) being functional. The audit trail ensures accountability and debugging capability.

**Independent Test**: Create an approved email send action. Verify the email is sent via the configured email service. Check that a log entry exists in Logs/YYYY-MM-DD.json with timestamp, action type, inputs, outputs, and approval reference. Verify the action file moves to Done folder after successful execution.

**Acceptance Scenarios**:

1. **Given** an approved email send action, **When** execution completes successfully, **Then** the email is sent, a log entry is created with all required fields, and the action file moves to Done
2. **Given** an approved action that fails due to network timeout, **When** the system retries (max 3 attempts with exponential backoff), **Then** each retry is logged and if all fail, an error alert is created in Needs_Action
3. **Given** the system crashes during action execution, **When** it restarts, **Then** it detects the incomplete action (file still in Approved), resumes execution, and prevents duplicate execution
4. **Given** 10 approved actions in queue, **When** Gmail API rate limit is hit on action 3, **Then** the system pauses, waits with exponential backoff, and resumes processing remaining actions without data loss
5. **Given** an action completes successfully, **When** I review the log file, **Then** I can see timestamp, action type, email ID, approval file reference, execution status, and any error messages

---

### User Story 4 - System Resilience and Recovery (Priority: P4)

As a business owner, I want the system to handle errors gracefully and recover from failures without losing data or creating duplicates, so I can run it continuously without manual intervention.

**Why this priority**: This ensures production-grade reliability for 24/7 operation. While lower priority than core functionality, it's essential for real-world deployment. It can be tested independently by simulating various failure scenarios.

**Independent Test**: Simulate network outage during polling. Verify system queues operations locally and resumes when connection restored. Simulate orchestrator crash mid-execution. Verify system recovers on restart without duplicate actions or data loss.

**Acceptance Scenarios**:

1. **Given** the system is polling Gmail, **When** network connection is lost, **Then** polling pauses, operations queue locally, and resume automatically when connection restored
2. **Given** the system has processed 100 emails, **When** it restarts, **Then** it resumes from last known state without reprocessing any emails or creating duplicates
3. **Given** an OAuth token expires during operation, **When** the system detects expiration, **Then** it pauses operations, creates a human alert, and resumes after token refresh without data loss
4. **Given** the vault folder structure is corrupted (missing Approved folder), **When** the system starts, **Then** it recreates required folders, logs the recovery action, and continues operation
5. **Given** the system encounters 3 consecutive API failures, **When** max retries are exhausted, **Then** it creates a detailed error report in Needs_Action, pauses that specific operation, but continues processing other actions

---

### Edge Cases

- **Expired OAuth Token**: System detects token expiration before API call, pauses operations, creates alert in Needs_Action requesting token refresh, resumes automatically after refresh
- **Gmail API Rate Limits**: System implements exponential backoff (1s, 2s, 4s delays) with max 3 retries, logs rate limit events, queues operations if limit persists
- **Network Outage**: System detects connection failure, queues pending operations in local state file, retries with exponential backoff, resumes when connection restored
- **Duplicate Message Detection**: System maintains persistent state file with processed email IDs, checks against this list before creating action files, survives restarts
- **Partial MCP Failure**: If email send fails after approval, system logs failure with full context, creates retry action in Needs_Action, does not mark original as complete
- **Corrupted Approval File**: System validates approval file structure before execution, quarantines malformed files, creates error alert with details for human review
- **Orchestrator Crash During Execution**: System uses atomic file operations, checks for incomplete actions on restart (files in Approved folder), resumes or retries based on log state
- **Email Already Processed But File Missing**: System relies on persistent state file (not file existence) to track processed emails, prevents re-creation even if action file was manually deleted
- **Vault Folder Structure Missing**: System validates required folders on startup (Inbox, Needs_Action, Pending_Approval, Approved, Rejected, Done, Plans, Logs), creates missing folders, logs recovery
- **Concurrent File Access**: System uses file locking or atomic rename operations to prevent race conditions when moving files between folders
- **Large Email Attachments**: System stores only email metadata and preview in action files, provides link to full email in Gmail, avoids vault bloat
- **Time Zone Handling**: All timestamps use ISO 8601 format with UTC timezone, log files named by UTC date for consistency

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST poll the configured Gmail inbox at a configurable interval (default 120 seconds) for unread emails
- **FR-002**: System MUST identify important emails based on configurable priority keywords (urgent, important, invoice, payment, client, deadline, etc.)
- **FR-003**: System MUST create a structured action file in Needs_Action folder for each important email detected
- **FR-004**: System MUST prevent duplicate action files for the same email ID, even after system restarts
- **FR-005**: System MUST maintain persistent state tracking all processed email IDs across restarts
- **FR-006**: System MUST support file-based state transitions: Needs_Action → Pending_Approval → Approved/Rejected → Done
- **FR-007**: System MUST detect when action files are moved between folders and trigger appropriate workflow transitions
- **FR-008**: System MUST execute approved actions only after explicit human approval (file moved to Approved folder)
- **FR-009**: System MUST skip execution for rejected actions (file moved to Rejected folder) and move directly to Done
- **FR-010**: System MUST log all actions to daily log files (Logs/YYYY-MM-DD.json) with complete audit trail
- **FR-011**: System MUST support dry-run mode where actions are simulated but not executed (for testing and development)
- **FR-012**: System MUST implement retry logic with exponential backoff (max 3 attempts) for transient failures
- **FR-013**: System MUST validate approval file structure before execution and quarantine malformed files
- **FR-014**: System MUST recover gracefully from crashes by resuming incomplete operations on restart
- **FR-015**: System MUST create human-readable error alerts in Needs_Action folder when intervention is required

### Security & Approval Requirements

- **SR-001**: System MUST require human approval for all email sending actions (no automatic execution)
- **SR-002**: System MUST log all email send actions to `/Logs/YYYY-MM-DD.json` with timestamp, email ID, recipient, subject, approval reference, and execution status
- **SR-003**: System MUST store Gmail OAuth credentials only in environment variables (never in vault files or code)
- **SR-004**: System MUST implement idempotent email watcher with persistent state tracking to prevent duplicate action creation
- **SR-005**: System MUST create Plan.md in Plans folder before executing any external action (email send, API call)
- **SR-006**: System MUST refresh expired OAuth tokens automatically and pause operations if refresh fails
- **SR-007**: System MUST validate that approval files reference valid action items before execution
- **SR-008**: System MUST prevent approval file tampering by validating file integrity (checksums or signatures)
- **SR-009**: System MUST maintain minimum 90-day retention for all log files
- **SR-010**: System MUST use atomic file operations to prevent race conditions during state transitions

### Key Entities

- **Email Action Item**: Represents a detected important email requiring human review. Contains email metadata (ID, from, to, subject, date), preview snippet, priority indicators, suggested actions, and workflow state
- **Approval Request**: Represents a pending decision on a sensitive action. Contains action type, parameters, risk assessment, approval status, and references to original email action
- **Log Entry**: Represents a completed action or system event. Contains timestamp, action type, inputs, outputs, approval reference, execution status, error details, and retry count
- **Watcher State**: Represents the persistent state of the Gmail watcher. Contains last poll timestamp, processed email IDs set, error count, and configuration parameters
- **Action Plan**: Represents the reasoning and strategy for executing an action. Contains problem analysis, alternatives considered, chosen approach, expected outcomes, and risk mitigation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: New important emails are detected and action files created within 2 minutes of arrival (default polling interval)
- **SC-002**: Zero duplicate action files created for the same email, even after 10 system restarts
- **SC-003**: 100% of sensitive actions (email sends) require explicit human approval before execution
- **SC-004**: All executed actions have corresponding log entries with complete audit trail (timestamp, inputs, outputs, approval reference)
- **SC-005**: System recovers from transient errors (network outage, API rate limits) within 3 retry attempts without data loss
- **SC-006**: System resumes operation within 30 seconds of restart, continuing from last known state
- **SC-007**: Approval workflow completes within 30 seconds of file movement to Approved folder
- **SC-008**: System operates continuously for 7 days without manual intervention (excluding approval decisions)
- **SC-009**: All edge cases (token expiration, rate limits, crashes) result in graceful degradation with human alerts, not system failure
- **SC-010**: End-to-end workflow (email arrival → detection → approval → execution → logging) is reproducible from vault state alone

### Assumptions

- Gmail API access is available with appropriate OAuth scopes (gmail.readonly, gmail.send)
- File system supports atomic rename operations for state transitions
- Polling interval of 120 seconds is acceptable latency for email detection (not real-time)
- Human approval decisions occur within reasonable timeframe (hours, not days)
- Vault storage has sufficient capacity for action files and logs (estimated 1MB per 100 emails)
- System runs on environment with persistent storage (not ephemeral containers)
- Email priority keywords are configurable and cover 80% of important emails
- MCP server for email sending is available and properly configured
- Network connectivity is generally reliable (transient failures, not permanent offline)
- Single user/business owner scenario (no multi-user approval workflows)
