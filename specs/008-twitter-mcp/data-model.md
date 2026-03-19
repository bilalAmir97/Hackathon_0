# Data Model: Twitter MCP Server

**Feature**: 008-twitter-mcp
**Date**: 2026-03-19
**Purpose**: Define data entities and their relationships for Twitter integration

---

## Core Entities

### Tweet

Represents a single tweet posted to Twitter.

**Fields**:
- `tweet_id` (string, required): Unique Twitter tweet identifier (e.g., "1234567890123456789")
- `text` (string, required): Tweet content (max 280 characters)
- `author_id` (string, required): Twitter user ID of tweet author
- `created_at` (datetime, required): Tweet creation timestamp (ISO 8601)
- `media_ids` (array of strings, optional): IDs of attached media (max 4)
- `in_reply_to_tweet_id` (string, optional): ID of tweet this is replying to (for threads)
- `metrics` (Metrics object, optional): Engagement metrics

**Validation Rules**:
- `text` must be 1-280 characters
- `media_ids` array max length: 4
- `tweet_id` must match Twitter ID format (numeric string)
- `created_at` must be valid ISO 8601 datetime

**State Transitions**:
- Created → Posted (via Twitter API)
- Posted → Deleted (via delete API, not implemented in v1)

**Example**:
```json
{
  "tweet_id": "1234567890123456789",
  "text": "Excited to announce our new product! 🚀",
  "author_id": "9876543210987654321",
  "created_at": "2026-03-19T10:30:00Z",
  "media_ids": ["1111111111111111111"],
  "in_reply_to_tweet_id": null,
  "metrics": {
    "likes": 42,
    "retweets": 15,
    "replies": 8,
    "impressions": 1250
  }
}
```

---

### Thread

Represents a collection of tweets linked as a thread.

**Fields**:
- `thread_id` (string, required): Unique thread identifier (generated, format: "thread_YYYYMMDD_HHMMSS")
- `tweet_ids` (array of strings, required): Ordered list of tweet IDs in thread
- `created_at` (datetime, required): Thread creation timestamp
- `total_tweets` (integer, required): Number of tweets in thread
- `status` (string, required): Thread status ("pending", "posted", "failed", "partial")

**Validation Rules**:
- `tweet_ids` array length: 2-25 (Twitter limit)
- `total_tweets` must equal `tweet_ids.length`
- `status` must be one of: "pending", "posted", "failed", "partial"
- All `tweet_ids` must be valid Twitter ID format

**State Transitions**:
- pending → posted (all tweets successfully posted)
- pending → failed (error before any tweets posted)
- pending → partial (some tweets posted, then error - triggers rollback)

**Example**:
```json
{
  "thread_id": "thread_20260319_103000",
  "tweet_ids": [
    "1234567890123456789",
    "1234567890123456790",
    "1234567890123456791"
  ],
  "created_at": "2026-03-19T10:30:00Z",
  "total_tweets": 3,
  "status": "posted"
}
```

---

### Mention

Represents a tweet that mentions the authenticated user's account.

**Fields**:
- `mention_id` (string, required): Unique mention identifier (same as tweet_id)
- `tweet_id` (string, required): ID of tweet containing mention
- `author_id` (string, required): Twitter user ID who mentioned us
- `author_username` (string, required): Twitter username who mentioned us
- `text` (string, required): Full text of mention tweet
- `created_at` (datetime, required): Mention timestamp
- `conversation_id` (string, optional): ID of conversation thread

**Validation Rules**:
- `mention_id` equals `tweet_id`
- `text` must contain "@" + our username
- `created_at` must be within last 7 days (API limit)

**Example**:
```json
{
  "mention_id": "1234567890123456789",
  "tweet_id": "1234567890123456789",
  "author_id": "9876543210987654321",
  "author_username": "customer_user",
  "text": "@our_account Great product! When is the next release?",
  "created_at": "2026-03-19T09:15:00Z",
  "conversation_id": "1234567890123456780"
}
```

---

### Metrics

Represents engagement metrics for a tweet.

**Fields**:
- `likes` (integer, required): Number of likes (formerly favorites)
- `retweets` (integer, required): Number of retweets
- `replies` (integer, required): Number of replies
- `impressions` (integer, optional): Number of times tweet was viewed
- `engagement_rate` (float, optional): Calculated engagement rate (likes + retweets + replies) / impressions
- `cached_at` (datetime, required): When metrics were last fetched (for cache TTL)

**Validation Rules**:
- All counts must be >= 0
- `engagement_rate` must be 0.0-1.0 if present
- `cached_at` must be recent (within 5 minutes for cache validity)

**Calculations**:
- `engagement_rate` = (likes + retweets + replies) / impressions (if impressions > 0)

**Example**:
```json
{
  "likes": 42,
  "retweets": 15,
  "replies": 8,
  "impressions": 1250,
  "engagement_rate": 0.052,
  "cached_at": "2026-03-19T10:35:00Z"
}
```

---

### ApprovalRequest

Represents a pending action requiring human approval.

**Fields**:
- `approval_id` (string, required): Unique approval identifier (format: "SOCIAL_TWITTER_{ACTION}_{TIMESTAMP}")
- `action_type` (string, required): Type of action ("twitter_post_tweet", "twitter_post_thread")
- `email_action_ref` (string, required): Reference to email action type ("social_media_post")
- `action_params` (object, required): Action-specific parameters
  - `platform` (string): "twitter"
  - `post_type` (string): "tweet" or "thread"
- `risk_assessment` (string, required): Risk level ("low", "medium", "high")
- `reasoning` (string, required): Human-readable explanation of action
- `created_at` (datetime, required): When approval request was created
- `metadata` (object, required): Action-specific data (see below)

**Metadata for twitter_post_tweet**:
- `text` (string, required): Tweet text (max 280 chars)
- `image_paths` (array of strings, optional): Local paths to images (max 4)
- `scheduled_time` (datetime, optional): When to post (null for immediate)

**Metadata for twitter_post_thread**:
- `tweets` (array of strings, required): Array of tweet texts (2-25 items)
- `image_paths` (array of strings, optional): Local paths to images for specific tweets
- `scheduled_time` (datetime, optional): When to post thread

**Validation Rules**:
- `approval_id` must match format pattern
- `action_type` must be valid Twitter action
- `risk_assessment` must be "low", "medium", or "high"
- `metadata` must match schema for `action_type`

**State Transitions**:
- Created (in Pending_Approval/)
- Approved (moved to Approved/)
- Executed (moved to Done/)
- Rejected (moved to Rejected/)

**Example (Tweet)**:
```yaml
---
approval_id: SOCIAL_TWITTER_POST_TWEET_20260319_103000
action_type: twitter_post_tweet
email_action_ref: social_media_post
action_params:
  platform: twitter
  post_type: tweet
risk_assessment: low
reasoning: Posting product announcement tweet with image
created_at: 2026-03-19T10:30:00Z
metadata:
  text: "Excited to announce our new product! 🚀"
  image_paths: ["/path/to/product.jpg"]
  scheduled_time: null
---
```

**Example (Thread)**:
```yaml
---
approval_id: SOCIAL_TWITTER_POST_THREAD_20260319_103000
action_type: twitter_post_thread
email_action_ref: social_media_post
action_params:
  platform: twitter
  post_type: thread
risk_assessment: low
reasoning: Posting product launch announcement thread
created_at: 2026-03-19T10:30:00Z
metadata:
  tweets:
    - "Big announcement coming! 🎉"
    - "We're launching our new product today!"
    - "Check it out at our website!"
  image_paths: ["/path/to/product.jpg"]
  scheduled_time: null
---
```

---

## Entity Relationships

```
ApprovalRequest (1) --creates--> (1) Tweet
ApprovalRequest (1) --creates--> (1) Thread
Thread (1) --contains--> (2-25) Tweet
Tweet (1) --has--> (0-1) Metrics
Tweet (1) --replies-to--> (0-1) Tweet (for threads)
Mention (1) --is-a--> (1) Tweet
```

**Relationship Rules**:
- One approval request creates one tweet OR one thread
- One thread contains 2-25 tweets
- Each tweet can have metrics (fetched separately)
- Tweets in thread are linked via `in_reply_to_tweet_id`
- Mentions are tweets that reference our account

---

## Data Storage

### File-Based Storage (Approval Workflow)
- **Location**: `AI_Employee_Vault/Pending_Approval/`, `Approved/`, `Done/`
- **Format**: Markdown with YAML frontmatter
- **Naming**: `SOCIAL_TWITTER_{ACTION}_{TIMESTAMP}.md`

### In-Memory Storage (Runtime)
- **Metrics Cache**: Dictionary keyed by tweet_id, TTL 5 minutes
- **Rate Limit State**: Dictionary keyed by endpoint, updated per request
- **Thread State**: Temporary storage during thread creation

### Audit Logs (Persistent)
- **Location**: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
- **Format**: JSON lines (one JSON object per line)
- **Retention**: 90 days minimum

---

## Data Flow

### Tweet Posting Flow
1. MCP tool receives request → validates text/images
2. Creates ApprovalRequest entity → writes to Pending_Approval/
3. User approves → file moved to Approved/
4. Executor reads ApprovalRequest → extracts metadata
5. Uploads images → gets media_ids
6. Posts tweet → gets Tweet entity from API
7. Logs to audit system → writes Tweet data
8. Moves approval to Done/

### Thread Creation Flow
1. MCP tool receives thread request → validates tweets array
2. Creates ApprovalRequest entity → writes to Pending_Approval/
3. User approves → file moved to Approved/
4. Executor reads ApprovalRequest → extracts tweets array
5. Creates Thread entity (status: pending)
6. Posts tweets sequentially → collects tweet_ids
7. Updates Thread entity (status: posted)
8. Logs to audit system → writes Thread data
9. Moves approval to Done/

### Mentions Monitoring Flow
1. MCP tool receives mentions request → checks cache
2. If cache miss → calls Twitter API
3. Receives Mention entities → caches for 5 minutes
4. Returns Mention array to caller
5. Logs retrieval to audit system

### Metrics Retrieval Flow
1. MCP tool receives metrics request → checks cache
2. If cache miss → calls Twitter API
3. Receives Metrics entity → caches for 5 minutes
4. Returns Metrics to caller
5. Logs retrieval to audit system

---

## Cache Management

### Metrics Cache
- **Key**: tweet_id
- **Value**: Metrics object with cached_at timestamp
- **TTL**: 5 minutes
- **Eviction**: LRU (Least Recently Used)
- **Max Size**: 100 entries

### Rate Limit Cache
- **Key**: endpoint (e.g., "tweets", "mentions")
- **Value**: {limit, remaining, reset_timestamp}
- **TTL**: Until reset_timestamp
- **Update**: After each API call (from response headers)

---

## Error Handling

### Validation Errors
- Invalid tweet text length → Return error before approval
- Invalid image format → Return error before approval
- Thread too long (>25 tweets) → Return error before approval

### API Errors
- Rate limit exceeded → Queue request, return error with retry time
- Authentication failure → Log error, return clear message
- Network timeout → Retry with exponential backoff
- Duplicate tweet → Return error with suggestion

### Partial Failures
- Thread creation fails mid-thread → Rollback (delete posted tweets)
- Image upload fails → Post text-only tweet OR return error (configurable)
- Metrics unavailable → Return cached data OR zeros with note

---

## Data Validation

All entities must pass validation before:
- Creating approval requests
- Posting to Twitter API
- Storing in cache
- Writing to audit logs

Validation enforced by:
- Pydantic models (type checking, constraints)
- Custom validators (business logic)
- API client (pre-flight checks)

---

## Next Steps

1. Create JSON schemas in contracts/ directory
2. Implement Pydantic models for each entity
3. Create validation functions
4. Implement cache management
5. Test data flow end-to-end
