# Facebook & Instagram Integration

**Skill Name:** post-facebook-instagram
**Category:** Gold Tier - Social Media Management
**MCP Required:** Yes (Social Media MCP Server)

## Purpose

Automatically post content to Facebook and Instagram, monitor engagement, and generate summaries of social media activity for business growth and lead generation.

## Prerequisites

- Facebook Business Account
- Instagram Business Account (linked to Facebook)
- Facebook Graph API access token
- Meta Developer App configured
- Social Media MCP server configured

## Setup

### 1. Create Facebook Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create new app → Business type
3. Add Facebook Login and Instagram Graph API products
4. Get App ID and App Secret

### 2. Get Access Tokens

```bash
# Run authentication helper
uv run python scripts/auth/facebook_auth.py
```

This will:
- Open browser for Facebook OAuth
- Request permissions: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
- Save long-lived access token to `.env`

### 3. Configure MCP Server

Add to `.claude/mcp.json`:

```json
{
  "mcpServers": {
    "social-media": {
      "command": "uv",
      "args": ["run", "python", "mcp_servers/social_media_mcp_server.py"],
      "env": {
        "FB_ACCESS_TOKEN": "${FB_ACCESS_TOKEN}",
        "FB_PAGE_ID": "${FB_PAGE_ID}",
        "IG_ACCOUNT_ID": "${IG_ACCOUNT_ID}"
      }
    }
  }
}
```

### 4. Environment Variables

Add to `.env`:

```bash
FB_ACCESS_TOKEN=your_facebook_access_token
FB_PAGE_ID=your_facebook_page_id
FB_APP_ID=your_app_id
FB_APP_SECRET=your_app_secret
IG_ACCOUNT_ID=your_instagram_business_account_id
IG_ACCESS_TOKEN=your_instagram_access_token
```

## Usage

### Invoke the Skill

```bash
/post-facebook-instagram [action] [options]
```

### Available Actions

1. **Post to Facebook**
   ```
   /post-facebook-instagram post-facebook --message "Check out our new service!" --image "path/to/image.jpg"
   ```

2. **Post to Instagram**
   ```
   /post-facebook-instagram post-instagram --caption "New product launch! 🚀" --image "path/to/image.jpg"
   ```

3. **Post to Both Platforms**
   ```
   /post-facebook-instagram post-both --message "Exciting news!" --image "path/to/image.jpg"
   ```

4. **Generate Engagement Summary**
   ```
   /post-facebook-instagram engagement-summary --period "last-7-days"
   ```

5. **Schedule Post**
   ```
   /post-facebook-instagram schedule --platform "facebook" --message "Weekend special!" --time "2026-03-16T10:00:00Z"
   ```

## Workflow Integration

### Automatic Post Creation from Approved Content

1. Create post draft in `AI_Employee_Vault/Pending_LinkedIn/POST_YYYYMMDD_HHMMSS.md`
2. Claude reviews against Company_Handbook.md guidelines
3. Creates approval request in `Pending_Approval/`
4. Human approves → Post published to Facebook/Instagram
5. Engagement tracked and logged

### Post Template Format

```markdown
---
type: social_media_post
platforms: [facebook, instagram]
scheduled_time: 2026-03-16T10:00:00Z
status: pending_approval
created: 2026-03-14T10:00:00Z
---

## Post Content

Check out our latest service offering! We're helping businesses automate their workflows with AI. 🚀

Learn more: https://example.com/services

## Media

- Image: AI_Employee_Vault/images/service_announcement.jpg
- Alt Text: AI automation service announcement graphic

## Hashtags

#AIAutomation #BusinessGrowth #Productivity #TechInnovation

## Target Audience

- Small business owners
- Entrepreneurs
- Tech enthusiasts

## Call to Action

Visit our website to learn more and schedule a free consultation.
```

## MCP Server Implementation

The Social Media MCP server provides these tools:

```python
# Available MCP Tools
- facebook_post(message, image_url, link, scheduled_time)
- instagram_post(caption, image_url, scheduled_time)
- facebook_get_insights(post_id, metrics)
- instagram_get_insights(post_id, metrics)
- get_engagement_summary(platform, start_date, end_date)
- schedule_post(platform, content, publish_time)
- delete_post(platform, post_id)
```

## Approval Workflow

All social media posts require approval:

```markdown
---
type: approval_request
action: social_media_post
platforms: [facebook, instagram]
created: 2026-03-14T10:00:00Z
expires: 2026-03-15T10:00:00Z
status: pending
---

## Post Preview

**Message:** Check out our latest service offering! 🚀

**Image:** service_announcement.jpg

**Platforms:** Facebook, Instagram

**Scheduled:** 2026-03-16 10:00 AM

## Engagement Prediction

Based on past performance:
- Expected reach: 500-800 people
- Expected engagement: 30-50 interactions
- Best posting time: ✅ (10 AM weekday)

## To Approve

Move this file to `/Approved` folder.

## To Reject

Move this file to `/Rejected` folder.
```

## Engagement Tracking

### Automatic Summary Generation

Daily summary created at 8 PM:

```markdown
# Social Media Summary - 2026-03-14

## Facebook Performance

- **Posts Today:** 2
- **Total Reach:** 1,234 people
- **Engagement Rate:** 4.2%
- **Top Post:** "New service announcement" (523 reach, 45 reactions)

## Instagram Performance

- **Posts Today:** 2
- **Total Reach:** 856 people
- **Engagement Rate:** 6.8%
- **Top Post:** "Behind the scenes" (412 reach, 58 likes)

## Insights

- ✅ Instagram engagement up 15% from last week
- ⚠️ Facebook reach down 8% - consider posting earlier
- 💡 Posts with images get 3x more engagement

## Recommendations

1. Post to Instagram between 11 AM - 1 PM for best reach
2. Use more video content on Facebook
3. Increase hashtag usage on Instagram (currently 3, optimal is 8-12)
```

## Integration with Weekly Audit

The weekly business audit automatically includes:

1. Total social media reach and engagement
2. Lead generation from social posts
3. Top performing content
4. Follower growth trends
5. Recommendations for next week

## Content Guidelines

From `Company_Handbook.md`:

```markdown
## Social Media Posting Rules

### Allowed (Auto-Approve)
- Business updates and announcements
- Educational content related to services
- Client success stories (with permission)
- Industry news and insights
- Behind-the-scenes content

### Requires Approval
- Promotional offers and discounts
- Controversial or political topics
- Client testimonials
- Partnership announcements
- Any content mentioning competitors

### Never Post
- Personal opinions on sensitive topics
- Unverified information
- Client data without explicit consent
- Negative comments about competitors
- Content violating platform guidelines
```

## Error Handling

- **API Rate Limit:** Queue posts, retry after limit resets
- **Invalid Access Token:** Alert user, pause posting
- **Image Upload Failed:** Retry 3 times, then post text-only
- **Post Rejected by Platform:** Create alert with rejection reason
- **Scheduled Post Failed:** Attempt immediate posting, alert user

## Security

- Never commit access tokens
- Rotate tokens every 60 days
- Use short-lived tokens for testing
- Implement IP whitelist for API access
- Monitor for unauthorized access

## Logging

All social media operations logged to `AI_Employee_Vault/Logs/social_media_YYYYMMDD.log`:

```json
{
  "timestamp": "2026-03-14T10:30:00Z",
  "action": "post_published",
  "platform": "facebook",
  "post_id": "123456789",
  "message": "Check out our new service!",
  "reach": 0,
  "engagement": 0,
  "approval_status": "approved",
  "result": "success"
}
```

## Analytics Dashboard

Create `AI_Employee_Vault/Dashboard_Social_Media.md`:

```markdown
# Social Media Dashboard

**Last Updated:** 2026-03-14 20:00

## This Week's Performance

| Platform  | Posts | Reach  | Engagement | Followers |
|-----------|-------|--------|------------|-----------|
| Facebook  | 5     | 3,421  | 4.2%       | +12       |
| Instagram | 5     | 2,856  | 6.8%       | +23       |

## Top Performing Posts

1. "New service launch" - 1,234 reach, 89 engagements
2. "Client success story" - 987 reach, 67 engagements
3. "Industry insights" - 756 reach, 54 engagements

## Upcoming Scheduled Posts

- 2026-03-15 10:00 AM - "Weekend special offer"
- 2026-03-16 02:00 PM - "Behind the scenes video"
```

## Troubleshooting

**Q: Posts not appearing on Facebook**
- Verify page permissions
- Check if page is published (not in draft mode)
- Ensure access token has `pages_manage_posts` permission

**Q: Instagram posting fails**
- Confirm account is Instagram Business (not Personal)
- Verify image meets Instagram requirements (aspect ratio, size)
- Check if account is linked to Facebook page

**Q: Engagement data not updating**
- Insights have 24-48 hour delay
- Verify access token has insights permissions
- Check if post is public (not private)

## References

- [Facebook Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api)
- [Meta Business Suite](https://business.facebook.com)

## Example: Complete Posting Flow

```bash
# 1. Create post draft
# File: Pending_LinkedIn/POST_20260314_service_announcement.md

# 2. Review and approve
/post-facebook-instagram post-both --file "POST_20260314_service_announcement.md"

# 3. Claude creates approval request
# File: Pending_Approval/SOCIAL_POST_20260314.md

# 4. Human approves
# Move to: Approved/

# 5. Post published to both platforms
# Confirmation: Done/SOCIAL_POST_20260314.md

# 6. Track engagement
# Automatic updates every 6 hours to Dashboard_Social_Media.md
```

## Gold Tier Completion Criteria

- ✅ Facebook Business Account configured
- ✅ Instagram Business Account linked
- ✅ MCP server configured and tested
- ✅ Can post to Facebook via Claude Code
- ✅ Can post to Instagram via Claude Code
- ✅ Engagement tracking automated
- ✅ Daily summaries generated
- ✅ Integration with weekly audit
- ✅ Approval workflow implemented
