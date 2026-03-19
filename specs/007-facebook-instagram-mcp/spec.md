# Feature Specification: Facebook & Instagram MCP Server

**Feature ID:** 007-facebook-instagram-mcp
**Created:** 2026-03-18
**Status:** Draft
**Priority:** P1 (Gold Tier - Module 3)

---

## Overview

Create an MCP (Model Context Protocol) server that integrates with Meta Graph API to enable social media posting and engagement tracking for Facebook pages and Instagram business accounts. The server exposes 8 MCP tools (4 write, 4 read) for posting content, retrieving engagement metrics, scheduling posts with approval workflow, and handling rate limits gracefully.

---

## User Scenarios & Testing

### P1: Post to Facebook Page

**As a** business owner
**I want to** post content to my Facebook page via AI Employee
**So that** I can maintain social media presence without manual posting

**Acceptance Scenarios:**

1. **Successful text post**
   - Given: Valid Facebook page access token
   - When: AI Employee posts "New product launch today!"
   - Then: Post appears on Facebook page with correct content
   - And: Audit log records the action
   - And: Dashboard shows post confirmation

2. **Post with image**
   - Given: Valid access token and image file
   - When: AI Employee posts text with attached image
   - Then: Post appears with image correctly displayed
   - And: Image is uploaded to Facebook CDN
   - And: Post ID is returned for tracking

3. **Post requires approval**
   - Given: Approval workflow is enabled
   - When: AI Employee attempts to post
   - Then: Approval request is created in Pending_Approval/
   - And: Post is not published until approved
   - And: Approval executor publishes after approval

**Edge Cases:**
- Invalid access token → Error logged, retry with token refresh
- Image too large (>4MB) → Error message, suggest compression
- Rate limit exceeded → Queue post, retry after cooldown
- Network timeout → Retry with exponential backoff

---

### P1: Post to Instagram Business Account

**As a** business owner
**I want to** post content to my Instagram business account
**So that** I can engage with customers on Instagram

**Acceptance Scenarios:**

1. **Successful image post**
   - Given: Valid Instagram business account access token
   - When: AI Employee posts image with caption
   - Then: Post appears on Instagram feed
   - And: Caption is correctly formatted
   - And: Post ID is returned

2. **Post with hashtags**
   - Given: Caption includes hashtags
   - When: AI Employee posts to Instagram
   - Then: Hashtags are clickable and functional
   - And: Post is discoverable via hashtags

3. **Post requires approval**
   - Given: Approval workflow is enabled
   - When: AI Employee attempts to post
   - Then: Approval request is created
   - And: Post is not published until approved

**Edge Cases:**
- Image missing → Error, Instagram requires image
- Caption too long (>2200 chars) → Truncate with warning
- Invalid hashtag format → Auto-correct or warn
- Account not business account → Error with instructions

---

### P2: Retrieve Engagement Metrics

**As a** business owner
**I want to** track engagement metrics for my posts
**So that** I can measure social media performance

**Acceptance Scenarios:**

1. **Get post engagement**
   - Given: Valid post ID
   - When: AI Employee retrieves engagement metrics
   - Then: Returns likes, comments, shares counts
   - And: Returns reach and impressions
   - And: Data is cached for 5 minutes

2. **Get page insights**
   - Given: Valid Facebook page ID
   - When: AI Employee retrieves page insights
   - Then: Returns follower count, engagement rate
   - And: Returns top performing posts
   - And: Data is formatted for weekly audit

3. **Get Instagram insights**
   - Given: Valid Instagram business account ID
   - When: AI Employee retrieves insights
   - Then: Returns follower growth, engagement rate
   - And: Returns top posts by engagement

**Edge Cases:**
- Post too recent (no metrics yet) → Return partial data with note
- Metrics API unavailable → Return cached data if available
- Invalid post ID → Error with clear message

---

### P2: Schedule Posts with Approval Workflow

**As a** business owner
**I want to** schedule posts in advance with approval
**So that** I can plan content calendar and maintain quality control

**Acceptance Scenarios:**

1. **Schedule Facebook post**
   - Given: Valid content and future timestamp
   - When: AI Employee schedules post
   - Then: Approval request is created
   - And: Post is queued for scheduled time
   - And: Post publishes at scheduled time after approval

2. **Schedule Instagram post**
   - Given: Valid image, caption, and future timestamp
   - When: AI Employee schedules post
   - Then: Approval request is created
   - And: Post is queued with image stored temporarily
   - And: Post publishes at scheduled time after approval

3. **Cancel scheduled post**
   - Given: Scheduled post exists
   - When: User requests cancellation
   - Then: Post is removed from queue
   - And: Audit log records cancellation

**Edge Cases:**
- Scheduled time in past → Error, suggest current time
- Approval denied → Post is not published, user notified
- Scheduled time during rate limit → Auto-adjust to next available slot

---

### P3: Handle Rate Limits Gracefully

**As a** system administrator
**I want to** handle Meta API rate limits gracefully
**So that** the system remains stable and posts are not lost

**Acceptance Scenarios:**

1. **Rate limit detection**
   - Given: API returns rate limit error
   - When: AI Employee detects rate limit
   - Then: Post is queued for retry
   - And: Retry occurs after cooldown period
   - And: User is notified of delay

2. **Exponential backoff**
   - Given: Multiple rate limit errors
   - When: AI Employee retries
   - Then: Retry delay increases exponentially
   - And: Maximum retry attempts is 5
   - And: User is notified after max retries

3. **Rate limit monitoring**
   - Given: API returns rate limit headers
   - When: AI Employee makes requests
   - Then: Remaining quota is tracked
   - And: Requests are throttled proactively
   - And: Dashboard shows rate limit status

**Edge Cases:**
- Rate limit during scheduled post → Auto-reschedule to next available slot
- Persistent rate limit (24+ hours) → Alert user, suggest manual intervention
- Multiple accounts hitting rate limits → Queue per account

---

## Functional Requirements

### FR1: Facebook Posting

**FR1.1:** MCP tool `facebook_post_text` accepts parameters:
- `page_id` (required): Facebook page ID
- `message` (required): Post content (max 63,206 characters)
- `link` (optional): URL to attach
- `scheduled_time` (optional): ISO 8601 timestamp for scheduling

**FR1.2:** MCP tool `facebook_post_image` accepts parameters:
- `page_id` (required): Facebook page ID
- `message` (required): Post caption
- `image_path` (required): Local path to image file
- `scheduled_time` (optional): ISO 8601 timestamp

**FR1.3:** All Facebook write operations require approval workflow integration

**FR1.4:** Returns post ID, permalink, and creation timestamp on success

---

### FR2: Instagram Posting

**FR2.1:** MCP tool `instagram_post_image` accepts parameters:
- `account_id` (required): Instagram business account ID
- `caption` (required): Post caption (max 2,200 characters)
- `image_path` (required): Local path to image file
- `scheduled_time` (optional): ISO 8601 timestamp

**FR2.2:** MCP tool `instagram_post_carousel` accepts parameters:
- `account_id` (required): Instagram business account ID
- `caption` (required): Post caption
- `image_paths` (required): Array of image paths (2-10 images)
- `scheduled_time` (optional): ISO 8601 timestamp

**FR2.3:** All Instagram write operations require approval workflow integration

**FR2.4:** Returns media ID, permalink, and creation timestamp on success

---

### FR3: Engagement Metrics

**FR3.1:** MCP tool `get_facebook_post_metrics` accepts parameters:
- `post_id` (required): Facebook post ID
- `metrics` (optional): Array of metrics to retrieve (default: all)
  - Available: likes, comments, shares, reactions, reach, impressions

**FR3.2:** MCP tool `get_instagram_post_metrics` accepts parameters:
- `media_id` (required): Instagram media ID
- `metrics` (optional): Array of metrics to retrieve (default: all)
  - Available: likes, comments, saves, reach, impressions, engagement_rate

**FR3.3:** MCP tool `get_facebook_page_insights` accepts parameters:
- `page_id` (required): Facebook page ID
- `period` (optional): Time period (day, week, month) - default: week
- `metrics` (optional): Array of metrics (default: all)

**FR3.4:** MCP tool `get_instagram_account_insights` accepts parameters:
- `account_id` (required): Instagram business account ID
- `period` (optional): Time period (day, week, month) - default: week

**FR3.5:** Metrics are cached for 5 minutes to reduce API calls

---

### FR4: Authentication & Authorization

**FR4.1:** Access tokens are stored in `.env` file:
- `FACEBOOK_PAGE_ACCESS_TOKEN`: Long-lived page access token
- `INSTAGRAM_BUSINESS_ACCESS_TOKEN`: Long-lived access token

**FR4.2:** MCP server validates tokens on startup

**FR4.3:** Token refresh is attempted automatically on authentication errors

**FR4.4:** Invalid or expired tokens trigger alert in Needs_Action/

---

### FR5: Approval Workflow Integration

**FR5.1:** All write operations (post, schedule) create approval requests in `AI_Employee_Vault/Pending_Approval/`

**FR5.2:** Approval request includes:
- Action type (facebook_post, instagram_post)
- Content preview (text, image thumbnail)
- Target account (page_id or account_id)
- Scheduled time (if applicable)
- Risk level (low, medium, high)

**FR5.3:** Approval executor monitors Pending_Approval/ and executes approved actions

**FR5.4:** Denied approvals are logged and user is notified

---

### FR6: Rate Limiting & Error Recovery

**FR6.1:** Rate limit detection:
- Parse `X-App-Usage` and `X-Business-Use-Case-Usage` headers
- Track remaining quota per endpoint
- Proactively throttle when quota < 20%

**FR6.2:** Retry strategy:
- Network errors: Retry 3 times with exponential backoff (1s, 2s, 4s)
- Rate limit errors: Queue and retry after cooldown (header-specified or 1 hour)
- Authentication errors: Attempt token refresh, then retry once

**FR6.3:** Circuit breaker pattern:
- Open circuit after 5 consecutive failures
- Half-open after 5 minutes
- Close circuit after 3 successful requests

**FR6.4:** Graceful degradation:
- Queue posts when API unavailable
- Return cached metrics when API unavailable
- Alert user of degraded service

---

### FR7: Audit Logging

**FR7.1:** All operations are logged via audit logging system:
- Action type (facebook_post, instagram_post, get_metrics)
- Actor (mcp_server, approval_executor)
- Target (page_id, account_id, post_id)
- Parameters (with sensitive data masked)
- Result (success, failure)
- Error details (if applicable)

**FR7.2:** Sensitive data masking:
- Access tokens are fully redacted
- User IDs are partially masked (show last 4 digits)
- Image paths are logged without content

**FR7.3:** Audit logs are searchable by action type, target, and date range

---

### FR8: Image Upload & Formatting

**FR8.1:** Supported image formats: JPEG, PNG, GIF (non-animated for Instagram)

**FR8.2:** Image validation:
- Facebook: Max 4MB, min 200x200px
- Instagram: Max 8MB, aspect ratio 4:5 to 1.91:1, min 320px width

**FR8.3:** Image upload process:
- Validate format and size
- Upload to Meta CDN
- Receive media ID
- Attach to post

**FR8.4:** Image upload errors are logged with specific validation failure reason

---

### FR9: Post Formatting

**FR9.1:** Facebook post formatting:
- Preserve line breaks
- Auto-link URLs
- Support @mentions (page tags)
- Support hashtags

**FR9.2:** Instagram post formatting:
- Preserve line breaks
- Support @mentions (user tags)
- Support hashtags (max 30)
- First comment for additional hashtags (if caption > 2200 chars)

**FR9.3:** Emoji support for both platforms

---

## Security & Compliance

### SEC1: Access Token Security

- Access tokens stored in `.env` (not committed to git)
- Tokens are never logged (masked in audit logs)
- Token refresh uses secure OAuth2 flow
- Expired tokens trigger immediate alert

### SEC2: Approval Workflow

- All write operations require approval (no exceptions)
- Approval requests include risk assessment
- High-risk actions (e.g., posting to multiple accounts) require explicit approval
- Approval denials are logged with reason

### SEC3: Data Privacy

- User data (comments, engagement) is not stored permanently
- Metrics are cached for 5 minutes only
- Image uploads are deleted after posting
- Audit logs comply with GDPR (90-day retention)

---

## Success Criteria

### Measurable Outcomes

1. **Posting Success Rate:** 95% of approved posts are published successfully within 1 minute of approval
2. **Rate Limit Handling:** 100% of rate-limited requests are queued and retried successfully
3. **Approval Workflow:** 100% of write operations require approval before execution
4. **Metrics Accuracy:** Engagement metrics match Meta Business Suite within 5% margin
5. **Error Recovery:** 90% of transient errors (network, timeout) are recovered automatically
6. **Audit Completeness:** 100% of operations are logged in audit system
7. **Image Upload Success:** 95% of valid images are uploaded successfully on first attempt
8. **Scheduled Posts:** 95% of scheduled posts are published within 1 minute of scheduled time

### Qualitative Outcomes

- Users can post to Facebook and Instagram without leaving Claude Code
- Social media engagement is tracked automatically in weekly audits
- Approval workflow prevents accidental or inappropriate posts
- Rate limits do not cause post failures or data loss
- Error messages are clear and actionable

---

## Key Entities

### Post
- **Attributes:** post_id, platform (facebook/instagram), content, media_urls, scheduled_time, status (pending/approved/published/failed), created_at, published_at
- **Relationships:** Belongs to Account, has many Metrics

### Account
- **Attributes:** account_id, platform (facebook_page/instagram_business), name, access_token, rate_limit_quota, last_post_time
- **Relationships:** Has many Posts

### Metrics
- **Attributes:** metric_id, post_id, metric_type (likes/comments/shares/reach/impressions), value, timestamp
- **Relationships:** Belongs to Post

### ApprovalRequest
- **Attributes:** request_id, action_type, target_account, content_preview, risk_level, status (pending/approved/denied), created_at, resolved_at
- **Relationships:** References Post (if approved)

---

## Assumptions

1. **Meta Graph API Access:** User has valid Facebook page and Instagram business account with API access enabled
2. **Long-Lived Tokens:** User provides long-lived access tokens (60-day expiry) that can be refreshed
3. **Business Accounts:** Instagram account is converted to business account (required for API access)
4. **Image Storage:** Local filesystem has sufficient space for temporary image storage during upload
5. **Network Connectivity:** System has stable internet connection for API calls
6. **Approval Latency:** Approval workflow adds 1-60 minutes delay (acceptable for social media posting)
7. **Rate Limits:** Meta API rate limits are sufficient for typical small business usage (200 posts/day)
8. **Scheduling Precision:** Scheduled posts within 1-minute precision is acceptable (not real-time)

---

## Dependencies

### External Dependencies
- **Meta Graph API:** v19.0 or later
- **Facebook Page:** Active page with admin access
- **Instagram Business Account:** Active account linked to Facebook page
- **Access Tokens:** Valid long-lived tokens with required permissions

### Internal Dependencies
- **Approval Executor:** Monitors Pending_Approval/ and executes approved actions
- **Audit Logger:** Logs all operations with sensitive data masking
- **Error Recovery System:** Provides retry patterns and circuit breaker
- **Dashboard:** Displays post confirmations and engagement metrics

### Permissions Required
- Facebook: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
- Instagram: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`

---

## Out of Scope

- **Video Posting:** Not included in initial implementation (future enhancement)
- **Stories:** Facebook/Instagram stories not supported (future enhancement)
- **Direct Messages:** Responding to comments/DMs not supported
- **Ad Management:** Creating/managing paid ads not supported
- **Multi-Account Management:** Single page/account per platform (future enhancement)
- **Analytics Dashboard:** Detailed analytics UI not included (data available via weekly audit)
- **Content Calendar UI:** Visual calendar interface not included (scheduling via CLI only)
- **Image Editing:** No built-in image editing (use external tools)
- **Hashtag Suggestions:** No AI-powered hashtag recommendations (user provides hashtags)

---

## Risks & Mitigations

### Risk 1: API Rate Limits
- **Impact:** Posts may be delayed or fail
- **Probability:** Medium (depends on usage volume)
- **Mitigation:** Proactive throttling, queue system, rate limit monitoring

### Risk 2: Token Expiration
- **Impact:** All operations fail until token refreshed
- **Probability:** Low (60-day expiry with auto-refresh)
- **Mitigation:** Token validation on startup, auto-refresh, immediate alerts

### Risk 3: Meta API Changes
- **Impact:** Breaking changes require code updates
- **Probability:** Low (Meta provides deprecation notices)
- **Mitigation:** Pin to specific API version, monitor Meta changelog

### Risk 4: Image Upload Failures
- **Impact:** Posts fail if image required (Instagram)
- **Probability:** Medium (network issues, format issues)
- **Mitigation:** Validation before upload, retry logic, clear error messages

### Risk 5: Approval Workflow Delays
- **Impact:** Time-sensitive posts may miss optimal posting time
- **Probability:** High (depends on user availability)
- **Mitigation:** Scheduling feature, approval notifications, clear SLA expectations

---

## Future Enhancements

1. **Video Support:** Post videos to Facebook and Instagram (Reels)
2. **Stories:** Post to Facebook/Instagram stories with 24-hour expiry
3. **Comment Management:** Respond to comments via AI Employee
4. **Multi-Account:** Manage multiple pages/accounts per platform
5. **Analytics Dashboard:** Visual dashboard for engagement metrics
6. **Content Calendar:** Visual calendar interface for scheduling
7. **Hashtag Suggestions:** AI-powered hashtag recommendations
8. **Image Editing:** Built-in image cropping, filters, text overlay
9. **A/B Testing:** Test multiple post variations
10. **Competitor Analysis:** Track competitor posts and engagement

---

## Notes

- This specification focuses on WHAT the system should do, not HOW to implement it
- Technical implementation details (Python libraries, API client architecture) will be defined in the plan phase
- All write operations require approval to prevent accidental or inappropriate posts
- Rate limiting is critical for Meta API compliance and system stability
- Audit logging ensures compliance and debugging capability
