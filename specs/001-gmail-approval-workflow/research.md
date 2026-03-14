# Research: Gmail Watcher + Approval Workflow

**Feature**: 001-gmail-approval-workflow
**Created**: 2026-02-25
**Purpose**: Document technical research and decisions for implementation

## Research Questions & Decisions

### 1. Gmail API Integration Strategy

**Question**: What's the most efficient way to poll Gmail for new emails?

**Research Findings**:
- **Option A**: Pub/Sub notifications (push-based)
  - Pros: Real-time, no polling overhead, efficient
  - Cons: Requires external service (Cloud Pub/Sub), adds complexity, costs money
  - Verdict: ❌ Rejected - violates local-first principle

- **Option B**: Gmail API polling with `users().messages().list()`
  - Pros: Simple, no external dependencies, works with local-first architecture
  - Cons: Polling latency (2 min default), API quota usage
  - Verdict: ✅ **Selected**

**Decision**: Use `users().messages().list()` with `q='is:unread'` query parameter
- More efficient than fetching all messages and filtering locally
- Respects Gmail API quota limits (250 units/user/second)
- Configurable polling interval (default 120s, minimum 60s)

**Implementation Notes**:
```python
results = service.users().messages().list(
    userId='me',
    q='is:unread',
    maxResults=20
).execute()
```

---

### 2. Idempotency & State Management

**Question**: How to prevent duplicate action files after system restarts?

**Research Findings**:
- **Option A**: SQLite database
  - Pros: Queryable, relational, ACID guarantees
  - Cons: Adds dependency, violates local-first simplicity, requires schema migrations
  - Verdict: ❌ Rejected

- **Option B**: In-memory set
  - Pros: Fast, simple
  - Cons: Lost on restart, doesn't survive crashes
  - Verdict: ❌ Rejected

- **Option C**: Persistent JSON file with email ID set
  - Pros: Simple, survives restarts, human-readable, easy to debug
  - Cons: Grows unbounded (needs archival strategy)
  - Verdict: ✅ **Selected**

**Decision**: Persistent JSON file at `AI_Employee_Vault/.state/gmail_watcher_state.json`

**Schema**:
```json
{
  "last_poll_timestamp": "2026-02-25T14:30:00Z",
  "processed_email_ids": ["abc123", "xyz789", ...],
  "error_count": 0,
  "config": {
    "poll_interval_seconds": 120,
    "priority_keywords": ["urgent", "important", ...]
  }
}
```

**Archival Strategy**: After 10,000 entries, archive old IDs (keep last 30 days only)

---

### 3. File System Monitoring for Approval Workflow

**Question**: How to detect when files are moved between vault folders?

**Research Findings**:
- **Option A**: Polling folders every N seconds
  - Pros: Simple, cross-platform
  - Cons: Inefficient, high CPU usage, polling latency
  - Verdict: ❌ Rejected

- **Option B**: inotify (Linux-specific)
  - Pros: Event-driven, efficient, no polling
  - Cons: Linux-only, not cross-platform
  - Verdict: ❌ Rejected

- **Option C**: Watchdog library (Observer pattern)
  - Pros: Cross-platform, event-driven, well-maintained, efficient
  - Cons: Additional dependency
  - Verdict: ✅ **Selected**

**Decision**: Use `watchdog` library with `Observer` pattern

**Implementation Pattern**:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ApprovalHandler(FileSystemEventHandler):
    def on_moved(self, event):
        # Detect file movements between folders
        if event.dest_path.startswith('Approved/'):
            execute_approved_action(event.dest_path)
```

---

### 4. OAuth Token Management

**Question**: How to handle OAuth token expiration gracefully?

**Research Findings**:
- **Option A**: Refresh on failure
  - Pros: Simple
  - Cons: Causes unnecessary API errors, poor UX
  - Verdict: ❌ Rejected

- **Option B**: Manual refresh (human intervention)
  - Pros: Simple
  - Cons: Violates autonomy principle, requires human monitoring
  - Verdict: ❌ Rejected

- **Option C**: Check expiry before each API call, auto-refresh
  - Pros: Prevents failures, transparent to user, autonomous
  - Cons: Slight overhead on each call
  - Verdict: ✅ **Selected**

**Decision**: Check `creds.expired` before API calls, auto-refresh if needed

**Implementation**:
```python
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Save refreshed token
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
```

---

### 5. Retry Strategy for Transient Errors

**Question**: How to handle transient failures (network, rate limits)?

**Research Findings**:
- **Option A**: Fixed delay retry (e.g., always wait 5s)
  - Pros: Simple
  - Cons: Doesn't adapt to load, wastes time on quick recoveries
  - Verdict: ❌ Rejected

- **Option B**: Immediate retry
  - Pros: Fast recovery
  - Cons: Wastes API quota, can trigger rate limits
  - Verdict: ❌ Rejected

- **Option C**: Exponential backoff with jitter
  - Pros: Industry standard, adapts to load, prevents thundering herd
  - Cons: Slightly more complex
  - Verdict: ✅ **Selected**

**Decision**: Exponential backoff with jitter (1s, 2s, 4s + random 0-1s)

**Implementation**:
```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

---

### 6. Log Format & Storage

**Question**: What format for audit logs?

**Research Findings**:
- **Option A**: Single JSON array in one file
  - Pros: Valid JSON, easy to parse
  - Cons: Requires rewriting entire file on each append, not atomic
  - Verdict: ❌ Rejected

- **Option B**: CSV format
  - Pros: Human-readable, Excel-compatible
  - Cons: Poor for nested data, escaping issues
  - Verdict: ❌ Rejected

- **Option C**: JSON Lines (one JSON object per line)
  - Pros: Append-only (atomic), easy to parse, supports streaming
  - Cons: Not valid JSON as a whole (but each line is)
  - Verdict: ✅ **Selected**

**Decision**: JSON Lines format in `Logs/YYYY-MM-DD.json`

**Example**:
```json
{"timestamp":"2026-02-25T14:30:00Z","log_id":"uuid","action_type":"email_detected","status":"success"}
{"timestamp":"2026-02-25T14:31:00Z","log_id":"uuid","action_type":"email_sent","status":"success"}
```

**Rotation Strategy**: Daily files, compress after 7 days, delete after 90 days

---

### 7. Dry-Run Mode Implementation

**Question**: How to test workflow without executing real actions?

**Research Findings**:
- **Option A**: Separate code paths (if dry_run: ... else: ...)
  - Pros: Clear separation
  - Cons: Maintenance burden, code duplication, easy to forget
  - Verdict: ❌ Rejected

- **Option B**: Mock MCP server
  - Pros: Tests real integration
  - Cons: Complex setup, doesn't test actual MCP behavior
  - Verdict: ❌ Rejected

- **Option C**: Environment variable flag, skip execution but log intent
  - Pros: Simple, preserves workflow logic, easy to toggle
  - Cons: Requires discipline to check flag
  - Verdict: ✅ **Selected**

**Decision**: `DRY_RUN=true` environment variable

**Implementation**:
```python
import os

def execute_action(action):
    if os.getenv('DRY_RUN', 'false').lower() == 'true':
        log(f"DRY RUN: Would execute {action}")
        return
    # Real execution
    mcp_client.execute(action)
```

---

## Technology Stack Justification

### Python 3.10+
- Already used in Bronze tier (consistency)
- Excellent Gmail API support (official `google-api-python-client`)
- Rich ecosystem for file operations, JSON handling
- Type hints for better code quality
- Async support for future optimization

### google-auth-oauthlib
- Official Google library for OAuth 2.0
- Handles token refresh automatically
- Well-documented, actively maintained
- 10M+ downloads/month (mature, stable)

### watchdog
- Cross-platform file system monitoring (Linux, macOS, Windows)
- Event-driven architecture (efficient)
- Supports recursive directory watching
- 5M+ downloads/month (mature, stable)
- Used by major projects (pytest-watch, sphinx-autobuild)

### pytest
- Already used in project (consistency)
- Excellent fixture support for mocking Gmail API
- Parametrized tests for edge cases
- Coverage reporting built-in
- Industry standard for Python testing

---

## Performance Considerations

### Gmail API Quota
- **Limit**: 250 quota units/user/second, 1 billion/day
- **Cost per operation**:
  - `messages.list()`: 5 units
  - `messages.get()`: 5 units
  - `messages.send()`: 100 units
- **Mitigation**: Configurable polling interval (default 120s = 720 polls/day = 3,600 units)

### File System Performance
- **Vault size estimate**: 450 KB/day (100 emails)
- **90-day retention**: ~40 MB
- **Mitigation**: Daily log rotation, compression after 7 days

### Memory Usage
- **Watcher state**: ~10 KB (grows with processed_email_ids)
- **In-memory cache**: None (stateless, reads from files)
- **Mitigation**: Archive old email IDs after 10,000 entries

---

## Security Considerations

### Credential Storage
- **Decision**: OAuth credentials in `.env`, token in `token.json`
- **Rationale**: Environment variables prevent accidental git commits
- **Mitigation**: `.gitignore` includes `.env`, `token.json`, `credentials.json`

### Approval File Integrity
- **Risk**: Human could tamper with approval files
- **Mitigation**: Checksum validation (future enhancement)
- **Current**: Trust file system permissions

### Log Tampering
- **Risk**: Logs could be modified after creation
- **Mitigation**: Append-only file operations, immutable after creation
- **Future**: Digital signatures for log entries

---

## Alternatives Considered & Rejected

### Real-Time Email Processing
- **Approach**: Gmail Pub/Sub notifications
- **Rejected**: Requires external service, violates local-first principle
- **Trade-off**: Accept 2-minute polling latency for simplicity

### Database for State Management
- **Approach**: SQLite for processed email IDs
- **Rejected**: Adds complexity, violates local-first simplicity
- **Trade-off**: JSON file grows unbounded (mitigated by archival)

### Webhook-Based Approval
- **Approach**: Web UI for approval workflow
- **Rejected**: Adds web server, violates file-based principle
- **Trade-off**: Manual file movements in Obsidian (acceptable for single user)

---

## Open Questions & Future Research

1. **Scalability**: How to handle 1000+ emails/day?
   - Consider: Batch processing, parallel execution
   - Timeline: Gold tier (multi-user support)

2. **Multi-Account Support**: How to monitor multiple Gmail accounts?
   - Consider: Multiple watcher instances, shared state
   - Timeline: Gold tier

3. **Email Threading**: How to handle email conversations?
   - Consider: Thread-aware action grouping
   - Timeline: Silver tier enhancement

4. **Attachment Handling**: How to process email attachments?
   - Consider: Download to vault, virus scanning
   - Timeline: Gold tier

---

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 Best Practices](https://datatracker.ietf.org/doc/html/rfc6749)
- [Watchdog Documentation](https://python-watchdog.readthedocs.io/)
- [JSON Lines Specification](https://jsonlines.org/)
- [Exponential Backoff Algorithm](https://en.wikipedia.org/wiki/Exponential_backoff)
