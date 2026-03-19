# Research Findings: Facebook & Instagram MCP Server

**Feature**: 007-facebook-instagram-mcp
**Date**: 2026-03-18
**Phase**: Phase 0 - Research & Technology Decisions

---

## Overview

This document consolidates research findings and technology decisions for the Facebook & Instagram MCP Server implementation. All research tasks from plan.md have been completed, and all "NEEDS CLARIFICATION" items have been resolved.

---

## R1: Meta Graph API Integration Patterns

### Question
What are the best practices for integrating with Meta Graph API v19.0 for posting and metrics retrieval?

### Research Findings

#### Authentication Flow
**Decision**: Long-lived access tokens (60-day expiry)

**Findings**:
- Meta provides two token types: short-lived (1 hour) and long-lived (60 days)
- Long-lived tokens can be obtained via token exchange endpoint
- Tokens can be refreshed before expiry to maintain continuous access
- Page access tokens inherit page permissions from user token

**Best Practice**: Store long-lived tokens in .env, implement token validation on startup, provide clear refresh instructions on expiry.

#### API Endpoint Structure

**Facebook Page Posting**:
- Endpoint: `POST /{page-id}/feed`
- Parameters: `message`, `link`, `published` (for scheduling)
- Returns: `id` (post ID in format `{page-id}_{post-id}`)

**Facebook Page Photo Posting**:
- Endpoint: `POST /{page-id}/photos`
- Parameters: `message`, `url` or multipart file upload
- Returns: `id`, `post_id`

**Instagram Business Posting** (Two-step process):
1. Create media container: `POST /{ig-user-id}/media`
   - Parameters: `image_url`, `caption`
   - Returns: `id` (container ID)
2. Publish container: `POST /{ig-user-id}/media_publish`
   - Parameters: `creation_id` (container ID from step 1)
   - Returns: `id` (media ID)

**Metrics Retrieval**:
- Facebook: `GET /{post-id}/insights?metric=post_impressions,post_engaged_users`
- Instagram: `GET /{media-id}/insights?metric=impressions,reach,engagement`

#### Error Response Format

Meta API returns structured JSON errors:
```json
{
  "error": {
    "message": "Error description",
    "type": "OAuthException",
    "code": 190,
    "error_subcode": 463,
    "fbtrace_id": "trace_id"
  }
}
```

**Common Error Codes**:
- 190: Access token expired or invalid
- 4: Rate limit exceeded
- 100: Invalid parameter
- 200: Permission denied

**Best Practice**: Parse error responses, map to user-friendly messages, log fbtrace_id for debugging.

#### Pagination Patterns

Meta API uses cursor-based pagination:
```json
{
  "data": [...],
  "paging": {
    "cursors": {
      "before": "cursor_string",
      "after": "cursor_string"
    },
    "next": "https://graph.facebook.com/v19.0/..."
  }
}
```

**Best Practice**: For list operations (list_invoices equivalent), follow `next` URL until no more pages. Limit initial implementation to single page (sufficient for typical use cases).

### Decision Summary

- **Authentication**: Long-lived tokens stored in .env
- **API Version**: v19.0 (stable, well-documented)
- **Posting Pattern**: Direct POST for Facebook, two-step for Instagram
- **Error Handling**: Parse structured errors, map to user-friendly messages
- **Pagination**: Cursor-based, implement single-page initially

---

## R2: Rate Limiting Strategy

### Question
How should we implement proactive rate limiting to avoid hitting Meta API limits?

### Research Findings

#### Meta API Rate Limit Headers

Meta returns rate limit information in response headers:

**X-App-Usage** (app-level limits):
```json
{
  "call_count": 45,
  "total_cputime": 25,
  "total_time": 30
}
```

**X-Business-Use-Case-Usage** (business-level limits):
```json
{
  "business_id": {
    "call_count": 20,
    "total_cputime": 15,
    "total_time": 20
  }
}
```

**Rate Limit Calculation**:
- Limits are percentage-based (0-100%)
- Throttling begins at 75%, blocking at 100%
- Limits reset hourly (rolling window)
- Different endpoints have different weights

#### Throttling Strategies Evaluated

**1. Token Bucket Algorithm**:
- Pros: Smooth rate limiting, allows bursts
- Cons: Doesn't align with Meta's percentage-based limits

**2. Leaky Bucket Algorithm**:
- Pros: Constant rate, predictable
- Cons: Doesn't utilize available capacity efficiently

**3. Sliding Window (Meta's approach)**:
- Pros: Aligns with Meta's implementation, accurate
- Cons: More complex to implement

**Decision**: Hybrid approach - track percentage from headers, throttle proactively at 80% threshold.

#### Queue Management

**Approach**: In-memory queue with priority levels
- High priority: User-initiated actions (post now)
- Medium priority: Scheduled posts
- Low priority: Metrics retrieval (can be cached)

**Queue Behavior**:
- When rate limit reached (80%), queue new requests
- Process queue when limit drops below 50%
- Maximum queue size: 100 requests (prevent memory issues)
- Queue timeout: 1 hour (align with rate limit reset)

#### Exponential Backoff Pattern

**Strategy**: Exponential backoff with jitter for rate limit errors

```python
delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
```

**Parameters**:
- base_delay: 1 second
- max_delay: 60 seconds
- max_attempts: 5

**Rationale**: Prevents thundering herd, aligns with Meta's recommendations.

### Decision Summary

- **Rate Limit Tracking**: Parse X-App-Usage header, track percentage per endpoint
- **Proactive Throttling**: Block requests at 80% capacity
- **Queue Management**: In-memory priority queue, max 100 requests
- **Backoff Strategy**: Exponential with jitter (1s to 60s, max 5 attempts)
- **Implementation**: Custom (Meta's headers require custom parsing)

---

## R3: Image Upload Pipeline

### Question
What is the optimal approach for validating and uploading images to Facebook and Instagram?

### Research Findings

#### Image Format Validation

**Supported Formats**:
- Facebook: JPEG, PNG, GIF (including animated)
- Instagram: JPEG, PNG only (no GIF, no animated)

**Validation Approach**: Use Pillow to detect format from file header (not extension)

```python
from PIL import Image
img = Image.open(image_path)
format = img.format  # 'JPEG', 'PNG', 'GIF'
```

#### Size and Dimension Validation

**Facebook Limits**:
- Max file size: 4 MB
- Min dimensions: 200x200 pixels
- Max dimensions: 2048x2048 pixels (recommended)
- No strict aspect ratio requirement

**Instagram Limits**:
- Max file size: 8 MB
- Min width: 320 pixels
- Aspect ratio: 4:5 (portrait) to 1.91:1 (landscape)
- Recommended: 1080x1080 (square), 1080x1350 (portrait)

**Validation Logic**:
```python
width, height = img.size
aspect_ratio = width / height

# Instagram validation
if aspect_ratio < 0.8 or aspect_ratio > 1.91:
    raise ValidationError("Aspect ratio must be between 4:5 and 1.91:1")
```

#### Upload Methods Comparison

**Option 1: Multipart/form-data** (Recommended)
- Pros: Efficient, standard HTTP, no encoding overhead
- Cons: Requires file I/O
- Use case: Direct file upload

**Option 2: Base64 encoding**
- Pros: Can embed in JSON
- Cons: 33% size overhead, slower
- Use case: Not recommended for images

**Option 3: URL-based upload**
- Pros: No file transfer, Meta fetches from URL
- Cons: Requires publicly accessible URL
- Use case: Images already hosted online

**Decision**: Multipart/form-data for local files, URL-based for already-hosted images.

#### Temporary Storage for Scheduled Posts

**Approach**: No temporary storage needed

**Rationale**:
- Approval workflow stores image path in approval request
- Image remains at original location until approval
- On approval, image is uploaded directly from original path
- No need for temporary copies

**Edge Case**: If original image is deleted before approval, upload will fail with clear error message.

### Decision Summary

- **Format Validation**: Pillow-based format detection from file header
- **Size Validation**: Check file size before opening (os.path.getsize)
- **Dimension Validation**: Pillow to get dimensions, calculate aspect ratio
- **Upload Method**: Multipart/form-data for local files
- **Temporary Storage**: None (use original file path from approval request)
- **Library**: Pillow (comprehensive, lightweight, stable)

---

## R4: Metrics Caching Strategy

### Question
How should we cache engagement metrics to reduce API calls while maintaining freshness?

### Research Findings

#### Cache Invalidation Strategies

**TTL (Time-To-Live)** (Recommended):
- Pros: Simple, predictable, automatic expiry
- Cons: May serve stale data near expiry
- Use case: Metrics that update gradually (likes, comments)

**LRU (Least Recently Used)**:
- Pros: Automatic memory management
- Cons: No freshness guarantee
- Use case: Limited cache size, many unique keys

**Manual Invalidation**:
- Pros: Precise control, always fresh
- Cons: Complex, requires tracking dependencies
- Use case: Critical data that must be fresh

**Decision**: TTL (5 minutes) + LRU eviction for memory management.

#### Cache Storage Options

**In-Memory (dict with TTL)** (Recommended):
- Pros: Fast, simple, no external dependencies
- Cons: Lost on restart, not shared across processes
- Use case: Single MCP server instance, acceptable staleness

**File-Based**:
- Pros: Persists across restarts
- Cons: Slower, file I/O overhead
- Use case: Not needed (metrics not critical to persist)

**Redis**:
- Pros: Shared cache, advanced features
- Cons: External dependency, overkill for simple caching
- Use case: Not needed (single server instance)

**Decision**: In-memory with cachetools library (TTL + LRU).

#### Cache Key Design

**Key Format**: `{platform}:{resource_type}:{resource_id}:{metric_type}`

**Examples**:
- `facebook:post:12345_67890:engagement`
- `instagram:media:98765:insights`
- `facebook:page:12345:insights:week`

**Rationale**: Hierarchical structure enables selective invalidation.

#### Cache Hit Rate Optimization

**Strategies**:
1. Cache at appropriate granularity (per-post, not per-metric)
2. Pre-fetch commonly accessed metrics (page insights)
3. Batch requests when possible (multiple metrics in one API call)

**Expected Hit Rate**: 60-70% (based on typical usage patterns)

#### Stale Data Handling

**Approach**: Serve stale data with warning if API unavailable

```python
try:
    data = fetch_from_api()
    cache.set(key, data, ttl=300)
except APIError:
    cached_data = cache.get(key, ignore_expiry=True)
    if cached_data:
        return {"data": cached_data, "warning": "Stale data (API unavailable)"}
    raise
```

### Decision Summary

- **Cache Strategy**: TTL (5 minutes) + LRU eviction
- **Cache Storage**: In-memory (cachetools library)
- **Cache Key**: Hierarchical format (platform:type:id:metric)
- **Invalidation**: Automatic TTL expiry, manual invalidation on write operations
- **Stale Data**: Serve with warning if API unavailable
- **Library**: cachetools (TTL + LRU support, thread-safe)

---

## R5: Approval Workflow Integration

### Question
How should we integrate with the existing approval workflow system for social media posts?

### Research Findings

#### Approval Request File Format

**Pattern**: Follow odoo_mcp_server.py pattern

**File Location**: `AI_Employee_Vault/Pending_Approval/APPROVAL_{action_type}_{timestamp}.json`

**File Structure**:
```json
{
  "id": "approval-fb-post-20260318-123456",
  "action_type": "facebook_post",
  "target_account": "page_id_12345",
  "content_preview": {
    "message": "First 200 chars of post...",
    "image_url": "path/to/image.jpg",
    "platform": "facebook"
  },
  "risk_level": "medium",
  "parameters": {
    "page_id": "12345",
    "message": "Full post content...",
    "image_path": "/path/to/image.jpg",
    "link": null
  },
  "created_at": "2026-03-18T10:30:00Z",
  "status": "pending",
  "mcp_server": "facebook_instagram_mcp",
  "execution_function": "execute_facebook_post"
}
```

#### Risk Level Calculation

**Risk Factors**:
1. Content length (longer = higher risk)
2. External links (present = higher risk)
3. Image content (present = higher risk)
4. Target audience size (larger = higher risk)

**Risk Levels**:
- **Low**: Text-only post, <280 chars, no links
- **Medium**: Text with image, or text >280 chars, or contains link
- **High**: Multiple images (carousel), or scheduled post, or contains sensitive keywords

**Implementation**:
```python
def calculate_risk_level(parameters):
    risk_score = 0
    if len(parameters.get('message', '')) > 280:
        risk_score += 1
    if parameters.get('image_path'):
        risk_score += 1
    if parameters.get('link'):
        risk_score += 1
    if parameters.get('image_paths'):  # carousel
        risk_score += 2

    if risk_score == 0:
        return "low"
    elif risk_score <= 2:
        return "medium"
    else:
        return "high"
```

#### Content Preview Generation

**Text Preview**: First 200 characters with ellipsis if truncated

**Image Preview**: Store image path (not thumbnail) - approval UI can display if needed

**Platform Indicator**: Include platform name (facebook/instagram) for clarity

#### Approval Executor Integration

**Detection**: Approval executor monitors `Pending_Approval/` directory for new files

**Execution**: On approval, executor:
1. Reads approval request file
2. Extracts `mcp_server` and `execution_function`
3. Dynamically imports MCP server module
4. Calls execution function with parameters
5. Logs result via audit logger
6. Moves file to `Done/` directory

**Execution Function Pattern**:
```python
def execute_facebook_post(parameters):
    """Called by approval executor after approval."""
    client = get_meta_client()
    result = client.post_to_facebook_page(
        page_id=parameters['page_id'],
        message=parameters['message'],
        link=parameters.get('link')
    )
    return result
```

#### Denial Handling

**On Denial**:
1. Approval executor logs denial reason
2. Moves file to `Done/` with status "denied"
3. Creates notification in `Needs_Action/` for user
4. No cleanup needed (image remains at original location)

**Notification Format**:
```markdown
# Social Media Post Denied

**Action**: Facebook Post
**Reason**: User denied approval
**Content Preview**: First 200 chars...
**Timestamp**: 2026-03-18T10:30:00Z

No further action required. Post was not published.
```

### Decision Summary

- **File Format**: JSON following odoo_mcp_server.py pattern
- **File Location**: `Pending_Approval/APPROVAL_{action_type}_{timestamp}.json`
- **Risk Calculation**: Score-based (0=low, 1-2=medium, 3+=high)
- **Content Preview**: First 200 chars + image path + platform
- **Executor Integration**: Dynamic import + execution function pattern
- **Denial Handling**: Log + move to Done/ + notify user

---

## Technology Stack Summary

### Core Dependencies

| Library | Version | Purpose | Rationale |
|---------|---------|---------|-----------|
| requests | >=2.31.0 | HTTP client for Meta Graph API | Simple, synchronous, consistent with existing MCP servers |
| Pillow | >=10.0.0 | Image validation and processing | Comprehensive validation, lightweight, stable |
| cachetools | >=5.3.0 | Metrics caching (TTL + LRU) | Built-in TTL, thread-safe, automatic memory management |
| python-dotenv | >=1.0.0 | Environment variable management | Standard for .env files, simple API |
| mcp | (existing) | MCP protocol server | Required for MCP server implementation |

### Existing Infrastructure (Reused)

| Component | Location | Purpose |
|-----------|----------|---------|
| AuditLogger | scripts/audit_logger.py | Audit logging with sensitive data masking |
| Error Recovery | scripts/error_recovery/ | Retry decorators, circuit breaker |
| Approval Executor | scripts/approval_executor.py | Execute approved actions |

---

## Implementation Readiness

### All Research Tasks Complete

- ✅ R1: Meta Graph API Integration Patterns - RESOLVED
- ✅ R2: Rate Limiting Strategy - RESOLVED
- ✅ R3: Image Upload Pipeline - RESOLVED
- ✅ R4: Metrics Caching Strategy - RESOLVED
- ✅ R5: Approval Workflow Integration - RESOLVED

### All Technology Choices Made

- ✅ TC1: HTTP Client Library - `requests` (synchronous)
- ✅ TC2: Image Processing Library - `Pillow`
- ✅ TC3: Rate Limiting Implementation - Custom (Meta header parsing)
- ✅ TC4: Metrics Caching - `cachetools` (TTL + LRU)

### No NEEDS CLARIFICATION Items Remaining

All technical unknowns have been resolved. Ready to proceed to Phase 1 (Design Artifacts).

---

## Next Steps

1. ✅ Phase 0 Complete - All research tasks resolved
2. **Phase 1 Next**: Create data-model.md (entity definitions)
3. **Phase 1 Next**: Create contracts/ (MCP tool schemas)
4. **Phase 1 Next**: Create quickstart.md (setup guide)
5. **Phase 1 Final**: Update agent context with new technologies

---

**Research Status**: ✅ COMPLETE
**Date Completed**: 2026-03-18
**Ready for Phase 1**: YES
