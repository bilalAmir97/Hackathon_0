# Facebook & Instagram MCP - Quick Setup (5 Minutes)

**For users who can't find permissions in Graph API Explorer**

---

## Step 1: Get Your App ID (30 seconds)

1. Go to https://developers.facebook.com/apps/
2. Click on your app
3. Go to **Settings** → **Basic**
4. Copy your **App ID** (e.g., `123456789012345`)
5. Copy your **App Secret** (click "Show" button)

---

## Step 2: Generate Access Token (1 minute)

**Copy this URL and replace `YOUR_APP_ID` with your actual App ID:**

```
https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=https://localhost/&scope=pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish,instagram_manage_insights&response_type=token
```

**Example:**
```
https://www.facebook.com/v19.0/dialog/oauth?client_id=123456789012345&redirect_uri=https://localhost/&scope=pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish,instagram_manage_insights&response_type=token
```

1. Paste the URL in your browser
2. Click **"Continue as [Your Name]"**
3. Review permissions and click **"Continue"**
4. You'll be redirected to: `https://localhost/?access_token=EAABsbCS1iHgBO...&data_access_expiration_time=...`
5. Copy the **access_token** value (everything between `access_token=` and `&`)

**Save this token temporarily** - we'll convert it in the next step.

---

## Step 3: Convert to Long-Lived Page Token (2 minutes)

### 3a. Exchange for Long-Lived User Token

Run this command (replace placeholders):

```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

**Example:**
```bash
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=123456789012345&client_secret=abc123def456&fb_exchange_token=EAABsbCS1iHgBO..."
```

**Response:**
```json
{
  "access_token": "EAABsbCS1iHgBO7ZC9Q...",
  "token_type": "bearer",
  "expires_in": 5183944
}
```

Copy the new `access_token` - this is your **long-lived user token** (valid for 60 days).

### 3b. Get Page Access Token

Run this command with your long-lived user token:

```bash
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_LONG_LIVED_USER_TOKEN"
```

**Response:**
```json
{
  "data": [
    {
      "access_token": "EAABsbCS1iHgBO7ZC9Q...",
      "category": "Business",
      "name": "My Business Page",
      "id": "123456789012345",
      "tasks": ["ANALYZE", "ADVERTISE", "MODERATE", "CREATE_CONTENT", "MANAGE"]
    }
  ]
}
```

**Save these values:**
- `access_token` → **FACEBOOK_PAGE_ACCESS_TOKEN** (this never expires!)
- `id` → **FACEBOOK_PAGE_ID**

---

## Step 4: Get Instagram Business Account ID (1 minute)

Run this command with your page token:

```bash
curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?fields=instagram_business_account&access_token=YOUR_FACEBOOK_PAGE_TOKEN"
```

**Example:**
```bash
curl -X GET "https://graph.facebook.com/v19.0/123456789012345?fields=instagram_business_account&access_token=EAABsbCS1iHgBO..."
```

**Response:**
```json
{
  "instagram_business_account": {
    "id": "17841405309211844"
  },
  "id": "123456789012345"
}
```

**Save this value:**
- `instagram_business_account.id` → **INSTAGRAM_BUSINESS_ACCOUNT_ID**

---

## Step 5: Configure .env File (30 seconds)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:

```bash
# Facebook Page Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=EAABsbCS1iHgBO7ZC9Q...  # From Step 3b
FACEBOOK_PAGE_ID=123456789012345                    # From Step 3b

# Instagram Business Account Configuration
INSTAGRAM_BUSINESS_ACCESS_TOKEN=EAABsbCS1iHgBO7ZC9Q...  # Same as Facebook token
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841405309211844         # From Step 4

# Optional: Keep defaults
META_GRAPH_API_VERSION=v19.0
META_RATE_LIMIT_THRESHOLD=0.8
META_METRICS_CACHE_TTL=300
```

---

## Step 6: Verify Setup (30 seconds)

Test your tokens:

```bash
# Test Facebook token
curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?access_token=YOUR_FACEBOOK_PAGE_TOKEN&fields=id,name"

# Test Instagram token
curl -X GET "https://graph.facebook.com/v19.0/YOUR_INSTAGRAM_ACCOUNT_ID?access_token=YOUR_INSTAGRAM_TOKEN&fields=id,username"
```

**Expected:** Both should return JSON with your page/account info (not an error).

---

## ✅ Done!

Your Facebook & Instagram MCP Server is now configured. You have:

- ✅ **FACEBOOK_PAGE_ACCESS_TOKEN** (never expires)
- ✅ **FACEBOOK_PAGE_ID**
- ✅ **INSTAGRAM_BUSINESS_ACCESS_TOKEN** (same as Facebook token)
- ✅ **INSTAGRAM_BUSINESS_ACCOUNT_ID**

---

## Next Steps

1. Install dependencies:
   ```bash
   uv pip install requests Pillow cachetools
   ```

2. Run tests:
   ```bash
   pytest tests/test_*social*.py -v
   ```

3. Test posting via Claude Code MCP tools

---

## Common Issues

### "Instagram account not found"
- Your Instagram account must be a **Business Account** (not Personal or Creator)
- It must be **linked to your Facebook Page**
- Fix: Instagram app → Settings → Account → Switch to Professional Account → Link to Facebook Page

### "Invalid OAuth access token"
- Token expired or incorrect
- Fix: Regenerate token from Step 2

### "Permissions error"
- Missing required permissions
- Fix: Make sure you used the complete OAuth URL from Step 2 with all permissions

---

**Need help?** Check the full SETUP_GUIDE.md for detailed troubleshooting.
