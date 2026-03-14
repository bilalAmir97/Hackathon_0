# Research: WhatsApp Watcher Technology Decisions

**Feature**: 002-whatsapp-watcher
**Date**: 2026-02-25
**Status**: Complete

## Research Questions

### 1. Browser Automation for WhatsApp Web

**Question**: Which browser automation framework should we use for WhatsApp Web monitoring?

**Options Evaluated**:
- Playwright (Python)
- Selenium (Python)
- Puppeteer (Node.js)
- Direct WhatsApp API

**Decision**: Playwright with persistent browser context

**Rationale**:
- Industry standard for WhatsApp Web automation
- Excellent Python support with async/await
- Persistent context feature maintains login sessions across restarts
- Active development and good documentation
- Already added to project dependencies
- Better performance than Selenium for modern web apps

**Alternatives Considered**:
- **Selenium**: More mature but slower, more complex setup, less reliable for modern SPAs
- **Puppeteer**: Excellent but Node.js only, would require separate runtime
- **Direct API**: WhatsApp doesn't provide official API for personal accounts

**Trade-offs**:
- WhatsApp Web blocks headless mode (must run with visible browser)
- Requires Chromium installation (~300MB)
- DOM selectors may break with WhatsApp updates (mitigated with robust error handling)

---

### 2. Message Deduplication Strategy

**Question**: How do we reliably identify and deduplicate messages across restarts?

**Options Evaluated**:
- Composite key (sender + timestamp + preview)
- Message content hash
- Timestamp only
- Sequential numbering

**Decision**: Composite message ID from `sender_name + timestamp + message_text[:50]`

**Rationale**:
- WhatsApp Web doesn't expose stable message IDs in DOM
- Composite key provides reliable uniqueness without being fragile
- First 50 characters of message provide sufficient uniqueness
- Sender + timestamp alone insufficient (multiple messages same second)
- Resistant to minor content changes (uses preview, not full hash)

**Alternatives Considered**:
- **Full message hash**: Too fragile - any content change creates new ID
- **Timestamp only**: Insufficient - multiple messages can arrive same second
- **Sequential numbering**: Doesn't work across restarts or multiple devices

**Trade-offs**:
- Very long messages with identical first 50 chars could collide (extremely rare)
- Edited messages treated as new messages (acceptable for sensor layer)

---

### 3. DOM Selector Strategy

**Question**: How do we reliably select WhatsApp Web elements despite frequent UI updates?

**Options Evaluated**:
- data-testid attributes
- CSS class selectors
- XPath expressions
- Text content matching

**Decision**: Prioritize `data-testid` attributes with fallback to class-based selectors

**Rationale**:
- data-testid attributes more stable across WhatsApp updates
- WhatsApp Web uses data-testid for testing infrastructure
- Graceful degradation with fallback selectors
- Error handling logs failing selectors for debugging

**Alternatives Considered**:
- **XPath only**: Brittle, breaks easily with DOM structure changes
- **Class selectors only**: WhatsApp uses generated class names that change frequently
- **Text matching**: Language-dependent, unreliable for internationalization

**Implementation**:
```python
# Primary selector
chat_list = page.query_selector('[data-testid="chat-list"]')

# Fallback if primary fails
if not chat_list:
    chat_list = page.query_selector('.chat-list-container')

# Log error if both fail
if not chat_list:
    logger.error("Failed to find chat list with selectors: data-testid, class")
```

---

### 4. Session Persistence

**Question**: How do we maintain WhatsApp Web login across watcher restarts?

**Options Evaluated**:
- Playwright persistent_context
- Manual cookie management
- Fresh login each time
- Session token storage

**Decision**: Playwright `launch_persistent_context` with local directory

**Rationale**:
- Built-in Playwright feature for session persistence
- Stores cookies, local storage, and session data automatically
- Minimizes QR code scans (typically valid 30 days)
- Simple API, no manual cookie management

**Alternatives Considered**:
- **Manual cookies**: Complex, error-prone, requires understanding WhatsApp's auth flow
- **Fresh login**: Impractical for 24/7 operation, requires manual QR scan every restart
- **Token storage**: WhatsApp uses complex multi-token auth, difficult to replicate

**Implementation**:
```python
browser = playwright.chromium.launch_persistent_context(
    user_data_dir=".whatsapp_session",
    headless=False  # WhatsApp blocks headless
)
```

**Trade-offs**:
- Session directory must be gitignored (contains auth tokens)
- Corruption requires manual re-authentication
- Directory size ~50-100MB

---

### 5. Retry and Backoff Logic

**Question**: How should we handle transient failures (network timeouts, temporary errors)?

**Options Evaluated**:
- Exponential backoff
- Fixed delay retry
- Immediate retry
- No retry (fail fast)

**Decision**: Exponential backoff (1s, 2s, 4s) with max 3 retries

**Rationale**:
- Balances responsiveness with rate limit avoidance
- Standard pattern used in Gmail watcher (consistency)
- Gives transient issues time to resolve
- Prevents thundering herd on service recovery

**Alternatives Considered**:
- **Fixed delay**: Less adaptive to different failure types
- **Immediate retry**: Risks rate limiting and wasted resources
- **No retry**: Too fragile for production 24/7 operation

**Implementation**:
```python
for attempt in range(3):
    try:
        return perform_operation()
    except TransientError:
        if attempt < 2:
            delay = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(delay)
        else:
            raise
```

---

### 6. Logging Format

**Question**: What logging format should we use for consistency with existing infrastructure?

**Options Evaluated**:
- JSON Lines (existing standard)
- Structured JSON
- Plain text logs
- CSV format

**Decision**: JSON Lines format to `/Logs/YYYY-MM-DD.json`

**Rationale**:
- Consistent with Gmail watcher implementation
- One JSON object per line (easy to parse and append)
- Supports structured data (timestamp, action_type, status, inputs, outputs)
- Daily rotation by filename convention

**Format**:
```json
{"timestamp": "2026-02-25T10:30:00.000000Z", "log_id": "whatsapp_1234567890", "action_type": "message_detected", "status": "success", "inputs": {"sender": "John Doe", "keyword": "urgent"}, "outputs": {"action_file": "WHATSAPP_20260225_103000_john_doe.md"}}
```

---

### 7. State Management

**Question**: How should we persist watcher state (processed messages, session status)?

**Options Evaluated**:
- JSON file in vault
- SQLite database
- In-memory only
- Shared state with Gmail watcher

**Decision**: JSON file in `AI_Employee_Vault/.state/whatsapp_watcher_state.json`

**Rationale**:
- Consistent with local-first architecture
- Human-readable and inspectable
- Simple to backup and restore
- Reuses existing GmailState utility class

**State Structure**:
```json
{
  "processed_ids": [
    "John_Doe_10:30 AM_URGENT: Need invoice",
    "Jane_Smith_11:15 AM_IMPORTANT: Meeting"
  ],
  "last_check": "2026-02-25T10:30:00.000000Z",
  "session_status": "active"
}
```

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Language | Python | 3.13 | Existing project standard |
| Browser Automation | Playwright | 1.40+ | Best-in-class for modern web apps |
| State Management | JSON files | N/A | Local-first, human-readable |
| Logging | JSON Lines | N/A | Consistent with Gmail watcher |
| Process Management | PM2 | Latest | Existing deployment pattern |
| Testing | pytest | Latest | Existing test framework |

## Dependencies

**New**:
- playwright>=1.40.0 (browser automation)

**Existing** (reused):
- watchdog>=4.0.0 (file monitoring utilities)
- pyyaml>=6.0.0 (YAML parsing for action files)
- python-dotenv>=1.0.0 (environment variables)

## Installation Requirements

```bash
# Install Python dependencies
uv sync

# Install Playwright browsers (one-time, ~300MB)
uv run playwright install chromium
```

## Performance Characteristics

- **Startup time**: 5-10 seconds (browser launch)
- **Check cycle time**: 10-20 seconds (depends on unread count)
- **Memory usage**: 150-200MB (browser + Python)
- **CPU usage**: 2-5% average, 20-30% during check cycle
- **Disk usage**: ~400MB (Chromium + session data)

## Known Limitations

1. **Headless mode**: WhatsApp Web blocks headless browsers (must run with visible window)
2. **DOM stability**: Selectors may break with WhatsApp updates (mitigated with error handling)
3. **Rate limiting**: Excessive polling may trigger temporary blocks (mitigated with 30s interval)
4. **Session expiration**: Requires manual QR scan every ~30 days
5. **Single account**: Only one WhatsApp account per watcher instance

## Future Considerations

- **Multi-account support**: Would require separate browser contexts per account
- **Headless workaround**: Investigate virtual display (Xvfb) for true headless operation
- **Selector resilience**: Consider computer vision for element detection (overkill for MVP)
- **Real-time notifications**: WebSocket monitoring instead of polling (complex, not needed for 30s latency)

## Conclusion

All technology decisions align with existing project patterns and constitution principles. The stack is proven (Playwright + Python), the architecture is simple (sensor-only), and the implementation reuses existing utilities (state management, logging). No blockers identified.

**Status**: ✅ Research complete, ready for implementation validation.
