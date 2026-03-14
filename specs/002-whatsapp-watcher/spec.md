# Feature Specification: WhatsApp Watcher (Sensor Layer)

**Feature Branch**: `002-whatsapp-watcher`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "Production-grade WhatsApp Watcher for monitoring WhatsApp Web messages with keyword filtering, persistent session management, and idempotent operation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Priority Message Detection (Priority: P1)

As a business owner, I need the system to automatically detect important WhatsApp messages so I can respond to urgent client requests without constantly checking my phone.

**Why this priority**: This is the core value proposition - automated monitoring of WhatsApp for business-critical messages. Without this, the feature provides no value.

**Independent Test**: Can be fully tested by sending a WhatsApp message containing a priority keyword (e.g., "urgent") and verifying that a structured action file appears in the /Needs_Action folder within the polling interval.

**Acceptance Scenarios**:

1. **Given** WhatsApp Web is logged in and watcher is running, **When** a new unread message arrives containing the keyword "urgent", **Then** a structured markdown file is created in /Needs_Action within 60 seconds
2. **Given** WhatsApp Web is logged in and watcher is running, **When** a new unread message arrives without any priority keywords, **Then** no action file is created
3. **Given** multiple unread messages exist, **When** watcher performs a check cycle, **Then** only messages containing priority keywords generate action files
4. **Given** a priority message is detected, **When** the action file is created, **Then** it contains the sender name, message content, timestamp, and suggested actions

---

### User Story 2 - Restart-Safe Operation (Priority: P2)

As a system operator, I need the watcher to remember which messages it has already processed so that restarting the service doesn't create duplicate action files for the same messages.

**Why this priority**: Without idempotent operation, every restart would flood the /Needs_Action folder with duplicates, making the system unusable in production.

**Independent Test**: Can be tested by processing a priority message, restarting the watcher, and verifying that no duplicate action file is created for the same message.

**Acceptance Scenarios**:

1. **Given** a priority message has been processed and an action file created, **When** the watcher is restarted, **Then** the same message does not generate a duplicate action file
2. **Given** the watcher has processed 10 messages, **When** the watcher crashes and restarts, **Then** only new unread messages generate action files
3. **Given** the state file is corrupted, **When** the watcher starts, **Then** it initializes a new state file and logs a warning without crashing
4. **Given** a large backlog of 50 unread messages exists, **When** the watcher starts for the first time, **Then** it processes all priority messages exactly once

---

### User Story 3 - Automatic Failure Recovery (Priority: P3)

As a system operator, I need the watcher to automatically recover from temporary network issues or WhatsApp Web glitches so that monitoring continues without manual intervention.

**Why this priority**: Production systems must handle transient failures gracefully. Manual restarts for every network hiccup would make the system impractical.

**Independent Test**: Can be tested by simulating network interruption during a check cycle and verifying that the watcher retries and eventually succeeds without crashing.

**Acceptance Scenarios**:

1. **Given** the watcher is running, **When** a network timeout occurs during page load, **Then** the watcher retries up to 3 times with exponential backoff before logging an error
2. **Given** WhatsApp Web returns a temporary error, **When** the watcher encounters the error, **Then** it waits and retries without crashing
3. **Given** the WhatsApp Web session expires, **When** the watcher detects the expired session, **Then** it logs an alert to /Needs_Action requesting manual re-authentication
4. **Given** a DOM selector change breaks message detection, **When** the watcher attempts to read messages, **Then** it logs a detailed error with the failing selector and continues running

---

### User Story 4 - Testing and Validation Mode (Priority: P4)

As a developer, I need a dry-run mode to test the watcher's detection logic without creating actual action files so I can validate configuration changes safely.

**Why this priority**: Essential for testing and debugging, but not required for core functionality. Can be added after P1-P3 are working.

**Independent Test**: Can be tested by running the watcher in dry-run mode with priority messages and verifying that detection is logged but no files are created.

**Acceptance Scenarios**:

1. **Given** the watcher is started in dry-run mode, **When** a priority message is detected, **Then** the detection is logged but no action file is created
2. **Given** dry-run mode is enabled, **When** the watcher processes 10 priority messages, **Then** all detections are logged with full details for validation
3. **Given** dry-run mode is disabled, **When** the watcher runs, **Then** action files are created normally

---

### Edge Cases

- What happens when WhatsApp Web session expires during operation?
  - System detects login screen, logs alert to /Needs_Action, and waits for manual re-authentication

- How does system handle network interruption mid-check?
  - Implements retry logic with exponential backoff (1s, 2s, 4s) up to 3 attempts before logging error

- What happens when DOM selectors change due to WhatsApp Web updates?
  - Logs detailed error with failing selector, continues running, creates alert in /Needs_Action

- How does system handle a large backlog of 100+ unread messages on first run?
  - Processes messages in batches, respects rate limits, maintains state to prevent duplicates

- What happens when the browser session directory becomes corrupted?
  - Detects corruption on startup, logs error, requests manual re-authentication

- How does system handle partial page loads?
  - Implements wait conditions with timeouts, retries if elements not found

- What happens when WhatsApp Web rate limits or temporarily blocks automation?
  - Detects rate limiting, increases polling interval temporarily, logs warning

- How does system handle messages with special characters or emojis?
  - Sanitizes text for filename generation, preserves original content in action file

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor WhatsApp Web for new unread messages at a configurable polling interval (default: 30 seconds)
- **FR-002**: System MUST filter messages based on a configurable list of priority keywords (case-insensitive matching)
- **FR-003**: System MUST create a structured markdown file in /Needs_Action for each priority message detected
- **FR-004**: System MUST maintain a persistent state file tracking processed message IDs to prevent duplicate processing
- **FR-005**: System MUST use browser session persistence to avoid requiring QR code scan on every restart
- **FR-006**: System MUST extract sender name, message content, and timestamp from each priority message
- **FR-007**: System MUST generate unique, filesystem-safe filenames for action files (format: WHATSAPP_YYYYMMDD_HHMMSS_sender.md)
- **FR-008**: System MUST support dry-run mode where detections are logged but no files are created
- **FR-009**: System MUST implement graceful shutdown handling (SIGTERM, SIGINT) to save state before exit
- **FR-010**: System MUST log all operations (detections, errors, state changes) to /Logs/YYYY-MM-DD.json in JSON Lines format
- **FR-011**: System MUST operate as a sensor-only component (no reasoning, no MCP calls, no action execution)
- **FR-012**: System MUST integrate with existing approval workflow by creating files compatible with the /Needs_Action folder structure

### Security & Approval Requirements

- **SR-001**: System MUST NOT send messages or perform any write operations in WhatsApp (read-only monitoring)
- **SR-002**: System MUST store browser session data in a local directory excluded from version control
- **SR-003**: System MUST implement idempotent operation to prevent duplicate action files across restarts
- **SR-004**: System MUST log all message detections with timestamp, sender, and keyword matched
- **SR-005**: System MUST create alert files in /Needs_Action when critical errors occur (session expired, authentication required)
- **SR-006**: System MUST NOT expose message content in logs (only metadata like sender and timestamp)

### Resilience Requirements

- **RR-001**: System MUST retry failed operations up to 3 times with exponential backoff (1s, 2s, 4s)
- **RR-002**: System MUST continue running after transient failures (network timeout, temporary WhatsApp error)
- **RR-003**: System MUST detect and handle WhatsApp Web session expiration gracefully
- **RR-004**: System MUST handle DOM selector changes without crashing (log error and continue)
- **RR-005**: System MUST recover from corrupted state files by initializing fresh state
- **RR-006**: System MUST implement health checks and self-monitoring for 24/7 operation
- **RR-007**: System MUST handle rate limiting by temporarily increasing polling interval

### Key Entities

- **WhatsApp Message**: Represents an unread message detected in WhatsApp Web
  - Attributes: message_id (unique identifier), sender_name, message_text, timestamp, chat_type (individual/group)
  - Used for: Detection, filtering, deduplication, action file creation

- **Action File**: Structured markdown file created in /Needs_Action for priority messages
  - Attributes: type (whatsapp_message), from (sender), received (timestamp), priority (high), status (pending), original_timestamp
  - Used for: Human review, approval workflow integration, audit trail

- **Watcher State**: Persistent record of processed messages
  - Attributes: processed_ids (list of message identifiers), last_check (timestamp), session_status
  - Used for: Idempotent operation, restart recovery, duplicate prevention

- **Priority Keyword**: Configurable business term triggering action file creation
  - Attributes: keyword (text), case_sensitive (boolean), category (optional)
  - Used for: Message filtering, relevance detection

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Priority messages are detected and action files created within 60 seconds of message arrival (2x polling interval)
- **SC-002**: System operates continuously for 24 hours without crashes or manual intervention
- **SC-003**: Zero duplicate action files are created across multiple restart cycles (100% idempotent operation)
- **SC-004**: System recovers automatically from 95% of transient failures (network timeouts, temporary errors)
- **SC-005**: Only messages containing priority keywords generate action files (0% false positives for non-priority messages)
- **SC-006**: System processes a backlog of 100 unread messages in under 5 minutes on first run
- **SC-007**: All message detections are logged with complete metadata for audit purposes
- **SC-008**: System integrates seamlessly with existing approval workflow (action files compatible with current pipeline)
- **SC-009**: Manual re-authentication is required at most once per 30 days (session persistence)
- **SC-010**: System resource usage remains under 200MB RAM and 5% CPU during normal operation

### Quality Metrics

- **QM-001**: 100% of priority messages detected result in valid, parseable action files
- **QM-002**: State file corruption recovery succeeds in 100% of test cases
- **QM-003**: Graceful shutdown completes within 5 seconds and preserves all state
- **QM-004**: Error messages include actionable information for troubleshooting (failing selector, error context)

## Assumptions

1. **WhatsApp Web Access**: User has a valid WhatsApp account and can access WhatsApp Web
2. **Browser Compatibility**: System uses Chromium-based browser automation (industry standard for WhatsApp Web)
3. **Keyword Configuration**: Default priority keywords include: urgent, asap, important, help, invoice, payment, emergency, critical, deadline
4. **Session Duration**: WhatsApp Web sessions remain valid for approximately 30 days before requiring re-authentication
5. **Message Format**: WhatsApp messages are plain text or contain text content (media-only messages are ignored)
6. **Polling Frequency**: 30-second polling interval provides acceptable balance between responsiveness and resource usage
7. **File System**: /Needs_Action folder exists and is writable (created by existing approval workflow)
8. **State Storage**: .state directory within vault is used for persistent state files
9. **Logging Format**: JSON Lines format is consistent with existing Gmail watcher implementation
10. **Network Reliability**: Internet connection is generally stable with occasional transient failures

## Out of Scope

- **Message Sending**: WhatsApp reply functionality (deferred to future MCP server implementation)
- **Media Handling**: Processing images, videos, or voice messages (text-only in Silver Tier)
- **Group Chat Management**: Advanced group features like admin actions, member management
- **Message Search**: Historical message search or retrieval beyond current unread messages
- **Multi-Account**: Supporting multiple WhatsApp accounts simultaneously
- **Real-Time Notifications**: Push notifications or webhooks (polling-based only)
- **Message Analytics**: Sentiment analysis, keyword trends, or business intelligence
- **Automated Responses**: Any form of automatic reply or message generation
- **Contact Management**: Syncing or managing WhatsApp contacts
- **Encryption Handling**: End-to-end encryption is handled by WhatsApp Web itself

## Dependencies

- **Existing Infrastructure**: Gmail watcher and approval workflow must be operational
- **Browser Automation**: Requires browser automation capability (Playwright or equivalent)
- **Vault Structure**: Depends on /Needs_Action, /Logs, and .state directories existing
- **State Management**: Reuses state management patterns from Gmail watcher
- **Logging System**: Integrates with existing JSON Lines logging infrastructure

## Risks

1. **WhatsApp Terms of Service**: Automated access may violate WhatsApp ToS (mitigation: personal use only, low frequency)
2. **DOM Changes**: WhatsApp Web UI updates could break selectors (mitigation: robust error handling, fallback strategies)
3. **Rate Limiting**: Excessive polling could trigger temporary blocks (mitigation: configurable intervals, backoff logic)
4. **Session Expiration**: Frequent re-authentication required (mitigation: persistent session, alert system)
5. **False Positives**: Keyword matching may trigger on non-urgent messages (mitigation: configurable keywords, human review)

## Notes

- This specification focuses on the sensor layer only - no reasoning or action execution
- WhatsApp Watcher follows the same architectural pattern as Gmail Watcher for consistency
- Implementation should prioritize reliability and idempotent operation over feature richness
- Dry-run mode is essential for testing and validation before production deployment
- Session management is critical - losing session state requires manual QR code scan
