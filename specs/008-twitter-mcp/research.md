# Research: Twitter MCP Server

**Feature**: 008-twitter-mcp
**Date**: 2026-03-19
**Purpose**: Document technology decisions and best practices for Twitter API v2 integration

---

## R1: Twitter API v2 Integration with Tweepy

### Question
What are the best practices for integrating Twitter API v2 using Tweepy library?

### Research Findings

**Tweepy v4.14+ Features**:
- Native support for Twitter API v2 endpoints
- OAuth 1.0a authentication (required for posting tweets)
- OAuth 2.0 authentication (for read-only operations)
- Built-in rate limit handling with automatic waiting
- Pagination support for large result sets
- Media upload via API v1.1 endpoint (still required for images)

**Authentication Pattern**:
```python
import tweepy

# OAuth 1.0a for read/write access
auth = tweepy.OAuth1UserHandler(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Create API v2 client
client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

# Create API v1.1 client for media upload
api = tweepy.API(auth)
```

**Best Practices**:
1. Use `tweepy.Client` for API v2 operations (tweets, threads, mentions)
2. Use `tweepy.API` for media uploads (still on v1.1)
3. Enable `wait_on_rate_limit=True` for automatic rate limit handling
4. Catch `tweepy.TweepyException` for all API errors
5. Use `tweet_fields` parameter to request specific data (metrics, author info)
6. Implement exponential backoff for transient failures

**Media Upload Pattern**:
```python
# Upload media via API v1.1
media = api.media_upload(filename="image.jpg")

# Post tweet with media via API v2
client.create_tweet(text="Hello!", media_ids=[media.media_id])
```

### Decision

**Use Tweepy v4.14+ with dual client pattern**:
- `tweepy.Client` for API v2 operations (tweets, threads, mentions, metrics)
- `tweepy.API` for media uploads (v1.1 endpoint)
- OAuth 1.0a authentication for read/write access
- Built-in rate limit handling with `wait_on_rate_limit=True`

**Rationale**:
- Official library with active maintenance
- Simplifies authentication and request signing
- Built-in rate limit handling reduces custom code
- Dual client pattern handles media upload limitation

---

## R2: Twitter Rate Limiting Strategy

### Question
How should we handle Twitter's strict rate limits (50 tweets/24h for free tier)?

### Research Findings

**Twitter API v2 Rate Limits (Free Tier)**:
- Tweet creation: 50 tweets per 24 hours
- User lookup: 300 requests per 15 minutes
- Tweet lookup: 300 requests per 15 minutes
- User mentions: 180 requests per 15 minutes
- Rate limit headers: `x-rate-limit-limit`, `x-rate-limit-remaining`, `x-rate-limit-reset`

**Rate Limit Response**:
- HTTP 429 "Too Many Requests"
- Response includes `x-rate-limit-reset` timestamp
- Tweepy can automatically wait if `wait_on_rate_limit=True`

**Proactive Throttling Strategy**:
1. Track remaining quota per endpoint
2. Throttle at 80% capacity (e.g., stop at 40/50 tweets)
3. Queue requests during cooldown period
4. Display clear error messages to users
5. Log rate limit events for monitoring

**Queue-Based Approach**:
- Maintain in-memory queue of pending tweets
- Process queue when quota available
- Persist queue to disk for crash recovery
- Priority queue for urgent tweets

### Decision

**Implement proactive throttling with queue-based management**:
- Track rate limits per endpoint using response headers
- Throttle at 80% capacity (40/50 tweets, 240/300 lookups)
- Queue tweets during cooldown period
- Use Tweepy's `wait_on_rate_limit=True` as fallback
- Log all rate limit events to audit system
- Display quota usage in dashboard

**Rationale**:
- Prevents hitting hard limits that block all operations
- Provides better user experience with clear feedback
- Queue ensures no tweets are lost during rate limits
- Monitoring enables quota management

**Implementation**:
```python
class TwitterRateLimiter:
    def __init__(self, threshold=0.8):
        self.limits = {}  # endpoint -> {limit, remaining, reset}
        self.threshold = threshold

    def check_limit(self, endpoint):
        if endpoint in self.limits:
            limit_info = self.limits[endpoint]
            if limit_info['remaining'] < limit_info['limit'] * self.threshold:
                raise RateLimitException(f"Approaching rate limit for {endpoint}")

    def update_from_headers(self, endpoint, headers):
        self.limits[endpoint] = {
            'limit': int(headers.get('x-rate-limit-limit', 0)),
            'remaining': int(headers.get('x-rate-limit-remaining', 0)),
            'reset': int(headers.get('x-rate-limit-reset', 0))
        }
```

---

## R3: Thread Creation Patterns

### Question
What is the optimal approach for creating tweet threads with proper linking?

### Research Findings

**Twitter Thread Mechanics**:
- Threads created by replying to previous tweet
- Use `in_reply_to_tweet_id` parameter
- Each tweet must wait for previous tweet ID
- Thread numbering convention: "1/n", "2/n", etc.
- Maximum 25 tweets per thread (API limit)

**Thread Creation Pattern**:
```python
# Post first tweet
response1 = client.create_tweet(text="Thread 1/3: First tweet")
tweet1_id = response1.data['id']

# Reply to first tweet
response2 = client.create_tweet(
    text="Thread 2/3: Second tweet",
    in_reply_to_tweet_id=tweet1_id
)
tweet2_id = response2.data['id']

# Reply to second tweet
response3 = client.create_tweet(
    text="Thread 3/3: Third tweet",
    in_reply_to_tweet_id=tweet2_id
)
```

**Error Handling**:
- If any tweet fails, entire thread is incomplete
- Options: rollback (delete posted tweets) or continue with partial thread
- Rollback requires storing tweet IDs for deletion
- Partial threads confuse users and break narrative

**Thread Numbering**:
- Add numbering automatically: "1/5", "2/5", etc.
- Calculate total before posting
- Prepend or append to user's text
- Convention: append at end (e.g., "Tweet text (1/5)")

### Decision

**Implement atomic thread creation with automatic numbering**:
- Calculate total tweets before posting
- Add numbering to each tweet (format: "text (n/total)")
- Post tweets sequentially, tracking IDs
- If any tweet fails, delete all posted tweets (rollback)
- Return all tweet IDs on success, error on failure
- Maximum 25 tweets per thread

**Rationale**:
- Atomic operation prevents confusing partial threads
- Automatic numbering improves user experience
- Rollback maintains data consistency
- Clear error messages help users fix issues

**Implementation**:
```python
def create_thread(tweets):
    total = len(tweets)
    if total > 25:
        raise ValueError("Thread exceeds 25 tweet limit")

    posted_ids = []
    try:
        for i, text in enumerate(tweets):
            numbered_text = f"{text} ({i+1}/{total})"

            if i == 0:
                response = client.create_tweet(text=numbered_text)
            else:
                response = client.create_tweet(
                    text=numbered_text,
                    in_reply_to_tweet_id=posted_ids[-1]
                )

            posted_ids.append(response.data['id'])

        return posted_ids

    except Exception as e:
        # Rollback: delete all posted tweets
        for tweet_id in posted_ids:
            try:
                client.delete_tweet(tweet_id)
            except:
                pass  # Log but don't fail rollback
        raise e
```

---

## R4: Approval Workflow Integration

### Question
How should Twitter actions integrate with existing approval workflow?

### Research Findings

**Existing Approval Workflow Pattern** (from Facebook/Instagram MCP):
1. MCP tool creates approval request file in `Pending_Approval/`
2. File contains YAML frontmatter with metadata
3. User moves file to `Approved/` folder
4. `approval_executor.py` monitors `Approved/` folder
5. Executor calls action function with metadata
6. Result logged to audit system
7. File moved to `Done/` folder

**Approval Request Schema**:
```yaml
---
approval_id: SOCIAL_TWITTER_POST_TWEET_20260319_000001
action_type: twitter_post_tweet
email_action_ref: social_media_post
action_params:
  platform: twitter
  post_type: tweet
risk_assessment: low
reasoning: Posting announcement tweet about product launch
created_at: 2026-03-19T10:30:00Z
metadata:
  text: "Excited to announce our new product! 🚀"
  image_paths: ["/path/to/image.jpg"]
  scheduled_time: null
---
```

**Action Execution Pattern**:
```python
def execute_twitter_post_tweet(approval_id, metadata):
    """Called by approval_executor.py after approval"""
    try:
        # Extract parameters
        text = metadata['text']
        image_paths = metadata.get('image_paths', [])

        # Upload images if present
        media_ids = []
        for path in image_paths:
            media = api.media_upload(path)
            media_ids.append(media.media_id)

        # Post tweet
        response = client.create_tweet(
            text=text,
            media_ids=media_ids if media_ids else None
        )

        # Log to audit system
        audit_logger.log_action(
            action_type="twitter_post_tweet",
            actor="ai_employee",
            target=f"tweet_{response.data['id']}",
            parameters=metadata,
            result={"tweet_id": response.data['id']},
            approval=approval_id
        )

        return {
            "status": "success",
            "tweet_id": response.data['id']
        }

    except Exception as e:
        audit_logger.log_action(
            action_type="twitter_post_tweet",
            actor="ai_employee",
            target="twitter",
            parameters=metadata,
            error=str(e),
            approval=approval_id
        )
        return {"status": "error", "error": str(e)}
```

**Integration Points**:
1. MCP server creates approval requests
2. `approval_executor.py` needs Twitter action handlers
3. Action handlers use `twitter_client.py` for API calls
4. All actions logged via `audit_logger.py`
5. Error recovery decorators applied to action handlers

### Decision

**Follow existing approval workflow pattern with Twitter-specific handlers**:
- MCP tools create approval requests in `Pending_Approval/`
- Use YAML frontmatter schema matching Facebook/Instagram pattern
- Add Twitter action handlers to `approval_executor.py`
- Action handlers call `twitter_client.py` methods
- All actions logged via existing `audit_logger.py`
- Apply error recovery decorators to handlers

**Rationale**:
- Maintains consistency across social media integrations
- Reuses proven approval workflow infrastructure
- Minimal changes to existing systems
- Clear separation of concerns (MCP server vs executor)

**Required Changes**:
1. Add Twitter action handlers to `approval_executor.py`:
   - `execute_twitter_post_tweet()`
   - `execute_twitter_post_thread()`
2. Update approval request schema validation
3. Add Twitter-specific error handling
4. Update audit logger action types

---

## Technology Stack Summary

### Core Dependencies
- **Tweepy v4.14+**: Twitter API v2 client library
- **Pillow**: Image validation (reuse existing)
- **python-dotenv**: Environment variables (existing)
- **mcp**: MCP protocol server (existing)

### Architecture Patterns
- **Dual Client Pattern**: `tweepy.Client` (v2) + `tweepy.API` (v1.1 for media)
- **Proactive Throttling**: 80% capacity threshold with queue management
- **Atomic Threads**: All-or-none posting with automatic rollback
- **Approval Workflow**: File-based state transitions (existing pattern)

### Integration Points
- `approval_executor.py`: Add Twitter action handlers
- `audit_logger.py`: Log all Twitter actions
- `error_recovery/`: Apply retry/circuit breaker decorators
- `image_validator.py`: Reuse for Twitter images (5MB limit)

---

## Open Questions Resolved

All research questions have been answered:
- ✅ R1: Tweepy integration pattern defined
- ✅ R2: Rate limiting strategy decided
- ✅ R3: Thread creation approach finalized
- ✅ R4: Approval workflow integration clarified

No remaining NEEDS CLARIFICATION items.

---

## Next Steps

1. Create data-model.md with entity definitions
2. Create contracts/ with MCP tool schemas
3. Create quickstart.md with setup instructions
4. Update agent context with Twitter technologies
5. Proceed to `/sp.tasks` for implementation tasks
