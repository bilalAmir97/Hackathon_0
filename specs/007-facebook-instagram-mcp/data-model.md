# Data Model: Facebook & Instagram MCP Server

**Feature**: 007-facebook-instagram-mcp
**Date**: 2026-03-18
**Phase**: Phase 1 - Design Artifacts

---

## Overview

This document defines the data entities and their relationships for the Facebook & Instagram MCP Server. These entities represent the domain model for social media posting, engagement tracking, and approval workflow integration.

---

## Entity Definitions

### 1. Post

Represents a social media post on Facebook or Instagram.

**Attributes**:
- `post_id` (string, required): Unique identifier from Meta API
  - Facebook format: `{page_id}_{post_id}` (e.g., "12345_67890")
  - Instagram format: `{media_id}` (e.g., "98765432109876543")
- `platform` (enum, required): Platform where post was published
  - Values: `"facebook"`, `"instagram"`
- `account_id` (string, required): Account identifier (page_id or ig_account_id)
- `content` (object, required): Post content
  - `message` (string, optional): Text content (Facebook) or caption (Instagram)
  - `link` (string, optional): External URL (Facebook only)
  - `image_paths` (array[string], optional): Local paths to images
  - `media_urls` (array[string], optional): Published media URLs from Meta CDN
- `scheduled_time` (datetime, optional): When post should be published (ISO 8601)
- `published_at` (datetime, optional): When post was actually published (ISO 8601)
- `status` (enum, required): Current post status
  - Values: `"pending_approval"`, `"approved"`, `"published"`, `"failed"`, `"denied"`
- `approval_id` (string, optional): Reference to approval request
- `permalink` (string, optional): Public URL to published post
- `created_at` (datetime, required): When post entity was created (ISO 8601)
- `error_message` (string, optional): Error details if status is "failed"

**Relationships**:
- Belongs to one Account (via account_id)
- Has many Metrics (one-to-many)
- References one ApprovalRequest (via approval_id)

**Validation Rules**:
- Facebook: message max 63,206 characters
- Instagram: message (caption) max 2,200 characters
- Instagram: image_paths required (at least one image)
- Facebook: image_paths optional (text-only posts allowed)
- scheduled_time must be in future if provided

**State Transitions**:
```
pending_approval → approved → published
pending_approval → denied
approved → failed (if publish fails)
```

**Example**:
```json
{
  "post_id": "12345_67890",
  "platform": "facebook",
  "account_id": "12345",
  "content": {
    "message": "Excited to announce our new product launch!",
    "link": "https://example.com/product",
    "image_paths": ["/path/to/image.jpg"],
    "media_urls": ["https://scontent.xx.fbcdn.net/..."]
  },
  "scheduled_time": null,
  "published_at": "2026-03-18T10:30:00Z",
  "status": "published",
  "approval_id": "approval-fb-post-20260318-123456",
  "permalink": "https://facebook.com/12345/posts/67890",
  "created_at": "2026-03-18T10:25:00Z",
  "error_message": null
}
```

---

### 2. Account

Represents a Facebook page or Instagram business account.

**Attributes**:
- `account_id` (string, required): Unique identifier from Meta API
  - Facebook: page_id (e.g., "12345")
  - Instagram: ig_user_id (e.g., "98765")
- `platform` (enum, required): Platform type
  - Values: `"facebook_page"`, `"instagram_business"`
- `name` (string, required): Account display name
- `username` (string, optional): Account username/handle
- `access_token` (string, required): Long-lived access token (stored in .env, not in entity)
- `token_expires_at` (datetime, optional): Token expiration timestamp (ISO 8601)
- `rate_limit_quota` (object, required): Current rate limit status
  - `call_count` (integer): Percentage of calls used (0-100)
  - `total_cputime` (integer): Percentage of CPU time used (0-100)
  - `total_time` (integer): Percentage of total time used (0-100)
  - `last_updated` (datetime): When quota was last updated (ISO 8601)
- `last_post_time` (datetime, optional): When last post was published (ISO 8601)
- `is_active` (boolean, required): Whether account is currently active
- `created_at` (datetime, required): When account was added to system (ISO 8601)

**Relationships**:
- Has many Posts (one-to-many)

**Validation Rules**:
- access_token must be valid long-lived token (60-day expiry)
- platform must match account_id format (page_id for facebook_page, ig_user_id for instagram_business)
- rate_limit_quota percentages must be 0-100

**Example**:
```json
{
  "account_id": "12345",
  "platform": "facebook_page",
  "name": "My Business Page",
  "username": "mybusiness",
  "access_token": "[stored in .env]",
  "token_expires_at": "2026-05-17T00:00:00Z",
  "rate_limit_quota": {
    "call_count": 45,
    "total_cputime": 30,
    "total_time": 35,
    "last_updated": "2026-03-18T10:30:00Z"
  },
  "last_post_time": "2026-03-18T09:15:00Z",
  "is_active": true,
  "created_at": "2026-03-01T00:00:00Z"
}
```

---

### 3. Metrics

Represents engagement metrics for a social media post.

**Attributes**:
- `metric_id` (string, required): Unique identifier (generated)
- `post_id` (string, required): Reference to Post entity
- `platform` (enum, required): Platform where metrics were collected
  - Values: `"facebook"`, `"instagram"`
- `metric_type` (enum, required): Type of metric
  - Facebook values: `"likes"`, `"comments"`, `"shares"`, `"reactions"`, `"reach"`, `"impressions"`
  - Instagram values: `"likes"`, `"comments"`, `"saves"`, `"reach"`, `"impressions"`, `"engagement_rate"`
- `value` (integer or float, required): Metric value
- `timestamp` (datetime, required): When metric was collected (ISO 8601)
- `cached_until` (datetime, optional): Cache expiry time (ISO 8601)

**Relationships**:
- Belongs to one Post (via post_id)

**Validation Rules**:
- value must be non-negative
- metric_type must be valid for platform
- timestamp must not be in future

**Aggregation**:
Metrics can be aggregated by:
- Time period (day, week, month)
- Metric type (all likes, all comments, etc.)
- Platform (Facebook vs Instagram)

**Example**:
```json
{
  "metric_id": "metric-fb-12345-67890-likes",
  "post_id": "12345_67890",
  "platform": "facebook",
  "metric_type": "likes",
  "value": 142,
  "timestamp": "2026-03-18T10:30:00Z",
  "cached_until": "2026-03-18T10:35:00Z"
}
```

---

### 4. ApprovalRequest

Represents an approval workflow request for a write operation.

**Attributes**:
- `id` (string, required): Unique identifier (format: `approval-{platform}-{action}-{timestamp}`)
- `action_type` (enum, required): Type of action requiring approval
  - Values: `"facebook_post"`, `"facebook_post_image"`, `"instagram_post"`, `"instagram_carousel"`
- `target_account` (string, required): Account identifier (page_id or ig_account_id)
- `content_preview` (object, required): Preview of content for approval decision
  - `message` (string): First 200 characters of post content
  - `image_url` (string, optional): Path to image file
  - `platform` (string): Platform name ("facebook" or "instagram")
  - `link` (string, optional): External link if present
- `risk_level` (enum, required): Calculated risk level
  - Values: `"low"`, `"medium"`, `"high"`
- `parameters` (object, required): Full parameters for action execution
  - Structure varies by action_type
  - Contains all data needed to execute action after approval
- `created_at` (datetime, required): When request was created (ISO 8601)
- `status` (enum, required): Current approval status
  - Values: `"pending"`, `"approved"`, `"denied"`, `"executed"`, `"failed"`
- `resolved_at` (datetime, optional): When request was approved/denied (ISO 8601)
- `executed_at` (datetime, optional): When action was executed (ISO 8601)
- `mcp_server` (string, required): MCP server name ("facebook_instagram_mcp")
- `execution_function` (string, required): Function to call on approval
- `result` (object, optional): Execution result (post_id, permalink, etc.)
- `error_message` (string, optional): Error details if status is "failed"

**Relationships**:
- References one Post (created after execution)
- References one Account (via target_account)

**Validation Rules**:
- id must be unique
- action_type must match parameters structure
- risk_level must be calculated based on content
- status transitions must follow workflow

**State Transitions**:
```
pending → approved → executed
pending → denied
approved → failed (if execution fails)
```

**File Representation**:
Stored as JSON file in `AI_Employee_Vault/Pending_Approval/APPROVAL_{action_type}_{timestamp}.json`

**Example**:
```json
{
  "id": "approval-fb-post-20260318-123456",
  "action_type": "facebook_post",
  "target_account": "12345",
  "content_preview": {
    "message": "Excited to announce our new product launch! Check out the details at our website. Limited time offer - don't miss out! #NewProduct #Launch #Exciting",
    "image_url": "/path/to/product-image.jpg",
    "platform": "facebook",
    "link": "https://example.com/product"
  },
  "risk_level": "medium",
  "parameters": {
    "page_id": "12345",
    "message": "Excited to announce our new product launch! Check out the details at our website. Limited time offer - don't miss out! #NewProduct #Launch #Exciting",
    "image_path": "/path/to/product-image.jpg",
    "link": "https://example.com/product"
  },
  "created_at": "2026-03-18T10:25:00Z",
  "status": "pending",
  "resolved_at": null,
  "executed_at": null,
  "mcp_server": "facebook_instagram_mcp",
  "execution_function": "execute_facebook_post_image",
  "result": null,
  "error_message": null
}
```

---

### 5. RateLimitState

Represents current rate limit state for Meta Graph API endpoints.

**Attributes**:
- `endpoint` (string, required): API endpoint path (e.g., "/feed", "/photos", "/media")
- `platform` (enum, required): Platform
  - Values: `"facebook"`, `"instagram"`
- `quota_used` (object, required): Current quota usage
  - `call_count` (integer): Percentage of calls used (0-100)
  - `total_cputime` (integer): Percentage of CPU time used (0-100)
  - `total_time` (integer): Percentage of total time used (0-100)
- `is_throttled` (boolean, required): Whether endpoint is currently throttled
- `throttle_until` (datetime, optional): When throttling will be lifted (ISO 8601)
- `last_request_time` (datetime, required): When last request was made (ISO 8601)
- `last_updated` (datetime, required): When quota was last updated (ISO 8601)
- `request_count` (integer, required): Number of requests made in current window
- `reset_time` (datetime, required): When quota will reset (ISO 8601)

**Relationships**:
- None (standalone state tracking)

**Validation Rules**:
- quota_used percentages must be 0-100
- is_throttled should be true if any quota_used value >= 80
- reset_time should be approximately 1 hour from first request in window

**Storage**:
In-memory only (not persisted to disk)

**Example**:
```json
{
  "endpoint": "/feed",
  "platform": "facebook",
  "quota_used": {
    "call_count": 78,
    "total_cputime": 65,
    "total_time": 70
  },
  "is_throttled": false,
  "throttle_until": null,
  "last_request_time": "2026-03-18T10:30:00Z",
  "last_updated": "2026-03-18T10:30:00Z",
  "request_count": 45,
  "reset_time": "2026-03-18T11:00:00Z"
}
```

---

## Entity Relationships Diagram

```
┌─────────────────┐
│    Account      │
│  (Facebook/IG)  │
└────────┬────────┘
         │
         │ has many
         │
         ▼
┌─────────────────┐         ┌──────────────────┐
│      Post       │◄────────│ ApprovalRequest  │
│ (FB/IG content) │ creates │  (Pending/Done)  │
└────────┬────────┘         └──────────────────┘
         │
         │ has many
         │
         ▼
┌─────────────────┐
│    Metrics      │
│ (Engagement)    │
└─────────────────┘

┌─────────────────┐
│ RateLimitState  │
│  (In-memory)    │
└─────────────────┘
(No relationships - standalone state)
```

---

## Data Flow

### Write Operation Flow (Post Creation)

1. **MCP Tool Invoked**: Claude Code calls `facebook_post_text` or `instagram_post_image`
2. **Validation**: Image validation, caption length check
3. **ApprovalRequest Created**: Entity created and saved to `Pending_Approval/`
4. **User Approval**: Human reviews and approves/denies
5. **Post Created**: On approval, Post entity created with status "approved"
6. **API Call**: Meta Graph API called to publish post
7. **Post Updated**: Post entity updated with post_id, permalink, status "published"
8. **Metrics Initialized**: Initial Metrics entities created (0 values)

### Read Operation Flow (Metrics Retrieval)

1. **MCP Tool Invoked**: Claude Code calls `get_facebook_post_metrics`
2. **Cache Check**: Check if Metrics entities exist and are not expired
3. **Cache Hit**: Return cached Metrics entities
4. **Cache Miss**: Fetch from Meta Graph API
5. **Metrics Created/Updated**: Create or update Metrics entities
6. **Cache Set**: Set cached_until timestamp (5 minutes from now)
7. **Return**: Return Metrics entities to caller

### Rate Limit Flow

1. **Before Request**: Check RateLimitState for endpoint
2. **Throttle Check**: If quota_used >= 80%, queue request
3. **Make Request**: Call Meta Graph API
4. **Parse Headers**: Extract X-App-Usage from response
5. **Update State**: Update RateLimitState with new quota_used
6. **Throttle Decision**: Set is_throttled if quota_used >= 80%

---

## Storage Strategy

### Persistent Storage (File-Based)

**ApprovalRequest**:
- Location: `AI_Employee_Vault/Pending_Approval/`
- Format: JSON files
- Lifecycle: Created → Moved to Done/ after execution

**Audit Logs** (via AuditLogger):
- Location: `AI_Employee_Vault/Logs/`
- Format: JSONL (one JSON object per line)
- Retention: 90 days

### Transient Storage (In-Memory)

**Post**: Not persisted (reconstructed from audit logs if needed)
**Account**: Loaded from .env on startup
**Metrics**: Cached in-memory (5-minute TTL)
**RateLimitState**: In-memory only (reset on restart)

---

## Data Validation

### Input Validation

All MCP tool inputs are validated before creating entities:
- Required fields present
- Field types correct (string, integer, datetime)
- Field values within constraints (length, range)
- Enum values valid
- Relationships valid (account exists, post exists)

### Output Validation

All API responses are validated before creating entities:
- Response structure matches expected format
- Required fields present in response
- Field types match expectations
- Error responses handled gracefully

---

## Error Handling

### Validation Errors

Return structured error response:
```json
{
  "status": "error",
  "error_type": "validation_error",
  "message": "Image size exceeds 8MB limit for Instagram",
  "details": {
    "field": "image_path",
    "constraint": "max_size",
    "limit": "8MB",
    "actual": "12MB"
  }
}
```

### API Errors

Log error and return structured response:
```json
{
  "status": "error",
  "error_type": "api_error",
  "message": "Meta API error: Invalid OAuth access token",
  "details": {
    "error_code": 190,
    "error_subcode": 463,
    "fbtrace_id": "ABC123XYZ"
  }
}
```

---

## Success Criteria

Data model is complete when:

1. ✅ All 5 entities defined with attributes and relationships
2. ✅ Validation rules specified for each entity
3. ✅ State transitions documented for stateful entities
4. ✅ Storage strategy defined (persistent vs transient)
5. ✅ Data flow documented for write and read operations
6. ✅ Error handling patterns defined
7. ✅ Entity relationship diagram provided

---

**Data Model Status**: ✅ COMPLETE
**Date Completed**: 2026-03-18
**Ready for Contracts**: YES
