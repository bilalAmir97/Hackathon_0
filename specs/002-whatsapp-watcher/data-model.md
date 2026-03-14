# Data Model: WhatsApp Watcher

**Feature**: 002-whatsapp-watcher
**Date**: 2026-02-25
**Purpose**: Define entities, relationships, and state transitions for WhatsApp Watcher

## Entity Definitions

### 1. WhatsAppMessage

**Description**: Represents an unread message detected in WhatsApp Web during a check cycle.

**Attributes**:
- `message_id` (string): Composite unique identifier (sender + timestamp + preview)
  - Format: `{sender_name}_{timestamp}_{message_text[:50]}`
  - Example: `John_Doe_10:30 AM_URGENT: Need invoice for last month`
- `sender_name` (string): Contact or group name from WhatsApp
- `message_text` (string): Full message content
- `timestamp` (string): WhatsApp's displayed timestamp (e.g., "10:30 AM", "Yesterday")
- `chat_type` (enum): Type of chat
  - Values: `individual`, `group`
- `detected_at` (datetime): ISO 8601 timestamp when watcher detected the message
- `keywords_matched` (list[string]): Priority keywords found in message

**Validation Rules**:
- `message_id` must be unique within watcher state
- `sender_name` cannot be empty
- `message_text` cannot be empty
- `timestamp` must be valid WhatsApp format
- `detected_at` must be valid ISO 8601 datetime

**Relationships**:
- One WhatsAppMessage → One ActionFile (if priority)
- One WhatsAppMessage → One WatcherState entry (processed_ids)

**Lifecycle**:
1. Detected in WhatsApp Web unread chats
2. Filtered by priority keywords
3. Checked against processed IDs (deduplication)
4. If new and priority: ActionFile created
5. Added to processed IDs in WatcherState
6. Never deleted (state persists indefinitely)

---

### 2. ActionFile

**Description**: Structured markdown file created in `/Needs_Action` for each priority WhatsApp message.

**Attributes**:
- `filename` (string): Unique filesystem-safe name
  - Format: `WHATSAPP_{YYYYMMDD}_{HHMMSS}_{sanitized_sender}.md`
  - Example: `WHATSAPP_20260225_103045_john_doe.md`
- `type` (string): Always `"whatsapp_message"`
- `from` (string): Sender name (from WhatsAppMessage)
- `received` (datetime): ISO 8601 timestamp when detected
- `priority` (string): Always `"high"` (only priority messages create files)
- `status` (string): Always `"pending"` (initial state)
- `original_timestamp` (string): WhatsApp's timestamp display
- `message_content` (string): Full message text
- `suggested_actions` (list[string]): Checklist of potential actions

**File Format**:
```yaml
---
type: whatsapp_message
from: John Doe
received: 2026-02-25T10:30:45.123456Z
priority: high
status: pending
original_timestamp: 10:30 AM
---

## WhatsApp Message from John Doe

**Received**: 10:30 AM

### Message Content

URGENT: Need the invoice for last month's project ASAP!

### Suggested Actions

- [ ] Reply to John Doe
- [ ] Forward to relevant party
- [ ] Create task or reminder
- [ ] Archive after processing

### Notes

Priority message detected by WhatsApp watcher.
```

**Validation Rules**:
- Filename must be unique (timestamp ensures uniqueness)
- YAML frontmatter must be valid
- All required fields must be present
- Sender name must be sanitized for filesystem (alphanumeric + underscore only)

**Relationships**:
- One ActionFile ← One WhatsAppMessage (source)
- One ActionFile → Approval Workflow (integration point)

**Lifecycle**:
1. Created in `/Needs_Action` by watcher
2. Human reviews message
3. Human creates approval request (if action needed)
4. Moved to `/Done` after processing (by human or orchestrator)

---

### 3. WatcherState

**Description**: Persistent state tracking processed messages and session status.

**Attributes**:
- `processed_ids` (list[string]): List of message IDs already processed
  - Prevents duplicate action file creation
  - Persists across restarts
  - No expiration (grows indefinitely)
- `last_check` (datetime): ISO 8601 timestamp of last successful check cycle
- `session_status` (enum): Current WhatsApp Web session state
  - Values: `active`, `expired`, `unknown`
- `total_messages_processed` (integer): Lifetime count of processed messages
- `last_error` (string, optional): Most recent error message (for debugging)

**Storage**:
- File: `AI_Employee_Vault/.state/whatsapp_watcher_state.json`
- Format: JSON
- Permissions: Read/write by watcher only

**Example**:
```json
{
  "processed_ids": [
    "John_Doe_10:30 AM_URGENT: Need invoice for last month",
    "Jane_Smith_11:15 AM_IMPORTANT: Meeting rescheduled",
    "Bob_Wilson_Yesterday_Help with project deadline"
  ],
  "last_check": "2026-02-25T10:30:45.123456Z",
  "session_status": "active",
  "total_messages_processed": 127,
  "last_error": null
}
```

**Validation Rules**:
- `processed_ids` must be a list (can be empty)
- `last_check` must be valid ISO 8601 datetime
- `session_status` must be one of allowed enum values
- `total_messages_processed` must be non-negative integer

**Relationships**:
- One WatcherState → Many WhatsAppMessages (tracking)
- One WatcherState per watcher instance

**Lifecycle**:
1. Initialized on first run (empty processed_ids)
2. Updated after each check cycle
3. Saved to disk after each update
4. Loaded on watcher startup
5. If corrupted: Re-initialized with warning

**State Transitions**:
```
[Empty State] → [First Run] → [Active Monitoring]
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
            [Session Active]                    [Session Expired]
                    │                                   │
                    │ (check cycle)                     │
                    ▼                                   ▼
            [Update processed_ids]              [Create Alert]
                    │                                   │
                    ▼                                   │
            [Save State]                                │
                    │                                   │
                    └───────────────┬───────────────────┘
                                    ▼
                            [Continue Monitoring]
```

---

### 4. PriorityKeyword

**Description**: Configurable business term that triggers action file creation when found in messages.

**Attributes**:
- `keyword` (string): The term to match (case-insensitive)
- `case_sensitive` (boolean): Whether matching is case-sensitive (default: false)
- `category` (string, optional): Grouping for keyword (e.g., "urgency", "financial")
- `enabled` (boolean): Whether keyword is active (default: true)

**Default Keywords**:
```python
DEFAULT_KEYWORDS = [
    "urgent",
    "asap",
    "important",
    "help",
    "invoice",
    "payment",
    "emergency",
    "critical",
    "deadline"
]
```

**Configuration**:
- Stored in watcher initialization (not persisted separately)
- Can be overridden via constructor parameter
- Case-insensitive matching by default

**Matching Logic**:
```python
def is_priority_message(message_text: str, keywords: list[str]) -> bool:
    """Check if message contains any priority keyword."""
    text_lower = message_text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)
```

**Validation Rules**:
- Keyword cannot be empty string
- Keyword should be alphanumeric (special chars allowed but not recommended)
- Minimum 3 characters recommended (avoid false positives)

**Relationships**:
- Many PriorityKeywords → Many WhatsAppMessages (filtering)

---

## Entity Relationships

```
┌─────────────────────┐
│  WhatsAppMessage    │
│  (Detected)         │
└──────────┬──────────┘
           │
           │ 1:1 (if priority)
           ▼
┌─────────────────────┐
│    ActionFile       │
│  (Created)          │
└──────────┬──────────┘
           │
           │ Integration
           ▼
┌─────────────────────┐
│  Approval Workflow  │
│  (Existing)         │
└─────────────────────┘

┌─────────────────────┐
│  WatcherState       │
│  (Persistent)       │
└──────────┬──────────┘
           │
           │ Tracks
           ▼
┌─────────────────────┐
│  WhatsAppMessage    │
│  (processed_ids)    │
└─────────────────────┘

┌─────────────────────┐
│  PriorityKeyword    │
│  (Configuration)    │
└──────────┬──────────┘
           │
           │ Filters
           ▼
┌─────────────────────┐
│  WhatsAppMessage    │
│  (Detection)        │
└─────────────────────┘
```

## State Transitions

### Message Processing Flow

```
[Unread Message in WhatsApp Web]
           │
           ▼
[Detected by Watcher] → [WhatsAppMessage created]
           │
           ▼
[Keyword Filtering] → [PriorityKeyword matching]
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
[Priority]   [Non-Priority]
     │           │
     │           └─→ [Ignored]
     ▼
[Check WatcherState.processed_ids]
     │
     ┌─────┴─────┐
     │           │
     ▼           ▼
[New]      [Already Processed]
     │           │
     │           └─→ [Skip (idempotent)]
     ▼
[Create ActionFile]
     │
     ▼
[Add to processed_ids]
     │
     ▼
[Save WatcherState]
     │
     ▼
[Log to /Logs/YYYY-MM-DD.json]
     │
     ▼
[Complete]
```

### Session State Transitions

```
[Startup]
    │
    ▼
[Load WatcherState]
    │
    ▼
[Launch Browser]
    │
    ▼
[Check WhatsApp Web]
    │
    ┌─────┴─────┐
    │           │
    ▼           ▼
[Logged In] [Login Screen]
    │           │
    │           ▼
    │      [session_status = expired]
    │           │
    │           ▼
    │      [Create Alert in /Needs_Action]
    │           │
    │           ▼
    │      [Wait for Manual Re-auth]
    │           │
    ▼           ▼
[session_status = active]
    │
    ▼
[Continue Monitoring]
```

## Data Validation

### Message ID Uniqueness

**Constraint**: No two messages should have the same message_id

**Enforcement**: Check against `WatcherState.processed_ids` before creating ActionFile

**Collision Handling**: If collision detected (extremely rare), append timestamp milliseconds

### Filename Safety

**Constraint**: ActionFile filenames must be filesystem-safe

**Enforcement**: Sanitize sender name (remove special characters, replace spaces with underscores)

**Example**:
```python
def sanitize_filename(sender: str) -> str:
    """Convert sender name to filesystem-safe string."""
    # Remove special characters, keep alphanumeric and spaces
    safe = re.sub(r'[^\w\s-]', '', sender)
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    # Lowercase for consistency
    return safe.lower()
```

### State File Integrity

**Constraint**: WatcherState must be valid JSON

**Enforcement**: Try/except on load, initialize fresh state if corrupted

**Recovery**:
```python
try:
    state = json.load(open(state_file))
except (json.JSONDecodeError, FileNotFoundError):
    logger.warning("State file corrupted, initializing fresh state")
    state = {
        "processed_ids": [],
        "last_check": None,
        "session_status": "unknown",
        "total_messages_processed": 0
    }
```

## Performance Considerations

### State File Growth

**Issue**: `processed_ids` list grows indefinitely

**Impact**:
- 1 message/day = 365 IDs/year = ~50KB/year
- 10 messages/day = 3650 IDs/year = ~500KB/year
- Negligible for years of operation

**Mitigation**: Not needed for MVP, could add expiration (e.g., 90 days) in future

### ActionFile Accumulation

**Issue**: `/Needs_Action` folder accumulates files

**Impact**: Depends on human processing rate

**Mitigation**: Human moves files to `/Done` after processing (existing workflow)

## Summary

The data model is simple and focused:
- **WhatsAppMessage**: Ephemeral detection object
- **ActionFile**: Persistent markdown file for human review
- **WatcherState**: Persistent state for idempotency
- **PriorityKeyword**: Configuration for filtering

All entities follow local-first principles (file-based storage), support idempotent operation (state tracking), and integrate cleanly with existing approval workflow.
