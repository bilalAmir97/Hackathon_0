# Implementation Plan: Gmail Watcher + Approval Workflow

**Branch**: `001-gmail-approval-workflow` | **Date**: 2026-02-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-gmail-approval-workflow/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a production-grade, local-first Gmail Watcher with Human-in-the-Loop approval workflow for Silver Tier AI Employee. The system follows Perception → Reasoning → Approval → Action → Done pipeline, using file-based state transitions in Obsidian vault. Gmail Watcher polls for important emails (idempotent, restart-safe), creates action files in vault, and Orchestrator executes approved actions via MCP with complete audit logging.

**Key Technical Approach**:
- Python-based Gmail Watcher with persistent state tracking (processed email IDs)
- File-based state machine using vault folders (Needs_Action → Pending_Approval → Approved/Rejected → Done)
- Watchdog library for monitoring folder transitions
- OAuth 2.0 with automatic token refresh
- Exponential backoff retry logic (max 3 attempts)
- Structured JSON logging to /Logs/YYYY-MM-DD.json
- Dry-run mode for safe testing

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**:
- google-auth-oauthlib (OAuth 2.0 flow)
- google-auth (credential management)
- google-api-python-client (Gmail API)
- watchdog (file system monitoring)
- python-dotenv (environment variables)

**Storage**: File-based (Obsidian vault structure in AI_Employee_Vault/)
**Testing**: pytest with fixtures for Gmail API mocking, file system operations
**Target Platform**: Linux/WSL (current environment), compatible with macOS/Windows
**Project Type**: Single project (watchers + orchestrator in root)
**Performance Goals**:
- Email detection within 2 minutes (120s polling interval)
- Approval execution within 30 seconds of file movement
- Support 100+ emails/day without performance degradation

**Constraints**:
- Gmail API quota: 250 quota units/user/second, 1 billion quota units/day
- File operations must be atomic (prevent race conditions)
- Polling interval minimum 60s (avoid excessive API calls)
- Log file size management (rotate daily, compress after 7 days)

**Scale/Scope**:
- Single user/business owner
- 1-2 Gmail accounts monitored
- 50-100 emails/day processed
- 90-day log retention (estimated 50MB storage)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with project constitution (`.specify/memory/constitution.md`):

- [x] **Local-First Architecture**: All state persisted in vault files (processed_ids.json, action files, logs), no external databases
- [x] **Safety Before Autonomy**: Approval workflow designed before action execution capability (Pending_Approval → Approved gate)
- [x] **File-Based State Transitions**: State changes via file movements between vault directories (Needs_Action → Pending_Approval → Approved → Done)
- [x] **Idempotent Watchers**: Duplicate detection via persistent processed_ids.json with email ID tracking
- [x] **Explicit Reasoning**: Plan.md creation before MCP action invocation (orchestrator requirement)
- [x] **Human Accountability**: Approval boundaries enforced programmatically (no auto-approve, file movement required)
- [x] **Auditability**: Logging to `/Logs/YYYY-MM-DD.json` with timestamp, action_type, email_id, approval_ref, status, error_details
- [x] **Secrets Management**: OAuth credentials in .env only (GMAIL_CREDENTIALS_PATH, token.json path)
- [x] **Tier Isolation**: Code organized in watchers/ (Silver tier), separate from Bronze tier filesystem_watcher
- [x] **Error Handling**: Graceful handling of token expiration (auto-refresh), rate limits (exponential backoff), network outages (queue + retry), crashes (resume from state)

**Violations Requiring Justification**: None - all constitution principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-gmail-approval-workflow/
├── plan.md              # This file (/sp.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (technical decisions)
├── data-model.md        # Phase 1 output (entity schemas)
├── quickstart.md        # Phase 1 output (setup guide)
├── contracts/           # Phase 1 output (file format schemas)
│   ├── email-action.schema.json
│   ├── approval-request.schema.json
│   └── log-entry.schema.json
└── checklists/
    └── requirements.md  # Spec validation checklist
```

### Source Code (repository root)

```text
watchers/
├── __init__.py
├── base_watcher.py           # Existing base class (Bronze tier)
├── filesystem_watcher.py     # Existing (Bronze tier)
├── gmail_watcher.py          # NEW: Gmail polling + action creation
└── gmail_state.py            # NEW: Persistent state management

scripts/
├── orchestrator.py           # EXISTING: Needs enhancement for approval workflow
└── approval_executor.py      # NEW: Monitors folders, executes approved actions

AI_Employee_Vault/
├── Inbox/                    # Existing
├── Needs_Action/             # Existing - Gmail watcher writes here
├── Pending_Approval/         # Existing - Human moves files here
├── Approved/                 # Existing - Human approves here
├── Rejected/                 # Existing - Human rejects here
├── Done/                     # Existing - Completed actions
├── Plans/                    # Existing - Reasoning artifacts
└── Logs/                     # Existing - Audit trail
    └── YYYY-MM-DD.json

tests/
├── test_gmail_watcher.py     # NEW: Unit tests for Gmail watcher
├── test_gmail_state.py       # NEW: State management tests
├── test_approval_executor.py # NEW: Approval workflow tests
└── fixtures/
    ├── mock_gmail_api.py     # NEW: Gmail API mocks
    └── sample_emails.json    # NEW: Test email data

.env                          # OAuth credentials, config
token.json                    # Gmail OAuth token (gitignored)
credentials.json              # Gmail API credentials (gitignored)
```

**Structure Decision**: Single project structure chosen because:
- Watchers and orchestrator are tightly coupled (shared vault access)
- No frontend/backend separation needed (file-based UI via Obsidian)
- Simplifies deployment and testing
- Aligns with existing Bronze tier structure

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - constitution fully satisfied.

## Phase 0: Research & Technical Decisions

### Research Questions

1. **Gmail API Best Practices**
   - Decision: Use `users().messages().list()` with `q='is:unread'` query
   - Rationale: More efficient than fetching all messages and filtering locally
   - Alternatives: Pub/Sub notifications (rejected - adds complexity, requires external service)

2. **Idempotency Strategy**
   - Decision: Persistent JSON file with set of processed email IDs
   - Rationale: Simple, survives restarts, human-readable for debugging
   - Alternatives: SQLite database (rejected - violates local-first simplicity), in-memory (rejected - lost on restart)

3. **File Monitoring Approach**
   - Decision: Watchdog library with Observer pattern
   - Rationale: Cross-platform, event-driven (efficient), well-maintained
   - Alternatives: Polling folders (rejected - inefficient), inotify (rejected - Linux-only)

4. **OAuth Token Refresh**
   - Decision: Check token expiry before each API call, auto-refresh if needed
   - Rationale: Prevents mid-operation failures, transparent to user
   - Alternatives: Refresh on failure (rejected - causes unnecessary errors), manual refresh (rejected - violates autonomy)

5. **Retry Strategy**
   - Decision: Exponential backoff with jitter (1s, 2s, 4s + random 0-1s)
   - Rationale: Industry standard, prevents thundering herd, respects rate limits
   - Alternatives: Fixed delay (rejected - doesn't adapt to load), immediate retry (rejected - wastes quota)

6. **Log Format**
   - Decision: JSON Lines format (one JSON object per line)
   - Rationale: Append-only (atomic), easy to parse, supports streaming
   - Alternatives: Single JSON array (rejected - requires rewriting entire file), CSV (rejected - poor for nested data)

7. **Dry-Run Mode**
   - Decision: Environment variable `DRY_RUN=true` skips MCP execution, logs intent
   - Rationale: Safe testing, preserves workflow logic, easy to toggle
   - Alternatives: Separate code paths (rejected - maintenance burden), mock MCP (rejected - doesn't test real integration)

### Technology Stack Justification

**Python 3.10+**:
- Already used in project (Bronze tier)
- Excellent Gmail API support (official google-api-python-client)
- Rich ecosystem for file operations, JSON handling
- Type hints for better code quality

**google-auth-oauthlib**:
- Official Google library for OAuth 2.0
- Handles token refresh automatically
- Well-documented, actively maintained

**watchdog**:
- Cross-platform file system monitoring
- Event-driven (efficient for approval workflow)
- Supports recursive directory watching

**pytest**:
- Already used in project
- Excellent fixture support for mocking Gmail API
- Parametrized tests for edge cases

## Phase 1: Data Model & Contracts

### Entity Schemas

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:
1. **Email Action Item** - Detected important email requiring review
2. **Approval Request** - Pending decision on sensitive action
3. **Log Entry** - Completed action or system event
4. **Watcher State** - Persistent Gmail watcher state
5. **Action Plan** - Reasoning artifact for MCP execution

### API Contracts

See [contracts/](./contracts/) for JSON schemas.

**File Format Contracts**:
- `email-action.schema.json` - Structure for action files in Needs_Action/
- `approval-request.schema.json` - Structure for approval files in Pending_Approval/
- `log-entry.schema.json` - Structure for log entries in Logs/

### Quickstart Guide

See [quickstart.md](./quickstart.md) for setup instructions.

**Setup Steps**:
1. Gmail API credentials setup (Google Cloud Console)
2. OAuth token generation
3. Environment configuration (.env)
4. Vault structure validation
5. Watcher startup
6. Approval workflow testing

## Implementation Phases

### Phase 2: Core Implementation (via /sp.tasks)

**User Story 1: Email Detection (P1)**
- Gmail watcher with OAuth authentication
- Priority keyword detection
- Action file creation in Needs_Action/
- Persistent state management (processed_ids.json)
- Idempotency guarantees

**User Story 2: Approval Workflow (P2)**
- Folder monitoring with watchdog
- Approval file validation
- State transition logic (Pending → Approved/Rejected → Done)
- Error handling for corrupted files

**User Story 3: Action Execution (P3)**
- MCP integration for email sending
- Structured logging to Logs/YYYY-MM-DD.json
- Retry logic with exponential backoff
- Crash recovery (resume incomplete actions)

**User Story 4: System Resilience (P4)**
- Token expiration handling
- Rate limit detection and backoff
- Network outage recovery
- Vault structure validation on startup

### Testing Strategy

**Unit Tests**:
- Gmail watcher: API mocking, keyword detection, file creation
- State management: Idempotency, persistence, corruption recovery
- Approval executor: File validation, state transitions, logging

**Integration Tests**:
- End-to-end: Email → Needs_Action → Approved → MCP → Done
- Restart scenarios: State persistence, duplicate prevention
- Error scenarios: Token expiry, rate limits, network failures

**Manual Testing**:
- OAuth flow (first-time setup)
- Approval workflow (file movements in Obsidian)
- Log inspection (audit trail verification)

## Risk Analysis

**High Risk**:
- Gmail API quota exhaustion (mitigation: configurable polling interval, quota monitoring)
- OAuth token corruption (mitigation: automatic regeneration prompt, backup token)
- Race conditions in file operations (mitigation: atomic renames, file locking)

**Medium Risk**:
- Large email volume overwhelming vault (mitigation: archive old action files, log rotation)
- Network instability causing missed emails (mitigation: backfill on reconnect, alert on gaps)
- Approval file tampering (mitigation: checksum validation, immutable logs)

**Low Risk**:
- Keyword false positives (mitigation: configurable keywords, manual review)
- Time zone confusion (mitigation: UTC everywhere, ISO 8601 format)
- Disk space exhaustion (mitigation: log rotation, vault size monitoring)

## Success Metrics

**Functional**:
- Zero duplicate action files for same email ID (measured via state file audit)
- 100% approval requirement for email sends (measured via log analysis)
- <2 minute email detection latency (measured via timestamp comparison)

**Reliability**:
- 99% uptime over 7-day test period (excluding approval wait time)
- <3 retries for 95% of transient errors (measured via log analysis)
- Zero data loss on crash (measured via state file recovery tests)

**Auditability**:
- 100% of actions have log entries (measured via log completeness check)
- All log entries have required fields (measured via schema validation)
- 90-day log retention verified (measured via file age audit)

## Next Steps

1. Run `/sp.tasks` to generate actionable task list from this plan
2. Implement Phase 2 tasks in priority order (P1 → P2 → P3 → P4)
3. Create ADR for significant decisions (OAuth strategy, state management approach)
4. Update agent context with new technologies (watchdog, gmail API patterns)
