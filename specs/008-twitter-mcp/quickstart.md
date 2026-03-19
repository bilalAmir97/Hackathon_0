# Twitter MCP Server - Quickstart Guide

**Feature**: 008-twitter-mcp
**Date**: 2026-03-19
**Purpose**: Get started with Twitter integration in 15 minutes

---

## Prerequisites

- Twitter account (personal or business)
- Python 3.10+ installed
- AI Employee system running (Silver Tier minimum)
- Text editor for configuration

---

## Step 1: Create Twitter Developer Account

### 1.1 Sign Up for Developer Access

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Click "Sign up" or "Apply for access"
3. Log in with your Twitter account
4. Complete the application form:
   - **Use case**: "Building an AI assistant for social media management"
   - **Will you make Twitter content available to government entities?**: No
   - Accept terms and conditions
5. Verify your email address
6. Wait for approval (usually instant for free tier)

### 1.2 Create a Twitter App

1. Go to [Developer Portal Dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Click "Create Project" or "Create App"
3. Fill in app details:
   - **App name**: "AI Employee Twitter Integration"
   - **Description**: "Personal AI assistant for managing Twitter presence"
   - **Website URL**: Your website or `https://example.com`
   - **Callback URL**: `http://localhost` (not used, but required)
4. Click "Create"

---

## Step 2: Generate API Keys

### 2.1 Get API Keys and Secrets

1. In your app dashboard, go to "Keys and tokens" tab
2. Under "Consumer Keys", click "Generate" or view existing keys:
   - **API Key** (also called Consumer Key)
   - **API Secret** (also called Consumer Secret)
3. **IMPORTANT**: Copy these immediately - you won't see them again!

### 2.2 Generate Access Tokens

1. Scroll down to "Authentication Tokens" section
2. Click "Generate" under "Access Token and Secret"
3. Copy both:
   - **Access Token**
   - **Access Token Secret**
4. **IMPORTANT**: Save these securely - they won't be shown again!

### 2.3 Set App Permissions

1. Go to "Settings" tab in your app dashboard
2. Under "App permissions", click "Edit"
3. Select "Read and Write" (required for posting tweets)
4. Click "Save"
5. **IMPORTANT**: Regenerate access tokens after changing permissions!

---

## Step 3: Configure Environment Variables

### 3.1 Add Twitter Credentials to .env

Open your `.env` file in the project root and add:

```bash
# Twitter Configuration (Gold Tier - Module 3, Task 3.2)
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Twitter API Configuration
TWITTER_API_VERSION=2
TWITTER_RATE_LIMIT_THRESHOLD=0.8
TWITTER_METRICS_CACHE_TTL=300
```

### 3.2 Replace Placeholder Values

Replace the placeholder values with your actual credentials:
- `your_api_key_here` → Your API Key from Step 2.1
- `your_api_secret_here` → Your API Secret from Step 2.1
- `your_access_token_here` → Your Access Token from Step 2.2
- `your_access_token_secret_here` → Your Access Token Secret from Step 2.2

### 3.3 Verify .env is in .gitignore

**CRITICAL**: Ensure `.env` is in your `.gitignore` file to prevent credential leaks!

```bash
# Check if .env is ignored
grep "^\.env$" .gitignore
```

If not present, add it:
```bash
echo ".env" >> .gitignore
```

---

## Step 4: Install Dependencies

### 4.1 Install Tweepy Library

```bash
# Using pip
pip install tweepy>=4.14.0

# OR using uv (recommended)
uv pip install tweepy>=4.14.0
```

### 4.2 Verify Installation

```bash
python -c "import tweepy; print(f'Tweepy version: {tweepy.__version__}')"
```

Expected output: `Tweepy version: 4.14.0` (or higher)

---

## Step 5: Verify Setup

### 5.1 Run Setup Verification Script

```bash
python scripts/verify_twitter_setup.py
```

Expected output:
```
✅ Twitter API credentials found in .env
✅ Tweepy library installed (v4.14.0)
✅ Successfully authenticated with Twitter API
✅ Account info: @your_username (ID: 1234567890)
✅ API permissions: Read and Write
✅ Rate limits: 50 tweets remaining (24h window)

🎉 Twitter integration is ready!
```

### 5.2 Troubleshooting Verification Failures

**Error: "Could not authenticate"**
- Check API keys are correct in .env
- Ensure no extra spaces in .env values
- Verify app permissions are "Read and Write"
- Regenerate access tokens if permissions were changed

**Error: "Tweepy not found"**
- Run: `pip install tweepy>=4.14.0`
- Verify Python version: `python --version` (should be 3.10+)

**Error: "Rate limit exceeded"**
- Wait for rate limit reset (shown in error message)
- Free tier: 50 tweets per 24 hours

---

## Step 6: Test Your First Tweet

### 6.1 Create Test Approval Request

Create a file: `AI_Employee_Vault/Approved/SOCIAL_TWITTER_POST_TWEET_20260319_TEST.md`

```yaml
---
approval_id: SOCIAL_TWITTER_POST_TWEET_20260319_TEST
action_type: twitter_post_tweet
email_action_ref: social_media_post
action_params:
  platform: twitter
  post_type: tweet
risk_assessment: low
reasoning: Testing Twitter MCP integration setup
created_at: 2026-03-19T10:30:00Z
metadata:
  text: "🤖 Testing my AI Employee Twitter integration! #AI #Automation"
  image_paths: []
  scheduled_time: null
---

# Twitter Test Tweet

**Approval ID:** SOCIAL_TWITTER_POST_TWEET_20260319_TEST
**Action Type:** twitter_post_tweet

## Content

🤖 Testing my AI Employee Twitter integration! #AI #Automation

---

**Status:** APPROVED
```

### 6.2 Run Approval Executor

```bash
PYTHONPATH=. python scripts/approval_executor.py
```

### 6.3 Verify Tweet Posted

1. Check your Twitter profile: `https://twitter.com/your_username`
2. You should see the test tweet
3. Check audit logs: `AI_Employee_Vault/Logs/2026-03-19.json`
4. Approval file should be in `AI_Employee_Vault/Done/`

---

## Step 7: Test Thread Creation

### 7.1 Create Thread Approval Request

Create a file: `AI_Employee_Vault/Approved/SOCIAL_TWITTER_POST_THREAD_20260319_TEST.md`

```yaml
---
approval_id: SOCIAL_TWITTER_POST_THREAD_20260319_TEST
action_type: twitter_post_thread
email_action_ref: social_media_post
action_params:
  platform: twitter
  post_type: thread
risk_assessment: low
reasoning: Testing Twitter thread creation
created_at: 2026-03-19T10:35:00Z
metadata:
  tweets:
    - "Testing thread creation with my AI Employee! 🧵"
    - "This is the second tweet in the thread."
    - "And this is the final tweet. All automated!"
  image_paths: []
  scheduled_time: null
---

# Twitter Test Thread

**Approval ID:** SOCIAL_TWITTER_POST_THREAD_20260319_TEST
**Action Type:** twitter_post_thread

## Content

1. Testing thread creation with my AI Employee! 🧵
2. This is the second tweet in the thread.
3. And this is the final tweet. All automated!

---

**Status:** APPROVED
```

### 7.2 Run Approval Executor

```bash
PYTHONPATH=. python scripts/approval_executor.py
```

### 7.3 Verify Thread Posted

1. Check your Twitter profile
2. You should see a 3-tweet thread with automatic numbering
3. Each tweet should reply to the previous one

---

## Common Issues & Solutions

### Issue 1: "401 Unauthorized"

**Cause**: Invalid or expired credentials

**Solution**:
1. Verify API keys in .env are correct
2. Check for extra spaces or quotes in .env
3. Regenerate access tokens in Developer Portal
4. Ensure app permissions are "Read and Write"

### Issue 2: "403 Forbidden"

**Cause**: Insufficient permissions or suspended account

**Solution**:
1. Check app permissions are "Read and Write"
2. Verify Twitter account is not suspended
3. Ensure Developer account is approved
4. Check if app has been restricted

### Issue 3: "429 Too Many Requests"

**Cause**: Rate limit exceeded

**Solution**:
1. Wait for rate limit reset (check error message for time)
2. Free tier: 50 tweets per 24 hours
3. Consider upgrading to paid tier for higher limits
4. Use proactive throttling to avoid hitting limits

### Issue 4: "Duplicate Tweet"

**Cause**: Twitter rejects identical tweets within short time

**Solution**:
1. Modify tweet text slightly
2. Wait a few minutes before retrying
3. Add timestamp or unique identifier to tweet

### Issue 5: "Image Upload Failed"

**Cause**: Invalid image format or size

**Solution**:
1. Check image format: PNG, JPG, GIF only
2. Check image size: max 5MB per image
3. Verify file path is correct and accessible
4. Ensure image is not corrupted

---

## Next Steps

### For Development
1. Run `/sp.tasks` to generate implementation tasks
2. Implement twitter_client.py
3. Implement twitter_mcp_server.py
4. Write comprehensive tests
5. Update approval_executor.py

### For Production Use
1. Set up PM2 for process management
2. Configure cron jobs for monitoring
3. Set up rate limit alerts
4. Monitor audit logs regularly
5. Backup .env file securely

---

## Security Best Practices

1. **Never commit .env to git**
   - Always keep credentials in .env
   - Verify .env is in .gitignore
   - Use .env.example for documentation

2. **Rotate tokens regularly**
   - Regenerate access tokens every 90 days
   - Update .env with new tokens
   - Test after rotation

3. **Monitor API usage**
   - Check rate limit usage daily
   - Set up alerts for quota exhaustion
   - Review audit logs for suspicious activity

4. **Secure approval workflow**
   - Review all approval requests before moving to Approved/
   - Never automate approval process
   - Keep audit trail of all actions

---

## Additional Resources

- [Twitter API v2 Documentation](https://developer.twitter.com/en/docs/twitter-api)
- [Tweepy Documentation](https://docs.tweepy.org/)
- [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
- [Rate Limits Reference](https://developer.twitter.com/en/docs/twitter-api/rate-limits)

---

## Support

If you encounter issues not covered in this guide:
1. Check audit logs: `AI_Employee_Vault/Logs/`
2. Review error messages in approval executor output
3. Consult Twitter API documentation
4. Check Tweepy GitHub issues

---

**Setup Complete!** 🎉

You're now ready to use Twitter integration with your AI Employee system.
