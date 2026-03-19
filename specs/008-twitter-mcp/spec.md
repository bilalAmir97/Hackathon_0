# Feature Specification: Twitter MCP Server

**Feature ID:** 008-twitter-mcp
**Created:** 2026-03-19
**Status:** Draft
**Priority:** P1 (Gold Tier - Module 3, Task 3.2)

---

## Overview

Create an MCP (Model Context Protocol) server that integrates with Twitter API v2 to enable tweet posting, thread creation, mentions monitoring, and engagement tracking. The server exposes MCP tools for posting tweets, creating threads, retrieving mentions, and tracking engagement metrics, all integrated with the approval workflow system.

---

## User Scenarios & Testing

### P1: Post Tweet

**As a** business owner
**I want to** post tweets via AI Employee
**So that** I can maintain Twitter presence without manual posting

**Acceptance Scenarios:**

1. **Successful text tweet**
   - Given: Valid Twitter API credentials
   - When: AI Employee posts "Excited to announce our new product! 🚀"
   - Then: Tweet appears on Twitter timeline
   - And: Tweet ID is returned for tracking
   - And: Audit log records the action
   - And: Dashboard shows tweet confirmation

2. **Tweet with image**
   - Given: Valid credentials and image file (PNG/JPG/GIF)
   - When: AI Employee posts tweet with attached image
   - Then: Tweet appears with image correctly displayed
   - And: Image is uploaded to Twitter media endpoint
   - And: Tweet ID is returned

3. **Tweet with multiple images**
   - Given: Valid credentials and 2-4 images
   - When: AI Employee posts tweet with multiple images
   - Then: All images appear in tweet
   - And: Images are displayed in correct order

4. **Tweet requires approval**
   - Given: Approval workflow is enabled
   - When: AI Employee attempts to post tweet
   - Then: Approval request is created in Pending_Approval/
   - And: Tweet is not published until approved
   - And: Approval executor publishes after approval

**Edge Cases:**
- Tweet exceeds 280 characters → Error message with character count
- Invalid credentials → Error logged, suggest credential refresh
- Image too large (>5MB) → Error message, suggest compression
- Rate limit exceeded → Queue tweet, retry after cooldown
- Duplicate tweet → Error message, suggest modification

---

### P2: Create Tweet Thread

**As a** content creator
**I want to** create multi-tweet threads
**So that** I can share longer-form content on Twitter

**Acceptance Scenarios:**

1. **Successful thread creation**
   - Given: Valid credentials and array of tweet texts
   - When: AI Employee creates thread with 3 tweets
   - Then: All 3 tweets are posted in sequence
   - And: Each tweet replies to the previous one
   - And: Thread numbering is added (1/3, 2/3, 3/3)
   - And: All tweet IDs are returned

2. **Thread with images**
   - Given: Thread with images in some tweets
   - When: AI Employee creates thread
   - Then: Images appear in correct tweets
   - And: Thread structure is maintained

3. **Thread requires approval**
   - Given: Approval workflow enabled
   - When: AI Employee attempts to create thread
   - Then: Single approval request created for entire thread
   - And: All tweets published together after approval

**Edge Cases:**
- Thread exceeds 25 tweets → Error message with limit
- One tweet in thread fails → Rollback or continue with error log
- Rate limit hit mid-thread → Pause and resume after cooldown

---

### P3: Monitor Mentions

**As a** social media manager
**I want to** monitor mentions of my Twitter account
**So that** I can respond to customer inquiries and engagement

**Acceptance Scenarios:**

1. **Retrieve recent mentions**
   - Given: Valid credentials
   - When: AI Employee requests mentions from last 24 hours
   - Then: List of mentions is returned
   - And: Each mention includes: tweet ID, author, text, timestamp
   - And: Mentions are sorted by recency

2. **Filter mentions by engagement**
   - Given: Mentions exist with varying engagement
   - When: AI Employee requests high-engagement mentions (>10 likes)
   - Then: Only mentions meeting criteria are returned

**Edge Cases:**
- No mentions found → Return empty list with success status
- Rate limit on mentions endpoint → Use cached data if available

---

### P4: Track Engagement Metrics

**As a** business owner
**I want to** track engagement metrics for my tweets
**So that** I can measure social media performance

**Acceptance Scenarios:**

1. **Get tweet metrics**
   - Given: Valid tweet ID
   - When: AI Employee requests metrics
   - Then: Metrics returned include: likes, retweets, replies, impressions
   - And: Metrics are cached for 5 minutes

2. **Get account metrics**
   - Given: Valid credentials
   - When: AI Employee requests account metrics
   - Then: Metrics include: follower count, tweet count, engagement rate

**Edge Cases:**
- Tweet too recent (no metrics yet) → Return zeros with note
- Metrics API unavailable → Use cached data if available

---

## Functional Requirements

### FR1: Tweet Posting

**FR1.1** System shall post text tweets up to 280 characters
**FR1.2** System shall post tweets with 1-4 images (PNG, JPG, GIF)
**FR1.3** System shall validate image size (max 5MB per image)
**FR1.4** System shall validate image format before upload
**FR1.5** System shall return tweet ID after successful post
**FR1.6** System shall support hashtags and @mentions in tweets
**FR1.7** System shall create approval request before posting

### FR2: Thread Creation

**FR2.1** System shall create threads with 2-25 tweets
**FR2.2** System shall automatically number tweets (1/n format)
**FR2.3** System shall link tweets in reply chain
**FR2.4** System shall support images in thread tweets
**FR2.5** System shall handle thread creation atomically (all or none)
**FR2.6** System shall return all tweet IDs in thread

### FR3: Mentions Monitoring

**FR3.1** System shall retrieve mentions from last 7 days
**FR3.2** System shall filter mentions by date range (ISO 8601 format, max 7 days per API constraint)
**FR3.3** System shall include author info for each mention
**FR3.4** System shall sort mentions by recency
**FR3.5** System shall cache mentions for 5 minutes

### FR4: Engagement Metrics

**FR4.1** System shall retrieve tweet metrics (likes, retweets, replies, impressions)
**FR4.2** System shall retrieve account metrics (followers, tweets)
**FR4.3** System shall cache metrics for 5 minutes
**FR4.4** System shall handle metrics unavailability gracefully

### FR5: Rate Limiting

**FR5.1** System shall track Twitter API rate limits
**FR5.2** System shall throttle requests at 80% capacity
**FR5.3** System shall implement circuit breaker for sustained failures
**FR5.4** System shall queue requests during rate limit cooldown
**FR5.5** System shall log rate limit events

### FR6: Error Handling

**FR6.1** System shall retry failed requests with exponential backoff
**FR6.2** System shall log all errors with context
**FR6.3** System shall return user-friendly error messages
**FR6.4** System shall handle authentication failures gracefully
**FR6.5** System shall create health alerts for critical failures

### FR7: Audit Logging

**FR7.1** System shall log all tweet posts with tweet ID
**FR7.2** System shall log all thread creations
**FR7.3** System shall log all API errors
**FR7.4** System shall include timestamps in all logs
**FR7.5** System shall integrate with existing AuditLogger

---

## Success Criteria

1. **Tweet Posting**: Users can successfully post tweets via approval workflow with 95% success rate (measured over 100 tweet attempts in 30-day period)
2. **Thread Creation**: Users can create threads of up to 25 tweets with proper linking
3. **Mentions Monitoring**: System retrieves mentions within 5 minutes of posting
4. **Engagement Tracking**: Metrics retrieved within 1 second (cached data up to 5 minutes old)
5. **Rate Limit Compliance**: System never exceeds Twitter API rate limits
6. **Error Recovery**: 90% of transient failures recover automatically within 3 retries
7. **Audit Completeness**: 100% of Twitter actions are logged in audit system
8. **Approval Integration**: All tweets require and respect approval workflow

---

## Key Entities

### Tweet
- **tweet_id** (string): Unique Twitter tweet identifier
- **text** (string): Tweet content (max 280 chars)
- **author_id** (string): Twitter user ID of author
- **created_at** (datetime): Tweet creation timestamp
- **media_ids** (array): IDs of attached media
- **metrics** (object): Engagement metrics (likes, retweets, replies, impressions)

### Thread
- **thread_id** (string): Unique thread identifier
- **tweet_ids** (array): Ordered list of tweet IDs in thread
- **created_at** (datetime): Thread creation timestamp
- **total_tweets** (integer): Number of tweets in thread

### Mention
- **mention_id** (string): Unique mention identifier
- **tweet_id** (string): ID of tweet containing mention
- **author_id** (string): User who mentioned us
- **text** (string): Mention text
- **created_at** (datetime): Mention timestamp

### Metrics
- **likes** (integer): Number of likes
- **retweets** (integer): Number of retweets
- **replies** (integer): Number of replies
- **impressions** (integer): Number of impressions
- **engagement_rate** (float): Calculated engagement rate

---

## Constraints

### Technical Constraints
- Twitter API v2 rate limits: 50 tweets per 24 hours (free tier)
- Tweet character limit: 280 characters
- Image limit: 4 images per tweet, 5MB each
- Thread limit: 25 tweets per thread
- Mentions retrieval: Last 7 days only
- Poll duration: 5 minutes to 7 days

### Business Constraints
- All tweets require approval before posting
- Audit logging is mandatory for compliance
- Rate limiting must prevent quota exhaustion
- Error recovery must handle transient failures

### Integration Constraints
- Must integrate with existing approval workflow
- Must use existing AuditLogger
- Must follow MCP protocol specification
- Must use Tweepy library for Twitter API

---

## Dependencies

### External Dependencies
- Twitter API v2 (requires developer account and API keys)
- Tweepy Python library (v4.14+)
- Twitter Developer Portal access for credentials

### Internal Dependencies
- Approval workflow system (AI_Employee_Vault/)
- Audit logging system (scripts/audit_logger.py)
- Error recovery system (retry, circuit breaker)
- MCP server infrastructure

---

## Assumptions

1. Twitter developer account is already created
2. API keys and access tokens are available
3. Twitter account is set up and accessible
4. Approval workflow system is operational
5. Audit logging system is functional
6. Error recovery infrastructure exists
7. Users understand Twitter's 280 character limit
8. Free tier rate limits are acceptable for initial deployment

---

## Out of Scope

- Twitter Spaces integration
- Direct message functionality
- Twitter Lists management
- Advanced analytics and reporting
- Automated tweet scheduling (beyond approval workflow)
- Tweet editing (not supported by Twitter API v2 free tier)
- Twitter Ads integration
- Multi-account management
- Real-time streaming of timeline
- Tweet deletion or archiving

---

## Risks & Mitigations

### Risk 1: Twitter API Rate Limits
**Impact:** High - Could block all Twitter functionality
**Probability:** Medium
**Mitigation:**
- Implement proactive throttling at 80% capacity
- Queue requests during cooldown
- Cache metrics and mentions
- Monitor rate limit usage

### Risk 2: API Authentication Failures
**Impact:** High - Prevents all Twitter operations
**Probability:** Low
**Mitigation:**
- Implement token refresh logic
- Log authentication errors clearly
- Provide setup verification script
- Document credential management

### Risk 3: Thread Creation Failures
**Impact:** Medium - Partial threads could confuse users
**Probability:** Medium
**Mitigation:**
- Implement atomic thread creation (all or none)
- Log partial thread state
- Provide rollback mechanism
- Retry failed tweets in thread

### Risk 4: Image Upload Failures
**Impact:** Medium - Tweets post without images
**Probability:** Medium
**Mitigation:**
- Validate images before upload
- Retry image uploads separately
- Log image upload errors
- Provide clear error messages

---

## Open Questions

None - All requirements are clear and testable.

---

## Acceptance Criteria

- [ ] Can post text tweets via approval workflow
- [ ] Can post tweets with images (1-4 images)
- [ ] Can create threads with automatic numbering
- [ ] Can retrieve mentions from last 7 days
- [ ] Can get engagement metrics for tweets
- [ ] All actions logged in audit system
- [ ] Rate limiting prevents quota exhaustion
- [ ] Error recovery handles transient failures
- [ ] All tests passing (unit + integration)
- [ ] Documentation complete (setup guide, API reference)
