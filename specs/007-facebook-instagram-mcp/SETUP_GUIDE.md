# Facebook & Instagram MCP Server - Setup Guide

**Last Updated:** 2026-03-18

This guide walks you through obtaining the required credentials for the Facebook & Instagram MCP Server.

---

## 🚀 Quick Start (If Graph API Explorer doesn't show permissions)

**Problem:** The Graph API Explorer permissions dropdown doesn't show `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, etc.

**Solution:** Use the OAuth URL method instead:

1. **Get your App ID**: Go to https://developers.facebook.com/apps/ → Your App → Settings → Basic → Copy "App ID"

2. **Generate token with this URL** (replace `YOUR_APP_ID`):
   ```
   https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=https://localhost/&scope=pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish,instagram_manage_insights&response_type=token
   ```

3. **Authorize**: Paste URL in browser, click "Continue as [Your Name]", authorize all permissions

4. **Copy token**: You'll be redirected to `https://localhost/?access_token=EAABsbCS...` - Copy everything after `access_token=` and before `&`

5. **Convert to long-lived token**: Follow Step 4 below to convert to page token

**Then continue with the full guide below for detailed instructions.**

---

## Prerequisites

Before you begin, ensure you have:

1. ✅ **Facebook Page** - A Facebook Page you manage (not a personal profile)
2. ✅ **Instagram Business Account** - Instagram account converted to Business Account
3. ✅ **Instagram-Facebook Link** - Instagram Business Account linked to your Facebook Page
4. ✅ **Meta Developer Account** - Free account at https://developers.facebook.com

---

## Step 1: Create a Meta App

1. Go to **https://developers.facebook.com**
2. Click **"My Apps"** → **"Create App"**
3. Select **"Business"** as app type
4. Fill in app details:
   - **App Name:** "AI Employee Social Media Manager" (or your choice)
   - **App Contact Email:** Your email
   - **Business Account:** Select or create one
5. Click **"Create App"**

---

## Step 2: Add Required Products

In your app dashboard, add these products:

### Facebook Login
1. Click **"Add Product"** → **"Facebook Login"**
2. Click **"Settings"** under Facebook Login
3. Add **Valid OAuth Redirect URIs:** `https://localhost/` (for testing)

### Instagram Basic Display (Optional for testing)
1. Click **"Add Product"** → **"Instagram Basic Display"**

---

## Step 3: Configure App Permissions

1. Go to **"App Settings"** → **"Basic"**
2. Note your **App ID** and **App Secret** (you'll need these)

**IMPORTANT:** You don't need to manually request permissions in "App Review" for Development Mode testing. Permissions are requested during the OAuth token generation process (Step 4).

**Required Permissions:**

**For Facebook:**
- ✅ `pages_manage_posts` - Post to pages
- ✅ `pages_read_engagement` - Read engagement metrics
- ✅ `pages_show_list` - List pages you manage

**For Instagram:**
- ✅ `instagram_basic` - Basic account info
- ✅ `instagram_content_publish` - Publish content
- ✅ `instagram_manage_insights` - Read insights

**Note:** In Development Mode, you can test with your own accounts without app review. For production (posting to pages you don't own), you'll need to submit for app review.

---

## Step 4: Get Facebook Page Access Token

### Method 1: Using Graph API Explorer (Recommended for Testing)

1. Go to **https://developers.facebook.com/tools/explorer/**
2. Select your app from the dropdown
3. Click **"Generate Access Token"**
4. **IMPORTANT:** The permissions dropdown may not show all permissions. You can manually add them:
   - Click in the permissions field
   - Type or paste these permissions (comma-separated or one at a time):
     - `pages_manage_posts`
     - `pages_read_engagement`
     - `pages_show_list`
   - If typing doesn't work, use Method 2 below (OAuth URL)
5. Click **"Generate Access Token"** and authorize
6. Copy the **User Access Token** (short-lived, 1-2 hours)

### Method 2: Using OAuth URL (If Graph Explorer doesn't work)

If the Graph API Explorer doesn't show the permissions, generate a token using this OAuth URL:

```
https://www.facebook.com/v19.0/dialog/oauth?
  client_id=YOUR_APP_ID
  &redirect_uri=https://localhost/
  &scope=pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish,instagram_manage_insights
  &response_type=token
```

**Steps:**
1. Replace `YOUR_APP_ID` with your actual App ID (from App Dashboard → Settings → Basic)
2. Copy the entire URL into your browser (remove line breaks)
3. Authorize the permissions
4. You'll be redirected to `https://localhost/?access_token=...`
5. Copy the `access_token` from the URL (everything after `access_token=` and before `&`)
6. This is your short-lived User Access Token

### Method 3: Complete OAuth URL (All Permissions at Once)

Use this single URL to get all Facebook AND Instagram permissions:

```
https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=https://localhost/&scope=pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish,instagram_manage_insights&response_type=token
```

**Steps:**
1. Replace `YOUR_APP_ID` with your App ID
2. Paste the URL in your browser
3. Authorize all permissions
4. Copy the `access_token` from the redirect URL

### Convert to Long-Lived Page Access Token

**Important:** The token from Graph Explorer or OAuth expires quickly. Convert it to a long-lived token:

1. Use this API call (replace placeholders):

```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

2. You'll get a long-lived user token (60 days). Now get the page token:

```bash
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_LONG_LIVED_USER_TOKEN"
```

3. Find your page in the response and copy its `access_token` - **This is your FACEBOOK_PAGE_ACCESS_TOKEN**
4. Copy the page `id` - **This is your FACEBOOK_PAGE_ID**

**Example Response:**
```json
{
  "data": [
    {
      "access_token": "EAABsbCS1iHgBO7ZC9Q...",  // ← Use this
      "category": "Business",
      "name": "My Business Page",
      "id": "123456789012345",  // ← Use this
      "tasks": ["ANALYZE", "ADVERTISE", "MODERATE", "CREATE_CONTENT", "MANAGE"]
    }
  ]
}
```

---

## Step 5: Get Instagram Business Account Credentials

### Prerequisites
Your Instagram account MUST be:
1. Converted to **Business Account** (Settings → Account → Switch to Professional Account)
2. Linked to your **Facebook Page** (Settings → Account → Linked Accounts → Facebook)

### Get Instagram Account ID

1. Use the Facebook Page token from Step 4:

```bash
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?fields=instagram_business_account&access_token=YOUR_FACEBOOK_PAGE_TOKEN"
```

2. Find the `instagram_business_account` object:

```json
{
  "data": [
    {
      "instagram_business_account": {
        "id": "17841405309211844"  // ← This is your INSTAGRAM_BUSINESS_ACCOUNT_ID
      },
      "id": "123456789012345"
    }
  ]
}
```

3. **INSTAGRAM_BUSINESS_ACCESS_TOKEN** = Same as your **FACEBOOK_PAGE_ACCESS_TOKEN**
   (Instagram uses the Facebook Page token for Business Account API access)

---

## Step 6: Configure Your .env File

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` and add your credentials:

```bash
# Facebook Page Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=EAABsbCS1iHgBO7ZC9Q...  # From Step 4
FACEBOOK_PAGE_ID=123456789012345                    # From Step 4

# Instagram Business Account Configuration
INSTAGRAM_BUSINESS_ACCESS_TOKEN=EAABsbCS1iHgBO7ZC9Q...  # Same as Facebook token
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841405309211844         # From Step 5

# Optional: Keep defaults or customize
META_GRAPH_API_VERSION=v19.0
META_RATE_LIMIT_THRESHOLD=0.8
META_METRICS_CACHE_TTL=300
```

3. **IMPORTANT:** Verify `.env` is in `.gitignore` (it already is):

```bash
grep "^\.env$" .gitignore
# Should output: .env
```

---

## Step 7: Verify Your Setup

### Test 1: Check Token Validity

```bash
# Test Facebook token
curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?access_token=YOUR_FACEBOOK_PAGE_ACCESS_TOKEN&fields=id,name"

# Test Instagram token
curl -X GET "https://graph.facebook.com/v19.0/YOUR_INSTAGRAM_ACCOUNT_ID?access_token=YOUR_INSTAGRAM_TOKEN&fields=id,username"
```

**Expected:** Both should return JSON with your page/account info (not an error).

### Test 2: Run MCP Server Validation

The MCP server has built-in token validation. When you start it, it will validate tokens automatically.

---

## Troubleshooting

### Error: "Can't find permissions in Graph API Explorer dropdown"
- **Cause:** Graph API Explorer doesn't always show all permissions in the dropdown
- **Fix:** Use Method 2 or Method 3 (OAuth URL) from Step 4 instead of Graph API Explorer
- **Alternative:** In Graph API Explorer, try typing the permission name directly in the permissions field instead of selecting from dropdown

### Error: "Invalid OAuth access token"
- **Cause:** Token expired or incorrect
- **Fix:** Generate a new long-lived token (Step 4)

### Error: "Instagram account not found"
- **Cause:** Instagram account not converted to Business Account or not linked to Facebook Page
- **Fix:**
  1. Go to Instagram app → Settings → Account → Switch to Professional Account
  2. Link to Facebook Page: Settings → Account → Linked Accounts → Facebook

### Error: "Permissions not granted"
- **Cause:** Missing required permissions
- **Fix:** Regenerate token with all required permissions using OAuth URL method (Step 4, Method 3)

### Error: "App not in Development Mode"
- **Cause:** App is in Development Mode and you're trying to post to pages you don't manage
- **Fix:** Either:
  1. Add test users in App Dashboard → Roles → Test Users
  2. Submit app for review to go live (for production)

### Error: "(#200) Provide valid app ID"
- **Cause:** App ID is incorrect in OAuth URL
- **Fix:** Copy App ID from App Dashboard → Settings → Basic and replace YOUR_APP_ID in the OAuth URL

---

## Token Expiration & Refresh

### Token Lifetimes
- **Short-lived User Token:** 1-2 hours
- **Long-lived User Token:** 60 days
- **Page Access Token:** Never expires (as long as user token is valid)

### When to Refresh
- Page tokens don't expire, but if the user revokes permissions, you'll need to regenerate
- Set up monitoring to detect token expiration (the MCP server logs errors)

### Auto-Refresh (Future Enhancement)
Currently, tokens must be manually refreshed. Future versions will support automatic token refresh.

---

## Security Best Practices

1. ✅ **Never commit .env to git** - Already in .gitignore
2. ✅ **Use long-lived tokens** - Follow Step 4 to convert tokens
3. ✅ **Rotate tokens periodically** - Regenerate every 30-60 days
4. ✅ **Monitor token usage** - Check audit logs for suspicious activity
5. ✅ **Use Development Mode** - For testing, keep app in Development Mode
6. ✅ **Limit permissions** - Only request permissions you need

---

## Quick Reference

### Where to Find Things

| What | Where |
|------|-------|
| App Dashboard | https://developers.facebook.com/apps/ |
| Graph API Explorer | https://developers.facebook.com/tools/explorer/ |
| Access Token Debugger | https://developers.facebook.com/tools/debug/accesstoken/ |
| Permissions Reference | https://developers.facebook.com/docs/permissions/reference |
| Instagram API Docs | https://developers.facebook.com/docs/instagram-api |

### Required Credentials Summary

```bash
# 4 Required Values
FACEBOOK_PAGE_ACCESS_TOKEN=<long-lived-page-token>
FACEBOOK_PAGE_ID=<numeric-page-id>
INSTAGRAM_BUSINESS_ACCESS_TOKEN=<same-as-facebook-token>
INSTAGRAM_BUSINESS_ACCOUNT_ID=<numeric-instagram-id>
```

---

## Next Steps

After completing this setup:

1. ✅ Verify credentials are in `.env`
2. ✅ Install dependencies: `uv pip install requests Pillow cachetools`
3. ✅ Run tests: `pytest tests/test_*social*.py -v`
4. ✅ Test posting via Claude Code MCP tools
5. ✅ Monitor approval workflow in `AI_Employee_Vault/Pending_Approval/`

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify token validity with Access Token Debugger
3. Review audit logs in `AI_Employee_Vault/Logs/`
4. Check Meta's API status: https://developers.facebook.com/status/

---

**Setup Complete!** 🎉

Your Facebook & Instagram MCP Server is ready to use.
