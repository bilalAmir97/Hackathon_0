# Twitter (X) Integration

**Skill Name:** post-twitter
**Category:** Gold Tier - Social Media Management
**MCP Required:** Yes (Twitter MCP Server)

## Purpose

Automatically post content to Twitter/X, monitor engagement, track mentions, and generate summaries of Twitter activity for brand building and lead generation.

## Prerequisites

- Twitter/X Developer Account
- Twitter API v2 access (Essential or higher)
- OAuth 2.0 credentials configured
- Twitter MCP server configured

## Setup

### 1. Create Twitter Developer App

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create new project and app
3. Enable OAuth 2.0 with Read and Write permissions
4. Get API Key, API Secret, Bearer Token

### 2. Get Access Tokens

```bash
# Run authentication helper
uv run python scripts/auth/twitter_auth.py
```

This will:
- Open browser for Twitter OAuth 2.0
- Request permissions: `tweet.read`, `tweet.write`, `users.read`
- Save access token and refresh token to `.env`

### 3. Configure MCP Server

Add to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "twitter": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/twitter_mcp_server.py"],
      "env": {
        "TWITTER_API_KEY": "${TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_SECRET": "${TWITTER_ACCESS_SECRET}",
        "TWITTER_BEARER_TOKEN": "${TWITTER_BEARER_TOKEN}"
      }
    }
  }
}
```

### 4. Environment Variables

Add to `.env`:

```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_USER_ID=your_user_id
```

## Usage

### Invoke the Skill

```bash
/post-twitter [action] [options]
```

### Available Actions

1. **Post Tweet**
   ```
   /post-twitter post --message "Excited to share our new AI automation service! 🚀"
   ```

2. **Post Thread**
   ```
   /post-twitter thread --file "AI_Employee_Vault/Pending_LinkedIn/THREAD_automation_tips.md"
   ```

3. **Post with Media**
   ```
   /post-twitter post --message "Check this out!" --image "path/to/image.jpg"
   ```

4. **Reply to Mention**
   ```
   /post-twitter reply --tweet-id "123456789" --message "Thanks for reaching out!"
   ```

5. **Get Engagement Summary**
   ```
   /post-twitter engagement-summary --period "last-7-days"
   ```

6. **Monitor Mentions**
   ```
   /post-twitter monitor-mentions --keywords "AI automation, business automation"
   ```

## Workflow Integration

### Automatic Tweet Creation

1. Create tweet draft in `AI_Employee_Vault/Pending_LinkedIn/TWEET_YYYYMMDD_HHMMSS.md`
2. Claude reviews against Company_Handbook.md guidelines
3. Creates approval request in `Pending_Approval/`
4. Human approves → Tweet published
5. Engagement tracked and logged

### Tweet Template Format

```markdown
---
type: twitter_post
tweet_type: single  # or 'thread'
scheduled_time: 2026-03-16T10:00:00Z
status: pending_approval
created: 2026-03-14T10:00:00Z
---

## Tweet Content

🚀 Excited to announce our new AI Employee automation service!

We help businesses automate workflows with Claude Code + custom agents.

✅ 24/7 operation
✅ 85% cost savings
✅ Instant deployment

Learn more: https://example.com/ai-employee

#AIAutomation #BusinessGrowth #Productivity

## Media

- Image: AI_Employee_Vault/images/ai_employee_announcement.jpg
- Alt Text: AI Employee automation service announcement

## Target Audience

- Tech entrepreneurs
- Small business owners
- Productivity enthusiasts
- AI/ML community

## Engagement Strategy

- Post at 10 AM EST (peak engagement time)
- Use 3-4 relevant hashtags
- Include clear call-to-action
- Tag relevant accounts if applicable
```

### Thread Template Format

```markdown
---
type: twitter_thread
thread_length: 5
status: pending_approval
created: 2026-03-14T10:00:00Z
---

## Thread: 5 Ways AI Employees Transform Your Business

### Tweet 1/5

🧵 5 ways AI Employees are transforming small businesses in 2026:

From email management to accounting, here's what's possible with autonomous agents.

👇 Thread

### Tweet 2/5

1️⃣ Email Triage & Response

Your AI Employee monitors Gmail 24/7, categorizes emails, drafts responses, and flags urgent items.

Result: 3 hours saved daily, zero missed opportunities.

### Tweet 3/5

2️⃣ Social Media Management

Automatically posts to LinkedIn, Facebook, Instagram, and Twitter based on your content calendar.

Result: Consistent presence without manual effort.

### Tweet 4/5

3️⃣ Financial Management

Integrates with Odoo for invoicing, expense tracking, and financial reporting.

Result: Real-time visibility into business health.

### Tweet 5/5

4️⃣ Client Communication

Monitors WhatsApp for urgent keywords, creates action items, and ensures timely responses.

Result: Improved client satisfaction and retention.

Want to build your own AI Employee? Check out our guide: https://example.com

#AIAutomation #BusinessGrowth
```

## MCP Server Implementation

The Twitter MCP server provides these tools:

```python
# Available MCP Tools
- twitter_post(text, media_ids, reply_to_id)
- twitter_post_thread(tweets_list)
- twitter_upload_media(image_path, alt_text)
- twitter_get_mentions(since_id, max_results)
- twitter_reply(tweet_id, text)
- twitter_get_tweet_metrics(tweet_id)
- twitter_search_tweets(query, max_results)
- twitter_get_user_timeline(user_id, max_results)
- twitter_delete_tweet(tweet_id)
```

## Approval Workflow

All tweets require approval:

```markdown
---
type: approval_request
action: twitter_post
tweet_type: single
created: 2026-03-14T10:00:00Z
expires: 2026-03-15T10:00:00Z
status: pending
---

## Tweet Preview

🚀 Excited to announce our new AI Employee automation service!

We help businesses automate workflows with Claude Code + custom agents.

✅ 24/7 operation
✅ 85% cost savings
✅ Instant deployment

Learn more: https://example.com/ai-employee

#AIAutomation #BusinessGrowth #Productivity

**Character Count:** 267/280 ✅

## Media

- Image: ai_employee_announcement.jpg (preview attached)

## Engagement Prediction

Based on past performance:
- Expected impressions: 800-1,200
- Expected engagement rate: 2-4%
- Best posting time: ✅ (10 AM EST weekday)

## Compliance Check

- ✅ No sensitive information
- ✅ Follows brand guidelines
- ✅ Appropriate hashtags
- ✅ Clear call-to-action

## To Approve

Move this file to `/Approved` folder.

## To Reject

Move this file to `/Rejected` folder.
```

## Mention Monitoring

### Automatic Mention Detection

Twitter watcher monitors mentions every 5 minutes:

```python
# watchers/twitter_watcher.py
MONITOR_KEYWORDS = [
    "AI automation",
    "business automation",
    "@your_handle",
    "Claude Code"
]

# Creates action items for:
# - Direct mentions
# - Keyword matches
# - Questions about services
# - Potential leads
```

### Mention Action Item

```markdown
---
type: twitter_mention
tweet_id: 123456789
author: @potential_client
created: 2026-03-14T10:30:00Z
priority: high
status: needs_response
---

## Mention Details

**From:** @potential_client (2.3K followers)
**Tweet:** "Looking for AI automation solutions for my business. Anyone have recommendations?"

**Context:** Potential lead asking for recommendations

## Suggested Response

"Hi @potential_client! We specialize in AI automation for businesses. Our AI Employee solution handles email, social media, accounting, and more. Would love to chat about your needs. DM us or check out: https://example.com"

## Action Required

- [ ] Review suggested response
- [ ] Approve or modify
- [ ] Send reply
- [ ] Follow up via DM if interested
```

## Engagement Tracking

### Daily Twitter Summary

Generated at 8 PM daily:

```markdown
# Twitter Summary - 2026-03-14

## Today's Performance

- **Tweets Posted:** 3
- **Total Impressions:** 2,456
- **Engagement Rate:** 3.2%
- **Profile Visits:** 45
- **New Followers:** +8

## Top Performing Tweet

"5 ways AI Employees transform your business 🧵"
- Impressions: 1,234
- Engagements: 67 (5.4% rate)
- Retweets: 12
- Likes: 45
- Replies: 10

## Mentions & Interactions

- **Mentions:** 5 (3 responded, 2 pending)
- **Potential Leads:** 2
- **Questions:** 1 (answered)

## Insights

- ✅ Thread format performed 2x better than single tweets
- ✅ Morning posts (10 AM) get 40% more engagement
- ⚠️ Hashtag usage could be optimized (currently 2-3, optimal is 3-5)

## Recommendations

1. Post more threads (higher engagement)
2. Increase visual content (images/videos)
3. Engage more with mentions within 1 hour
4. Use Twitter Spaces for live Q&A
```

## Integration with Weekly Audit

The weekly business audit automatically includes:

1. Total Twitter impressions and engagement
2. Follower growth and demographics
3. Top performing content
4. Lead generation from Twitter
5. Mention response time
6. Recommendations for next week

## Content Guidelines

From `Company_Handbook.md`:

```markdown
## Twitter Posting Rules

### Allowed (Auto-Approve)
- Business updates and product launches
- Industry insights and tips
- Retweets of relevant content
- Responses to mentions (non-controversial)
- Educational threads

### Requires Approval
- Promotional offers
- Partnership announcements
- Controversial topics
- Direct competitor mentions
- Political or social commentary

### Never Post
- Personal attacks or negative comments
- Unverified information or rumors
- Client data without consent
- Spam or excessive self-promotion
- Content violating Twitter ToS
```

## Error Handling

- **API Rate Limit:** Queue tweets, retry after 15-minute window
- **Duplicate Tweet:** Add timestamp or emoji to make unique
- **Media Upload Failed:** Retry 3 times, then post text-only
- **Authentication Error:** Alert user, refresh access token
- **Tweet Rejected:** Create alert with rejection reason

## Security

- Never commit API keys or tokens
- Rotate access tokens every 90 days
- Use OAuth 2.0 with PKCE
- Monitor for unauthorized access
- Implement rate limiting on client side

## Logging

All Twitter operations logged to `AI_Employee_Vault/Logs/twitter_YYYYMMDD.log`:

```json
{
  "timestamp": "2026-03-14T10:30:00Z",
  "action": "tweet_posted",
  "tweet_id": "123456789",
  "text": "Excited to announce...",
  "impressions": 0,
  "engagement": 0,
  "approval_status": "approved",
  "result": "success"
}
```

## Analytics Dashboard

Create `AI_Employee_Vault/Dashboard_Twitter.md`:

```markdown
# Twitter Dashboard

**Last Updated:** 2026-03-14 20:00

## This Week's Performance

| Metric          | This Week | Last Week | Change  |
|-----------------|-----------|-----------|---------|
| Tweets          | 15        | 12        | +25%    |
| Impressions     | 12,456    | 10,234    | +22%    |
| Engagement Rate | 3.2%      | 2.8%      | +14%    |
| Followers       | +45       | +32       | +41%    |

## Top Performing Tweets

1. "AI automation thread" - 2,345 impressions, 5.4% engagement
2. "Client success story" - 1,876 impressions, 4.2% engagement
3. "Industry insights" - 1,234 impressions, 3.8% engagement

## Upcoming Scheduled Tweets

- 2026-03-15 10:00 AM - "Weekend productivity tips"
- 2026-03-16 02:00 PM - "Behind the scenes video"
- 2026-03-17 11:00 AM - "New feature announcement"
```

## Troubleshooting

**Q: Tweets not posting**
- Verify API credentials are valid
- Check if account is suspended or restricted
- Ensure tweet meets character limit (280 chars)
- Verify media file size and format

**Q: Mentions not being detected**
- Confirm bearer token has read permissions
- Check if mention monitoring is running (PM2 status)
- Verify webhook is configured correctly

**Q: Engagement data not updating**
- Twitter metrics have 24-hour delay
- Verify API access level (Essential vs Elevated)
- Check rate limits haven't been exceeded

## References

- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
- [Twitter API Rate Limits](https://developer.twitter.com/en/docs/twitter-api/rate-limits)

## Example: Complete Tweet Flow

```bash
# 1. Create tweet draft
# File: Pending_LinkedIn/TWEET_20260314_announcement.md

# 2. Review and approve
/post-twitter post --file "TWEET_20260314_announcement.md"

# 3. Claude creates approval request
# File: Pending_Approval/TWITTER_POST_20260314.md

# 4. Human approves
# Move to: Approved/

# 5. Tweet published
# Confirmation: Done/TWITTER_POST_20260314.md

# 6. Track engagement
# Automatic updates every 6 hours to Dashboard_Twitter.md
```

## Gold Tier Completion Criteria

- ✅ Twitter Developer Account configured
- ✅ API v2 access enabled
- ✅ MCP server configured and tested
- ✅ Can post tweets via Claude Code
- ✅ Can post threads via Claude Code
- ✅ Mention monitoring automated
- ✅ Daily summaries generated
- ✅ Integration with weekly audit
- ✅ Approval workflow implemented
- ✅ Lead tracking from mentions
