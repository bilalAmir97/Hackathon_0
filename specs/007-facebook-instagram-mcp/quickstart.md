# Quickstart Guide: Facebook & Instagram MCP Server

**Feature**: 007-facebook-instagram-mcp
**Date**: 2026-03-18
**Audience**: Developers setting up the MCP server

---

## Overview

This guide walks you through setting up the Facebook & Instagram MCP Server for the AI Employee system. You'll obtain access tokens, configure environment variables, install dependencies, and test the MCP server with Claude Code.

**Estimated Setup Time**: 30-45 minutes

---

## Prerequisites

- Python 3.10+ installed
- Facebook page with admin access
- Instagram business account linked to Facebook page
- Meta Business Suite access
- Claude Code installed and configured

---

## Step 1: Obtain Facebook Page Access Token

### 1.1 Create Facebook App (if not already created)

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Select "Business" as app type
4. Fill in app details:
   - App Name: "AI Employee Social Media"
   - Contact Email: Your email
5. Click "Create App"

### 1.2 Configure App Permissions

1. In your app dashboard, go to "App Settings" → "Basic"
2. Add "Facebook Login" product
3. Go to "Facebook Login" → "Settings"
4. Add OAuth Redirect URI: `https://localhost/`
5. Go to "App Review" → "Permissions and Features"
6. Request these permissions:
   - `pages_manage_posts` (publish to pages)
   - `pages_read_engagement` (read metrics)
   - `pages_show_list` (list pages)

### 1.3 Generate User Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from dropdown
3. Click "Generate Access Token"
4. Grant permissions when prompted
5. Copy the short-lived token (valid for 1 hour)

### 1.4 Exchange for Long-Lived Token

Run this command (replace placeholders):

```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
```

Response:
```json
{
  "access_token": "LONG_LIVED_USER_TOKEN",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

### 1.5 Get Page Access Token

Run this command (replace with your long-lived user token):

```bash
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=LONG_LIVED_USER_TOKEN"
```

Response:
```json
{
  "data": [
    {
      "access_token": "PAGE_ACCESS_TOKEN",
      "category": "Business",
      "name": "My Business Page",
      "id": "12345",
      "tasks": ["ANALYZE", "ADVERTISE", "MODERATE", "CREATE_CONTENT"]
    }
  ]
}
```

**Save**: `PAGE_ACCESS_TOKEN` and `id` (page_id)

---

## Step 2: Obtain Instagram Business Account Access Token

### 2.1 Link Instagram to Facebook Page

1. Go to [Meta Business Suite](https://business.facebook.com/)
2. Select your Facebook page
3. Go to "Settings" → "Instagram"
4. Click "Connect Account"
5. Log in to Instagram and authorize

### 2.2 Get Instagram Business Account ID

Run this command (replace with your page access token and page ID):

```bash
curl -X GET "https://graph.facebook.com/v19.0/PAGE_ID?fields=instagram_business_account&access_token=PAGE_ACCESS_TOKEN"
```

Response:
```json
{
  "instagram_business_account": {
    "id": "98765"
  },
  "id": "12345"
}
```

**Save**: Instagram business account ID (`98765`)

### 2.3 Verify Instagram Permissions

Run this command to verify you can access Instagram:

```bash
curl -X GET "https://graph.facebook.com/v19.0/IG_ACCOUNT_ID?fields=username,name&access_token=PAGE_ACCESS_TOKEN"
```

Response:
```json
{
  "username": "mybusiness",
  "name": "My Business",
  "id": "98765"
}
```

**Note**: The same page access token works for both Facebook and Instagram.

---

## Step 3: Configure Environment Variables

### 3.1 Create .env File

In your project root, create or update `.env`:

```bash
# Facebook Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
FACEBOOK_PAGE_ID=12345

# Instagram Configuration
INSTAGRAM_BUSINESS_ACCESS_TOKEN=your_page_access_token_here
INSTAGRAM_BUSINESS_ACCOUNT_ID=98765

# Optional Configuration
META_API_VERSION=v19.0
RATE_LIMIT_THRESHOLD=0.8
METRICS_CACHE_TTL=300
```

### 3.2 Verify .env is in .gitignore

Ensure `.env` is listed in `.gitignore`:

```bash
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
```

---

## Step 4: Install Dependencies

### 4.1 Update requirements.txt

Add these dependencies to `requirements.txt`:

```
requests>=2.31.0
Pillow>=10.0.0
cachetools>=5.3.0
python-dotenv>=1.0.0
```

### 4.2 Install Dependencies

```bash
pip install -r requirements.txt
```

Or with uv (if using uv):

```bash
uv pip install -r requirements.txt
```

---

## Step 5: Verify Setup

### 5.1 Test Facebook Connection

Create a test script `test_facebook_connection.py`:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

page_id = os.getenv("FACEBOOK_PAGE_ID")
access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

# Test API connection
url = f"https://graph.facebook.com/v19.0/{page_id}"
params = {
    "fields": "name,username,fan_count",
    "access_token": access_token
}

response = requests.get(url, params=params)
print("Facebook Page Info:")
print(response.json())
```

Run:
```bash
python test_facebook_connection.py
```

Expected output:
```json
{
  "name": "My Business Page",
  "username": "mybusiness",
  "fan_count": 1234,
  "id": "12345"
}
```

### 5.2 Test Instagram Connection

Create a test script `test_instagram_connection.py`:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
access_token = os.getenv("INSTAGRAM_BUSINESS_ACCESS_TOKEN")

# Test API connection
url = f"https://graph.facebook.com/v19.0/{account_id}"
params = {
    "fields": "username,name,followers_count",
    "access_token": access_token
}

response = requests.get(url, params=params)
print("Instagram Account Info:")
print(response.json())
```

Run:
```bash
python test_instagram_connection.py
```

Expected output:
```json
{
  "username": "mybusiness",
  "name": "My Business",
  "followers_count": 5678,
  "id": "98765"
}
```

---

## Step 6: Configure Claude Code MCP Server

### 6.1 Update Claude Code Configuration

Edit your Claude Code MCP configuration file (location varies by OS):

**Linux/WSL**: `~/.config/claude-code/mcp_config.json`
**macOS**: `~/Library/Application Support/claude-code/mcp_config.json`
**Windows**: `%APPDATA%\claude-code\mcp_config.json`

Add the Facebook & Instagram MCP server:

```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": ["mcp_servers/email_mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    },
    "odoo": {
      "command": "python",
      "args": ["mcp_servers/odoo_mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    },
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

### 6.2 Restart Claude Code

Restart Claude Code to load the new MCP server configuration.

---

## Step 7: Test MCP Server with Claude Code

### 7.1 Test Facebook Post (Text Only)

In Claude Code, try this command:

```
Post to Facebook: "Testing the new AI Employee social media integration! 🚀"
```

Expected response:
```
Approval request created: approval-fb-post-20260318-103045
Status: Pending approval
Approval file: AI_Employee_Vault/Pending_Approval/APPROVAL_facebook_post_20260318_103045.json

Please review and approve the post in the Pending_Approval directory.
```

### 7.2 Approve the Post

1. Open `AI_Employee_Vault/Pending_Approval/APPROVAL_facebook_post_20260318_103045.json`
2. Review the content preview
3. Move the file to `AI_Employee_Vault/Approved/` to approve
4. The approval executor will detect and execute the post

### 7.3 Verify Post Published

Check your Facebook page to verify the post was published.

### 7.4 Test Metrics Retrieval

In Claude Code, try this command:

```
Get engagement metrics for Facebook post ID: 12345_67890
```

Expected response:
```json
{
  "status": "success",
  "post_id": "12345_67890",
  "metrics": {
    "likes": 15,
    "comments": 3,
    "shares": 2,
    "reactions": 18,
    "reach": 245,
    "impressions": 312
  },
  "cached": false,
  "cached_until": "2026-03-18T10:35:00Z"
}
```

---

## Step 8: Test Instagram Post

### 8.1 Prepare Test Image

Ensure you have a test image that meets Instagram requirements:
- Format: JPEG or PNG
- Size: Max 8MB
- Aspect ratio: 4:5 to 1.91:1
- Min width: 320px

### 8.2 Test Instagram Post

In Claude Code, try this command:

```
Post to Instagram: "New product launch! 🎉 #NewProduct #Launch" with image at /path/to/test-image.jpg
```

Expected response:
```
Image validation passed:
- Format: JPEG
- Size: 2.3 MB
- Dimensions: 1080x1080
- Aspect ratio: 1.0

Approval request created: approval-ig-post-20260318-103045
Status: Pending approval
Approval file: AI_Employee_Vault/Pending_Approval/APPROVAL_instagram_post_20260318_103045.json

Please review and approve the post in the Pending_Approval directory.
```

### 8.3 Approve and Verify

Follow the same approval process as Facebook, then verify the post on Instagram.

---

## Troubleshooting

### Issue: "Invalid OAuth access token"

**Cause**: Token expired or invalid

**Solution**:
1. Check token expiration: `curl "https://graph.facebook.com/v19.0/debug_token?input_token=YOUR_TOKEN&access_token=YOUR_TOKEN"`
2. If expired, generate new long-lived token (Step 1.4)
3. Update `.env` file with new token

### Issue: "Rate limit exceeded"

**Cause**: Too many API calls in short period

**Solution**:
1. Wait 1 hour for rate limit to reset
2. Check rate limit status in MCP server logs
3. Reduce posting frequency

### Issue: "Image validation failed"

**Cause**: Image doesn't meet platform requirements

**Solution**:
1. Check image format (JPEG/PNG for Instagram, JPEG/PNG/GIF for Facebook)
2. Check image size (max 8MB for Instagram, 4MB for Facebook)
3. Check aspect ratio (4:5 to 1.91:1 for Instagram)
4. Use image editing tool to resize/convert if needed

### Issue: "Permission denied"

**Cause**: Missing required permissions

**Solution**:
1. Go to Graph API Explorer
2. Verify permissions granted: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`
3. Re-generate token with correct permissions

### Issue: "Instagram account not found"

**Cause**: Instagram account not linked to Facebook page

**Solution**:
1. Go to Meta Business Suite
2. Link Instagram business account to Facebook page (Step 2.1)
3. Verify link: `curl "https://graph.facebook.com/v19.0/PAGE_ID?fields=instagram_business_account&access_token=TOKEN"`

---

## Next Steps

After successful setup:

1. **Configure Approval Workflow**: Set up approval executor to monitor `Pending_Approval/` directory
2. **Enable Scheduling**: Configure cron jobs for scheduled posts
3. **Monitor Metrics**: Set up weekly audit to track engagement metrics
4. **Test Error Recovery**: Simulate network errors to verify retry logic
5. **Review Audit Logs**: Check `AI_Employee_Vault/Logs/` for all operations

---

## Additional Resources

- [Meta Graph API Documentation](https://developers.facebook.com/docs/graph-api/)
- [Facebook Pages API](https://developers.facebook.com/docs/pages/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer/)

---

## Support

If you encounter issues not covered in this guide:

1. Check audit logs: `AI_Employee_Vault/Logs/`
2. Review error messages in approval request files
3. Verify environment variables are set correctly
4. Test API connection with curl commands
5. Check Meta API status: [Meta for Developers Status](https://developers.facebook.com/status/)

---

**Setup Status**: Ready for implementation
**Last Updated**: 2026-03-18
