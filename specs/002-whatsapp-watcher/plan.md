# Implementation Plan: WhatsApp Watcher (Sensor Layer)

**Branch**: `002-whatsapp-watcher` | **Date**: 2026-02-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-whatsapp-watcher/spec.md`

## Summary

Implement a production-grade, restart-safe WhatsApp Watcher that monitors WhatsApp Web for priority messages using Playwright browser automation. The watcher detects unread messages containing configurable keywords, creates structured action files in `/Needs_Action`, and maintains idempotent operation through persistent state tracking. This is a sensor-only component (no reasoning or action execution) that integrates with the existing approval workflow pipeline.

**Key Requirements**: Idempotent operation, 30-second polling, exponential backoff retry, session persistence, dry-run mode, graceful shutdown, JSON Lines logging.

## Technical Context

**Language/Version**: Python 3.13 (existing project standard)
**Primary Dependencies**:
- Playwright 1.40+ (browser automation for WhatsApp Web)
- watchdog 4.0+ (already in use for file monitoring)
- pyyaml 6.0+ (already in use for YAML parsing)
- python-dotenv 1.0+ (already in use for environment variables)

**Storage**: Local JSON state files in `AI_Employee_Vault/.state/whatsapp_watcher_state.json`
**Testing**: pytest (existing test framework), manual integration testing with real WhatsApp account
**Target Platform**: Linux/WSL (existing deployment environment)
**Project Type**: Single project (sensor component within existing watcher architecture)
**Performance Goals**:
- Polling interval: 30 seconds (configurable)
- Memory usage: <200MB RAM
- CPU usage: <5% average
- Detection latency: <60 seconds (2x polling interval)

**Constraints**:
- Read-only WhatsApp access (no message sending)
- Session persistence required (minimize QR code scans)
- Must handle 100+ unread message backlog
- Graceful handling of DOM changes, network failures, session expiration

**Scale/Scope**:
- Single WhatsApp account monitoring
- ~10-50 priority messages per day expected
- 24/7 continuous operation required
- Integration with existing Gmail watcher and approval workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with project constitution (`.specify/memory/constitution.md`):

- [x] **Local-First Architecture**: State persisted in `AI_Employee_Vault/.state/whatsapp_watcher_state.json`, action files in `/Needs_Action`
- [x] **Safety Before Autonomy**: Sensor-only design, no action execution capability, approval workflow integration
- [x] **File-Based State Transitions**: Action files created in `/Needs_Action` for human review and approval workflow
- [x] **Idempotent Watchers**: Processed message IDs tracked in state file, duplicate detection implemented
- [x] **Explicit Reasoning**: N/A (sensor layer only, no reasoning or MCP actions)
- [x] **Human Accountability**: All detected messages require human review via action files
- [x] **Auditability**: Logging to `/Logs/YYYY-MM-DD.json` with timestamp, sender, keyword matched
- [x] **Secrets Management**: Browser session in `.whatsapp_session/` (gitignored), no credentials in code
- [x] **Tier Isolation**: Silver Tier component in `watchers/` directory alongside Gmail watcher
- [x] **Error Handling**: Retry logic, session expiration detection, graceful degradation, alert creation

**Violations Requiring Justification**: None - design fully compliant with constitution.

**Post-Design Re-check**: ✅ All principles maintained in implementation design.

## Project Structure

### Documentation (this feature)

```text
specs/002-whatsapp-watcher/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (implementation plan)
├── research.md          # Technology research and decisions
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Setup and testing guide
├── contracts/           # Data schemas
│   └── whatsapp-action-file.schema.json
└── checklists/
    └── requirements.md  # Specification quality validation (complete)
```

### Source Code (repository root)

**Current Architecture** (as of 2026-02-25):

```text
watchers/
├── base_watcher.py           # Abstract base class for watchers (EXISTING)
├── gmail_watcher.py          # Gmail watcher implementation (EXISTING - reference pattern)
├── gmail_state.py            # State management utilities (EXISTING - reusable)
├── filesystem_watcher.py     # File system monitoring (EXISTING)
├── __init__.py               # Package initialization (EXISTING)
└── whatsapp_watcher.py       # WhatsApp watcher (TO BE IMPLEMENTED) ⚠️

scripts/
├── approval_executor.py      # Approval workflow executor (EXISTING)
├── orchestrator.py           # Main orchestration logic (EXISTING)
├── start_silver_tier.sh      # PM2 startup script (EXISTING - needs WhatsApp addition)
└── __init__.py               # Package initialization (EXISTING)

mcp_servers/
├── email_mcp_server.py       # Email MCP server (EXISTING)
├── email_client.py           # Email client wrapper (EXISTING)
└── __init__.py               # Package initialization (EXISTING)

AI_Employee_Vault/
├── .state/
│   ├── gmail_watcher_state.json     # Gmail state (EXISTING)
│   └── whatsapp_watcher_state.json  # WhatsApp state (TO BE CREATED)
├── Needs_Action/                    # Action files (EXISTING)
├── Pending_Approval/                # Pending approvals (EXISTING)
├── Approved/                        # Approved actions (EXISTING)
├── Done/                            # Completed actions (EXISTING)
├── Rejected/                        # Rejected actions (EXISTING)
├── .quarantine/                     # Invalid files (EXISTING)
└── Logs/
    └── YYYY-MM-DD.json              # JSON Lines logs (EXISTING)

.whatsapp_session/                   # Playwright browser context (TO BE CREATED, gitignored)

tests/
├── test_gmail_watcher.py            # Gmail watcher tests (EXISTING)
├── test_approval_executor.py        # Approval executor tests (EXISTING)
├── test_whatsapp_watcher.py         # WhatsApp watcher tests (TO BE IMPLEMENTED)
└── fixtures/
    └── mock_gmail_api.py            # Test fixtures (EXISTING)

Root level:
├── pyproject.toml                   # Dependencies (Playwright added)
├── credentials.json                 # OAuth credentials (EXISTING)
├── token.json                       # OAuth token (EXISTING)
├── .gitignore                       # Git ignore rules (needs .whatsapp_session/)
└── main.py                          # Entry point (EXISTING)
```

**Implementation Status**: WhatsApp Watcher does NOT exist yet. This is **new development**, not validation of existing code.

## Phase 0: Research & Technology Decisions

### Research Topics

1. **Playwright WhatsApp Web Automation**
   - Decision: Use Playwright with persistent browser context
   - Rationale: Industry standard for WhatsApp Web automation, supports session persistence, headless mode not supported by WhatsApp (must use headed mode)
   - Alternatives: Selenium (more complex), puppeteer (Node.js only), direct API (not available)

2. **Message Deduplication Strategy**
   - Decision: Composite message ID from sender + timestamp + message preview (first 50 chars)
   - Rationale: WhatsApp Web doesn't expose stable message IDs, composite key provides reliable uniqueness
   - Alternatives: Message hash (fragile to content changes), timestamp only (insufficient)

3. **DOM Selector Strategy**
   - Decision: Use data-testid attributes where available, fallback to class-based selectors with error handling
   - Rationale: data-testid more stable across WhatsApp updates, graceful degradation on selector failures
   - Alternatives: XPath (brittle), text content matching (language-dependent)

4. **Session Persistence**
   - Decision: Playwright persistent_context with local directory storage
   - Rationale: Maintains WhatsApp Web login across restarts, minimizes QR code scans
   - Alternatives: Manual cookie management (complex), fresh login each time (impractical)

5. **Retry and Backoff Logic**
   - Decision: Exponential backoff (1s, 2s, 4s) with max 3 retries per operation
   - Rationale: Balances responsiveness with rate limit avoidance, standard pattern from Gmail watcher
   - Alternatives: Fixed delay (less adaptive), immediate retry (risks rate limiting)

### Technology Stack Validation

- **Python 3.13**: ✅ Already in use, compatible with Playwright
- **Playwright 1.40+**: ✅ Added to pyproject.toml, requires `playwright install chromium`
- **State Management**: ✅ Reuse `gmail_state.py` utilities (GmailState class, create_log_entry, move_file_atomic)
- **Logging**: ✅ JSON Lines format consistent with Gmail watcher
- **Process Management**: ✅ PM2 for continuous operation (existing pattern)

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:
1. **WhatsAppMessage**: Detected unread message with sender, content, timestamp
2. **ActionFile**: Structured markdown file in /Needs_Action
3. **WatcherState**: Persistent state tracking processed messages
4. **PriorityKeyword**: Configurable keyword triggering detection

### API Contracts

See [contracts/whatsapp-action-file.schema.json](./contracts/whatsapp-action-file.schema.json) for JSON schema.

**Action File Format** (YAML frontmatter + Markdown):
```yaml
---
type: whatsapp_message
from: [sender_name]
received: [ISO 8601 timestamp]
priority: high
status: pending
original_timestamp: [WhatsApp timestamp]
---

## WhatsApp Message from [sender]

**Received**: [timestamp]

### Message Content

[message_text]

### Suggested Actions

- [ ] Reply to [sender]
- [ ] Forward to relevant party
- [ ] Create task or reminder
- [ ] Archive after processing
```

### Integration Points

1. **With Gmail Watcher**: Shared state management utilities, consistent logging format
2. **With Approval Workflow**: Action files compatible with existing `/Needs_Action` pipeline
3. **With Orchestrator**: File-based communication, no direct coupling

### Quickstart Guide

See [quickstart.md](./quickstart.md) for setup instructions.

**Key Steps**:
1. Install Playwright browsers: `uv run playwright install chromium`
2. Run watcher: `uv run python watchers/whatsapp_watcher.py`
3. Scan QR code on first run (session persists)
4. Send test message with "urgent" keyword
5. Verify action file created in `/Needs_Action`

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  WHATSAPP WATCHER ARCHITECTURE               │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  WhatsApp Web    │  (External)
│  (Browser)       │
└────────┬─────────┘
         │
         │ Playwright automation
         ▼
┌─────────────────────────────────────────────────────────────┐
│  WhatsAppWatcher Class                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Initialization                                         │ │
│  │  - Load config (keywords, polling interval)            │ │
│  │  - Initialize state (load processed IDs)               │ │
│  │  - Setup browser context (persistent session)          │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Main Loop (run_once)                                  │ │
│  │  1. Launch browser with persistent context            │ │
│  │  2. Navigate to WhatsApp Web                           │ │
│  │  3. Wait for login (QR code if needed)                 │ │
│  │  4. Scan unread chats                                  │ │
│  │  5. Filter by priority keywords                        │ │
│  │  6. Check against processed IDs (deduplication)        │ │
│  │  7. Create action files for new priority messages     │ │
│  │  8. Update state and save                              │ │
│  │  9. Close browser                                       │ │
│  │  10. Sleep for polling interval                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Error Handling                                         │ │
│  │  - Retry with exponential backoff (1s, 2s, 4s)        │ │
│  │  - Session expiration detection                        │ │
│  │  - DOM selector fallbacks                              │ │
│  │  - Graceful shutdown (SIGTERM/SIGINT)                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         │ File writes
         ▼
┌─────────────────────────────────────────────────────────────┐
│  AI_Employee_Vault/                                          │
│  ├── .state/whatsapp_watcher_state.json                     │
│  ├── Needs_Action/WHATSAPP_*.md                             │
│  └── Logs/YYYY-MM-DD.json                                   │
└─────────────────────────────────────────────────────────────┘
```

### State Machine

```
[Startup] → [Load State] → [Launch Browser]
                              │
                              ▼
                         [Check Login]
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            [QR Code Scan]      [Already Logged In]
                    │                   │
                    └─────────┬─────────┘
                              ▼
                      [Scan Unread Chats]
                              │
                              ▼
                    [Filter by Keywords]
                              │
                              ▼
                    [Check Processed IDs]
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            [New Priority Msg]    [Already Processed]
                    │                   │
                    ▼                   │
          [Create Action File]          │
                    │                   │
                    ▼                   │
            [Update State]              │
                    │                   │
                    └─────────┬─────────┘
                              ▼
                        [Save State]
                              │
                              ▼
                      [Close Browser]
                              │
                              ▼
                    [Sleep (30s default)]
                              │
                              └──────┐
                                     │
                    ┌────────────────┘
                    ▼
              [Repeat Loop]
```

### Error Handling Strategy

1. **Network Timeout**: Retry with exponential backoff, log warning after 3 failures
2. **Session Expired**: Detect login screen, create alert in /Needs_Action, wait for manual re-auth
3. **DOM Selector Failure**: Log detailed error with failing selector, continue operation, create alert
4. **State File Corruption**: Initialize fresh state, log warning, continue operation
5. **Rate Limiting**: Increase polling interval temporarily, log warning
6. **Graceful Shutdown**: Save state on SIGTERM/SIGINT, close browser cleanly

## Implementation Approach

### Development Strategy

**Status**: WhatsApp Watcher needs to be **implemented from scratch** following the existing watcher pattern.

**Reference Implementation**: `watchers/gmail_watcher.py` provides the architectural pattern to follow:
- Inherits from `BaseWatcher` abstract class (optional, but recommended for consistency)
- Reuses `GmailState` class pattern for state management (adapt for WhatsApp message ID format)
- Implements idempotent operation with processed ID tracking
- Creates structured action files with YAML frontmatter
- JSON Lines logging to `/Logs/YYYY-MM-DD.json`
- Graceful error handling and retry logic

**Key Implementation Tasks**:
1. **Create WhatsAppWatcher class** in `watchers/whatsapp_watcher.py`
   - Initialize Playwright with persistent browser context
   - Configure priority keywords (default: urgent, asap, important, help, invoice, payment, emergency, critical, deadline)
   - Load/save state from `AI_Employee_Vault/.state/whatsapp_watcher_state.json`

2. **Implement core detection logic**:
   - Launch browser and navigate to WhatsApp Web
   - Wait for login (QR code on first run, session persistence thereafter)
   - Scan unread chats using DOM selectors (data-testid preferred, class fallback)
   - Extract sender name, message text, timestamp
   - Generate composite message ID (sender + timestamp + preview)
   - Filter by priority keywords (case-insensitive)
   - Check against processed IDs (deduplication)

3. **Implement action file creation**:
   - Generate filename: `WHATSAPP_{YYYYMMDD}_{HHMMSS}_{sanitized_sender}.md`
   - Create YAML frontmatter with required fields (type, from, received, priority, status, original_timestamp)
   - Format message content in markdown
   - Write to `/Needs_Action` atomically

4. **Implement state management**:
   - Reuse `GmailState` class pattern (adapt for WhatsApp message IDs)
   - Track processed message IDs in JSON file
   - Persist session status (active/expired)
   - Handle state file corruption gracefully

5. **Implement error handling**:
   - Exponential backoff retry (1s, 2s, 4s) for transient failures
   - Session expiration detection and alert creation
   - DOM selector fallbacks with detailed error logging
   - Graceful shutdown on SIGTERM/SIGINT

6. **Add logging**:
   - JSON Lines format consistent with Gmail watcher
   - Log detection events, errors, state changes
   - Include timestamp, action_type, status, inputs, outputs

**Code Reuse Opportunities**:
- `watchers/gmail_state.py`: State management utilities (GmailState class, create_log_entry, move_file_atomic)
- `watchers/base_watcher.py`: Abstract base class (optional inheritance)
- `scripts/approval_executor.py`: Action file format validation (reference for schema compliance)

## Testing Strategy

### Unit Tests
- Keyword matching logic
- Message ID generation
- State persistence and recovery
- Action file formatting

### Integration Tests
- End-to-end: Send WhatsApp message → Verify action file created
- Idempotency: Restart watcher → Verify no duplicates
- Session persistence: Restart → Verify no QR code required
- Error recovery: Simulate network failure → Verify retry and recovery

### Manual Testing
1. First-time setup (QR code scan)
2. Priority message detection
3. Non-priority message filtering
4. Restart without duplicates
5. 24-hour stability test
6. Large backlog processing (50+ messages)

## Deployment

### Prerequisites
- Python 3.13 with uv package manager
- Playwright browsers installed (`uv run playwright install chromium`)
- WhatsApp account with access to WhatsApp Web
- Stable internet connection

### Startup
```bash
# Manual (for testing)
uv run python watchers/whatsapp_watcher.py

# PM2 (production)
pm2 start watchers/whatsapp_watcher.py --name whatsapp-watcher --interpreter python3
pm2 save
```

### Monitoring
- Check logs: `tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`
- Check PM2 status: `pm2 status whatsapp-watcher`
- Check action files: `ls -lh AI_Employee_Vault/Needs_Action/WHATSAPP_*`

## Risks & Mitigations

1. **WhatsApp ToS Violation**
   - Risk: Automated access may violate terms of service
   - Mitigation: Personal use only, low frequency polling, educational purpose

2. **DOM Changes**
   - Risk: WhatsApp Web UI updates break selectors
   - Mitigation: Robust error handling, fallback selectors, alert creation

3. **Session Expiration**
   - Risk: Frequent re-authentication required
   - Mitigation: Persistent session, alert system, manual re-auth workflow

4. **Rate Limiting**
   - Risk: Excessive polling triggers temporary blocks
   - Mitigation: Configurable intervals, backoff logic, monitoring

5. **False Positives**
   - Risk: Keyword matching triggers on non-urgent messages
   - Mitigation: Configurable keywords, human review via approval workflow

## Success Metrics

- **Detection Latency**: Target <60 seconds (2x polling interval)
- **Idempotency**: Target 0 duplicates across restarts
- **Uptime**: Target 24 hours continuous operation
- **Recovery Rate**: Target 95% automatic recovery from transient failures
- **Resource Usage**: Target <200MB RAM, <5% CPU

## Next Steps

1. ✅ Specification complete (spec.md)
2. ✅ Implementation plan complete (this file)
3. ✅ Architecture analysis complete (plan updated with actual project structure)
4. ⏭️ Run `/sp.tasks` to generate task breakdown for implementation
5. ⏭️ **Implement WhatsAppWatcher class** in `watchers/whatsapp_watcher.py` (new file)
6. ⏭️ Install Playwright browsers: `uv run playwright install chromium`
7. ⏭️ Create unit tests in `tests/test_whatsapp_watcher.py`
8. ⏭️ Manual testing with real WhatsApp account (QR code authentication)
9. ⏭️ Integration testing (end-to-end workflow validation)
10. ⏭️ 24-hour stability test
11. ⏭️ Update `.gitignore` to exclude `.whatsapp_session/`
12. ⏭️ Update `scripts/start_silver_tier.sh` to include WhatsApp watcher in PM2
13. ⏭️ Documentation and deployment guide
