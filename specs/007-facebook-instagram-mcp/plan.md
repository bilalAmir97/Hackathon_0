# Implementation Plan: Facebook & Instagram MCP Server

**Branch**: `007-facebook-instagram-mcp` | **Date**: 2026-03-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-facebook-instagram-mcp/spec.md`

## Summary

Create an MCP server that integrates with Meta Graph API to enable social media posting and engagement tracking for Facebook pages and Instagram business accounts. The server will expose 8 MCP tools (4 write, 4 read) for posting content, retrieving engagement metrics, and scheduling posts. All write operations will integrate with the existing approval workflow system. The implementation will follow established patterns from email_mcp_server.py and odoo_mcp_server.py, including audit logging, error recovery decorators, and file-based approval workflow.

**Technical Approach**: Python MCP server using Meta Graph API v19.0, with rate limiting via proactive throttling, image upload via multipart/form-data, metrics caching (5 minutes), and approval workflow integration for all write operations.

## Technical Context

**Language/Version**: Python 3.10+ (matching existing codebase)
**Primary Dependencies**:
- `mcp` (MCP protocol server)
- `requests` (Meta Graph API HTTP client)
- `Pillow` (image validation and processing)
- `python-dotenv` (environment variable management)

**Storage**:
- File-based approval workflow (AI_Employee_Vault/Pending_Approval/)
- Metrics cache (in-memory with 5-minute TTL)
- Rate limit state (in-memory, tracked per endpoint)
- Audit logs (AI_Employee_Vault/Logs/ via AuditLogger)

**Testing**: pytest (matching existing test suite)
- Unit tests for each MCP tool
- Integration tests for Meta Graph API calls
- Contract tests for approval workflow integration
- End-to-end tests for complete posting workflows

**Target Platform**: Linux server (WSL2 environment)

**Project Type**: Single project (MCP server module)

**Performance Goals**:
- Post creation: <2 seconds (excluding approval wait time)
- Metrics retrieval: <1 second (with caching)
- Image upload: <5 seconds for images up to 8MB
- Rate limit detection: <100ms overhead per request

**Constraints**:
- Meta API rate limits: 200 calls/hour per user (proactive throttling at 80%)
- Image size limits: Facebook 4MB, Instagram 8MB
- Caption limits: Facebook 63,206 chars, Instagram 2,200 chars
- Approval workflow adds 1-60 minutes latency (acceptable)

**Scale/Scope**:
- 2 platforms (Facebook, Instagram)
- 9 MCP tools (4 write, 5 read)
- ~500 lines of core logic (excluding tests)
- Support for 1-2 accounts per platform initially

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with project constitution (`.specify/memory/constitution.md`):

- [x] **Local-First Architecture**: Approval requests stored in vault files (Pending_Approval/), audit logs in Logs/, no critical state in external DBs
- [x] **Safety Before Autonomy**: All write operations (post, schedule) require approval workflow before execution
- [x] **File-Based State Transitions**: Approval workflow uses file movements (Pending_Approval/ → Approved/ → Done/)
- [x] **Idempotent Watchers**: N/A (this is an MCP server, not a watcher - idempotency handled by approval workflow)
- [x] **Explicit Reasoning**: MCP tools invoked by Claude Code after reasoning, approval requests document intent
- [x] **Human Accountability**: Approval boundaries enforced programmatically, no override capability in code
- [x] **Auditability**: All operations logged via AuditLogger with action_type, actor, target, parameters, result
- [x] **Secrets Management**: Access tokens in .env file only, never in code or vault files
- [x] **Tier Isolation**: Gold Tier feature (Module 3), code in mcp_servers/ directory
- [x] **Error Handling**: Retry decorators for network errors, circuit breaker for API failures, graceful degradation for rate limits

**Violations Requiring Justification**: None - all constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/007-facebook-instagram-mcp/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── facebook_tools.json      # Facebook MCP tool schemas
│   ├── instagram_tools.json     # Instagram MCP tool schemas
│   └── approval_workflow.json   # Approval request schema
├── checklists/
│   └── requirements.md  # Specification quality checklist (completed)
└── tasks.md             # Phase 2 output (created by /sp.tasks)
```

### Source Code (repository root)

```text
mcp_servers/
├── facebook_instagram_mcp_server.py  # Main MCP server (new)
├── meta_graph_client.py              # Meta Graph API client (new)
├── rate_limiter.py                   # Rate limiting logic (new)
├── image_validator.py                # Image validation (new)
├── email_mcp_server.py               # Existing (reference)
├── odoo_mcp_server.py                # Existing (reference)
└── odoo_client.py                    # Existing (reference)

scripts/
├── audit_logger.py                   # Existing (used by MCP server)
├── approval_executor.py              # Existing (executes approved actions)
└── error_recovery/                   # Existing (decorators for retry/circuit breaker)
    ├── decorators.py
    ├── retry_policy.py
    └── circuit_breaker.py

tests/
├── test_facebook_instagram_mcp_server.py  # MCP server tests (new)
├── test_meta_graph_client.py              # API client tests (new)
├── test_rate_limiter.py                   # Rate limiting tests (new)
├── test_image_validator.py                # Image validation tests (new)
├── test_integration_social_workflow.py    # End-to-end tests (new)
└── conftest.py                            # Existing (shared fixtures)

AI_Employee_Vault/
├── Pending_Approval/                 # Approval requests created here
├── Approved/                         # Approved actions moved here
├── Done/                             # Completed actions moved here
└── Logs/                             # Audit logs written here

.env                                  # Environment variables (not in git)
├── FACEBOOK_PAGE_ACCESS_TOKEN
├── FACEBOOK_PAGE_ID
├── INSTAGRAM_BUSINESS_ACCESS_TOKEN
└── INSTAGRAM_BUSINESS_ACCOUNT_ID
```

**Structure Decision**: Single project structure following existing MCP server pattern. New MCP server in `mcp_servers/` directory alongside email and Odoo servers. Supporting modules (API client, rate limiter, image validator) in same directory. Tests in `tests/` directory following existing naming convention. Approval workflow uses existing vault structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - table not needed.

---

## Phase 0: Research & Technology Decisions

### Research Tasks

#### R1: Meta Graph API Integration Patterns

**Question**: What are the best practices for integrating with Meta Graph API v19.0 for posting and metrics retrieval?

**Research Areas**:
1. Authentication flow (long-lived tokens vs short-lived)
2. API endpoint structure for Facebook pages vs Instagram business accounts
3. Error response formats and error codes
4. Pagination patterns for list operations
5. Webhook integration for real-time updates (future enhancement)

**Decision Criteria**:
- Simplicity of authentication (prefer long-lived tokens)
- Reliability of API endpoints (prefer stable v19.0 endpoints)
- Error handling patterns (prefer structured error responses)

#### R2: Rate Limiting Strategy

**Question**: How should we implement proactive rate limiting to avoid hitting Meta API limits?

**Research Areas**:
1. Meta API rate limit headers (`X-App-Usage`, `X-Business-Use-Case-Usage`)
2. Rate limit calculation (per-user vs per-app)
3. Throttling strategies (token bucket, leaky bucket, sliding window)
4. Queue management for rate-limited requests
5. Exponential backoff patterns

**Decision Criteria**:
- Prevent rate limit errors (proactive throttling at 80% capacity)
- Minimize latency (prefer in-memory tracking)
- Graceful degradation (queue requests when limit reached)

#### R3: Image Upload Pipeline

**Question**: What is the optimal approach for validating and uploading images to Facebook and Instagram?

**Research Areas**:
1. Image format validation (JPEG, PNG, GIF)
2. Size and dimension validation (Facebook 4MB, Instagram 8MB)
3. Aspect ratio validation (Instagram 4:5 to 1.91:1)
4. Upload methods (multipart/form-data vs base64)
5. Temporary storage for scheduled posts

**Decision Criteria**:
- Validation before upload (fail fast on invalid images)
- Efficient upload (prefer multipart/form-data over base64)
- Minimal disk usage (validate in-memory when possible)

#### R4: Metrics Caching Strategy

**Question**: How should we cache engagement metrics to reduce API calls while maintaining freshness?

**Research Areas**:
1. Cache invalidation strategies (TTL, LRU, manual invalidation)
2. Cache storage (in-memory vs file-based)
3. Cache key design (post_id, metric_type, timestamp)
4. Cache hit rate optimization
5. Stale data handling

**Decision Criteria**:
- Reduce API calls (5-minute TTL acceptable for metrics)
- Simplicity (prefer in-memory cache with TTL)
- Freshness (invalidate on write operations)

#### R5: Approval Workflow Integration

**Question**: How should we integrate with the existing approval workflow system for social media posts?

**Research Areas**:
1. Approval request file format (JSON structure)
2. Risk level calculation (low/medium/high based on content)
3. Content preview generation (text truncation, image thumbnails)
4. Approval executor integration (how it detects and executes approved actions)
5. Denial handling (user notification, cleanup)

**Decision Criteria**:
- Consistency with existing approval workflow (follow odoo_mcp_server.py pattern)
- Clear content preview (enable informed approval decisions)
- Robust error handling (handle approval denials gracefully)

### Technology Choices

#### TC1: HTTP Client Library

**Options Considered**:
1. `requests` - Simple, synchronous, widely used
2. `httpx` - Async support, modern API
3. `aiohttp` - Async-first, high performance

**Decision**: `requests`

**Rationale**:
- Existing codebase uses synchronous patterns (email_mcp_server.py, odoo_mcp_server.py)
- MCP protocol supports async but doesn't require it
- Simpler error handling and retry logic with synchronous code
- Meta Graph API calls are I/O bound but not high-volume (rate limited)

**Alternatives Rejected**:
- `httpx`: Adds async complexity without significant benefit for rate-limited API
- `aiohttp`: Requires async/await throughout, inconsistent with existing MCP servers

#### TC2: Image Processing Library

**Options Considered**:
1. `Pillow` - Full-featured, widely used
2. `imageio` - Lightweight, simple API
3. `opencv-python` - Advanced features, heavy dependency

**Decision**: `Pillow`

**Rationale**:
- Comprehensive validation (format, size, dimensions, aspect ratio)
- Lightweight compared to OpenCV
- Well-documented and stable
- Supports all required formats (JPEG, PNG, GIF)

**Alternatives Rejected**:
- `imageio`: Limited validation capabilities
- `opencv-python`: Overkill for validation-only use case, large dependency

#### TC3: Rate Limiting Implementation

**Options Considered**:
1. Custom implementation (token bucket algorithm)
2. `ratelimit` library (decorator-based)
3. `pyrate-limiter` (advanced features)

**Decision**: Custom implementation

**Rationale**:
- Meta API provides rate limit headers (need custom parsing)
- Proactive throttling requires custom logic (80% threshold)
- Per-endpoint tracking (different limits for different endpoints)
- Integration with error recovery decorators

**Alternatives Rejected**:
- `ratelimit`: Doesn't support dynamic limits from API headers
- `pyrate-limiter`: Overkill for simple rate limiting needs

#### TC4: Metrics Caching

**Options Considered**:
1. In-memory dict with TTL (custom)
2. `cachetools` library (LRU, TTL support)
3. Redis (external cache)

**Decision**: `cachetools` library

**Rationale**:
- Built-in TTL support (5-minute expiry)
- Thread-safe (important for concurrent requests)
- Lightweight (no external dependencies)
- LRU eviction (automatic memory management)

**Alternatives Rejected**:
- Custom dict: Requires manual TTL tracking and thread safety
- Redis: Overkill for simple caching, adds external dependency

---

## Phase 1: Design Artifacts

### Data Model

See `data-model.md` (to be created in Phase 1)

**Key Entities**:
1. **Post** - Represents a social media post (Facebook or Instagram)
2. **Account** - Represents a Facebook page or Instagram business account
3. **Metrics** - Engagement metrics for a post
4. **ApprovalRequest** - Approval workflow request for write operations
5. **RateLimitState** - Tracks API rate limit quotas per endpoint

### API Contracts

See `contracts/` directory (to be created in Phase 1)

**MCP Tool Contracts**:
1. `facebook_post_text` - Post text to Facebook page
2. `facebook_post_image` - Post image to Facebook page
3. `instagram_post_image` - Post image to Instagram
4. `instagram_post_carousel` - Post carousel to Instagram
5. `get_facebook_post_metrics` - Retrieve Facebook engagement
6. `get_instagram_post_metrics` - Retrieve Instagram engagement
7. `get_facebook_page_insights` - Page-level analytics
8. `get_instagram_account_insights` - Account-level analytics

**Approval Workflow Contract**:
- Approval request file format (JSON)
- Risk level calculation rules
- Content preview format

### Quickstart Guide

See `quickstart.md` (to be created in Phase 1)

**Setup Steps**:
1. Obtain Facebook page access token (Meta Business Suite)
2. Obtain Instagram business account access token
3. Configure .env file with tokens and account IDs
4. Install dependencies (`pip install -r requirements.txt`)
5. Start MCP server (`python mcp_servers/facebook_instagram_mcp_server.py`)
6. Test with Claude Code (post to Facebook, retrieve metrics)

---

## Phase 2: Implementation Approach

### Module Breakdown

#### Module 1: Meta Graph API Client (`meta_graph_client.py`)

**Responsibilities**:
- HTTP client wrapper for Meta Graph API
- Authentication (access token injection)
- Error handling (parse API error responses)
- Retry logic (network errors, transient failures)
- Rate limit header parsing

**Key Methods**:
- `post_to_facebook_page(page_id, message, link=None)` → post_id
- `post_image_to_facebook(page_id, message, image_path)` → post_id
- `post_to_instagram(account_id, caption, image_path)` → media_id
- `get_post_metrics(post_id, metrics)` → dict
- `get_page_insights(page_id, period, metrics)` → dict
- `upload_image(image_path)` → media_id

**Error Recovery**:
- `@with_retry` decorator for network errors (3 attempts, exponential backoff)
- `@with_circuit_breaker` decorator for API failures (5 failures → open circuit)

#### Module 2: Rate Limiter (`rate_limiter.py`)

**Responsibilities**:
- Track rate limit quotas per endpoint
- Parse rate limit headers from API responses
- Proactive throttling (block requests at 80% capacity)
- Queue management for rate-limited requests
- Exponential backoff for rate limit errors

**Key Methods**:
- `check_rate_limit(endpoint)` → bool (can proceed?)
- `update_rate_limit(endpoint, headers)` → None
- `wait_for_rate_limit_reset(endpoint)` → None
- `get_rate_limit_status()` → dict (for monitoring)

**State Management**:
- In-memory tracking (per-endpoint quotas)
- Thread-safe (concurrent requests)
- Reset on quota refresh (hourly)

#### Module 3: Image Validator (`image_validator.py`)

**Responsibilities**:
- Validate image format (JPEG, PNG, GIF)
- Validate image size (Facebook 4MB, Instagram 8MB)
- Validate dimensions (min 200x200px for Facebook, min 320px width for Instagram)
- Validate aspect ratio (Instagram 4:5 to 1.91:1)
- Generate validation error messages

**Key Methods**:
- `validate_facebook_image(image_path)` → ValidationResult
- `validate_instagram_image(image_path)` → ValidationResult
- `get_image_info(image_path)` → dict (format, size, dimensions)

**Validation Rules**:
- Facebook: JPEG/PNG/GIF, max 4MB, min 200x200px
- Instagram: JPEG/PNG, max 8MB, min 320px width, aspect ratio 4:5 to 1.91:1

#### Module 4: MCP Server (`facebook_instagram_mcp_server.py`)

**Responsibilities**:
- MCP protocol implementation (list_tools, call_tool)
- Tool routing (dispatch to appropriate handler)
- Approval workflow integration (create approval requests)
- Audit logging (log all operations)
- Metrics caching (5-minute TTL)
- Error handling (return structured error responses)

**Key Components**:
- `@app.list_tools()` - Define 9 MCP tools
- `@app.call_tool()` - Route tool calls to handlers
- `create_approval_request()` - Generate approval request files
- `get_audit_logger()` - Lazy initialization of AuditLogger
- `get_meta_client()` - Lazy initialization of MetaGraphClient
- `get_metrics_cache()` - Lazy initialization of metrics cache

**Tool Handlers** (one per MCP tool):
- `facebook_post_text_handler()` - Create approval request, return pending status
- `facebook_post_image_handler()` - Validate image, create approval request
- `instagram_post_image_handler()` - Validate image, create approval request
- `instagram_post_carousel_handler()` - Validate images, create approval request
- `get_facebook_post_metrics_handler()` - Check cache, fetch from API if miss
- `get_instagram_post_metrics_handler()` - Check cache, fetch from API if miss
- `get_facebook_page_insights_handler()` - Fetch from API (no caching)
- `get_instagram_account_insights_handler()` - Fetch from API (no caching)

### Integration Points

#### IP1: Approval Workflow Integration

**Pattern**: Follow `odoo_mcp_server.py` pattern

**Flow**:
1. MCP tool receives write operation request (post, schedule)
2. Validate inputs (image, caption length, etc.)
3. Generate approval request ID (UUID)
4. Create approval request file in `Pending_Approval/`
5. Return pending status to Claude Code
6. Approval executor monitors `Pending_Approval/`
7. On approval: Execute action via MetaGraphClient, move to `Done/`
8. On denial: Log denial, move to `Done/` with denial status

**Approval Request Format**:
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
    "image_path": "/path/to/image.jpg"
  },
  "created_at": "2026-03-18T10:30:00Z",
  "status": "pending"
}
```

#### IP2: Audit Logging Integration

**Pattern**: Follow `email_mcp_server.py` pattern

**Logged Actions**:
- `facebook_post` - Post to Facebook page
- `instagram_post` - Post to Instagram
- `get_facebook_metrics` - Retrieve Facebook metrics
- `get_instagram_metrics` - Retrieve Instagram metrics
- `facebook_page_insights` - Retrieve page insights
- `instagram_account_insights` - Retrieve account insights

**Log Entry Format**:
```python
audit_logger.log_action(
    action_type="facebook_post",
    actor="facebook_instagram_mcp",
    target="page_id_12345",
    parameters={
        "message": "Post content (first 100 chars)...",
        "image_path": "/path/to/image.jpg",
        "approval_id": "approval-fb-post-20260318-123456"
    },
    result="success",
    metadata={
        "post_id": "12345_67890",
        "permalink": "https://facebook.com/..."
    }
)
```

**Sensitive Data Masking**:
- Access tokens: Fully redacted (`***REDACTED***`)
- User IDs: Partially masked (show last 4 digits)
- Image paths: Logged without content

#### IP3: Error Recovery Integration

**Pattern**: Use existing decorators from `scripts/error_recovery/`

**Retry Decorator** (`@with_retry`):
```python
@with_retry(
    max_attempts=3,
    backoff_factor=2.0,
    service_name="meta_graph_api"
)
def post_to_facebook_page(page_id, message):
    # API call here
    pass
```

**Circuit Breaker Decorator** (`@with_circuit_breaker`):
```python
@with_circuit_breaker(
    service_name="meta_graph_api",
    failure_threshold=5,
    recovery_timeout=300
)
def get_post_metrics(post_id):
    # API call here
    pass
```

**Error Handling Flow**:
1. Network error → Retry 3 times with exponential backoff
2. Rate limit error → Queue request, wait for reset
3. Authentication error → Log error, create alert in `Needs_Action/`
4. API error (4xx) → Log error, return structured error response
5. Circuit breaker open → Return cached data if available, else error

### Testing Strategy

#### Unit Tests

**Test Coverage**:
- `test_meta_graph_client.py` - API client methods (mocked API responses)
- `test_rate_limiter.py` - Rate limiting logic (quota tracking, throttling)
- `test_image_validator.py` - Image validation (format, size, dimensions)
- `test_facebook_instagram_mcp_server.py` - MCP tool handlers (mocked dependencies)

**Key Test Cases**:
- Successful post creation (Facebook, Instagram)
- Image validation failures (size, format, aspect ratio)
- Rate limit detection and throttling
- Approval request creation
- Metrics caching (hit, miss, expiry)
- Error handling (network, API, authentication)

#### Integration Tests

**Test Coverage**:
- `test_integration_social_workflow.py` - End-to-end workflows

**Key Test Cases**:
- Email → approval → Facebook post workflow
- Scheduled post workflow (approval → queue → publish)
- Metrics retrieval workflow (cache miss → API call → cache hit)
- Rate limit workflow (throttle → queue → retry)
- Error recovery workflow (network error → retry → success)

#### Contract Tests

**Test Coverage**:
- MCP tool schemas (validate inputSchema against spec)
- Approval request format (validate against approval executor expectations)
- Audit log format (validate against AuditLogger expectations)

### Deployment Considerations

#### Environment Variables

Required in `.env`:
```bash
# Facebook
FACEBOOK_PAGE_ACCESS_TOKEN=your_long_lived_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram
INSTAGRAM_BUSINESS_ACCESS_TOKEN=your_long_lived_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id

# Optional
META_API_VERSION=v19.0
RATE_LIMIT_THRESHOLD=0.8  # Throttle at 80%
METRICS_CACHE_TTL=300  # 5 minutes
```

#### MCP Server Configuration

Add to Claude Code MCP configuration:
```json
{
  "mcpServers": {
    "facebook-instagram": {
      "command": "python",
      "args": ["mcp_servers/facebook_instagram_mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

#### Dependencies

Add to `requirements.txt`:
```
requests>=2.31.0
Pillow>=10.0.0
cachetools>=5.3.0
python-dotenv>=1.0.0
```

---

## Architectural Decisions

### AD1: Synchronous vs Async Implementation

**Decision**: Synchronous implementation using `requests` library

**Rationale**:
- Consistency with existing MCP servers (email, Odoo)
- Simpler error handling and retry logic
- Meta Graph API is rate-limited (not high-volume)
- MCP protocol supports both sync and async

**Trade-offs**:
- Lower throughput (acceptable for rate-limited API)
- Simpler codebase (easier to maintain)

### AD2: In-Memory vs Persistent Rate Limit State

**Decision**: In-memory rate limit tracking

**Rationale**:
- Rate limits reset hourly (short-lived state)
- Simplicity (no file I/O overhead)
- Acceptable to lose state on restart (conservative approach)

**Trade-offs**:
- State lost on restart (acceptable, will re-learn limits)
- No cross-process sharing (acceptable, single MCP server instance)

### AD3: Approval Workflow for All Write Operations

**Decision**: All write operations require approval (no exceptions)

**Rationale**:
- Constitution principle: Safety Before Autonomy
- Social media posts are public and irreversible
- Prevents accidental or inappropriate posts

**Trade-offs**:
- Adds 1-60 minutes latency (acceptable for social media)
- Requires human availability (acceptable, not time-critical)

### AD4: Metrics Caching Strategy

**Decision**: 5-minute TTL cache for engagement metrics

**Rationale**:
- Reduces API calls (rate limit conservation)
- Acceptable staleness for metrics (not real-time critical)
- Invalidate on write operations (maintain consistency)

**Trade-offs**:
- Stale data for up to 5 minutes (acceptable)
- Memory usage (acceptable, limited cache size)

---

## Risk Analysis

### Risk 1: Meta API Rate Limits

**Impact**: High - Posts may be delayed or fail
**Probability**: Medium - Depends on usage volume
**Mitigation**:
- Proactive throttling at 80% capacity
- Queue system for rate-limited requests
- Rate limit monitoring and alerts

### Risk 2: Token Expiration

**Impact**: High - All operations fail until token refreshed
**Probability**: Low - 60-day expiry with manual refresh
**Mitigation**:
- Token validation on startup
- Clear error messages with refresh instructions
- Alert in `Needs_Action/` on token expiration

### Risk 3: Image Upload Failures

**Impact**: Medium - Instagram posts fail (image required)
**Probability**: Medium - Network issues, format issues
**Mitigation**:
- Validation before upload (fail fast)
- Retry logic for network errors
- Clear error messages with validation details

### Risk 4: Approval Workflow Delays

**Impact**: Low - Time-sensitive posts may miss optimal time
**Probability**: High - Depends on user availability
**Mitigation**:
- Scheduling feature (post at specific time)
- Clear approval notifications
- Set expectations (1-60 minutes delay)

### Risk 5: Meta API Changes

**Impact**: Medium - Breaking changes require code updates
**Probability**: Low - Meta provides deprecation notices
**Mitigation**:
- Pin to specific API version (v19.0)
- Monitor Meta changelog
- Comprehensive test suite (detect breaking changes)

---

## Success Criteria

Implementation is complete when:

1. ✅ All 9 MCP tools are implemented and tested
2. ✅ Approval workflow integration works for all write operations
3. ✅ Audit logging captures all operations with sensitive data masking
4. ✅ Rate limiting prevents API limit errors (proactive throttling)
5. ✅ Image validation prevents upload failures (format, size, dimensions)
6. ✅ Metrics caching reduces API calls (5-minute TTL)
7. ✅ Error recovery handles network errors and API failures gracefully
8. ✅ End-to-end tests pass (email → approval → post workflow)
9. ✅ Constitution compliance verified (all principles satisfied)
10. ✅ Documentation complete (quickstart, contracts, data model)

---

## Next Steps

1. **Phase 0 Complete**: Create `research.md` with detailed findings for each research task
2. **Phase 1 Execute**: Create `data-model.md`, `contracts/`, and `quickstart.md`
3. **Phase 1 Complete**: Update agent context with new technologies
4. **Phase 2 Ready**: Run `/sp.tasks` to generate implementation tasks
5. **Implementation**: Run `/sp.implement` to execute tasks with TDD approach

---

**Plan Status**: ✅ Complete - Ready for Phase 0 research
**Next Command**: Continue with Phase 0 research artifact creation
