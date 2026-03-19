# Troubleshooting: "No Pages Found" Error

## Problem

The `/me/accounts` endpoint returns empty `{"data":[]}` even though you own a Facebook Page.

## Root Cause

Your Meta app doesn't have access to your Facebook Page, even in Development Mode. This is a common issue with Meta's permission system.

---

## Solution 1: Grant App Access via Page Settings

1. Go to your **Facebook Page**
2. Click **Settings** (left sidebar)
3. Look for one of these sections (varies by interface):
   - **Page Access**
   - **Apps**
   - **Platform** → **Apps**
   - **Advanced** → **Connected Apps**
4. Click **Add Apps** or **Connect Apps**
5. Search for your app (by name or App ID)
6. Grant access with these permissions:
   - Manage Page
   - Publish content
   - Read insights

---

## Solution 2: Use Page Access Token Tool

1. Go to https://developers.facebook.com/tools/accesstoken/
2. Find your app in the list
3. Under **User Token**, click **Generate Token**
4. You'll see a list of pages you manage
5. Select your page
6. Grant all requested permissions
7. Copy the **Page Access Token** (not User Token)
8. This token can be used directly in your .env file

**Add to .env:**
```bash
FACEBOOK_PAGE_ACCESS_TOKEN=<token from Access Token Tool>
FACEBOOK_PAGE_ID=<your page ID>
```

---

## Solution 3: Manual Page Token Generation

If the above methods don't work, generate a page token manually:

### Step 1: Get User Token with Page Permissions

```bash
# Use this OAuth URL (replace YOUR_APP_ID)
https://www.facebook.com/v19.0/dialog/oauth?client_id=YOUR_APP_ID&redirect_uri=https://localhost/&scope=pages_show_list,pages_manage_posts,pages_read_engagement&response_type=token
```

### Step 2: List Your Pages

```bash
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_USER_TOKEN"
```

**If this still returns empty**, try:

```bash
# Get your Page ID manually from the page URL
# Example: facebook.com/YourPageName → Page ID is in the URL or About section

# Then get page token directly using Page ID
curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?fields=access_token&access_token=YOUR_USER_TOKEN"
```

---

## Solution 4: Check App Configuration

Your app might be missing required products:

1. Go to https://developers.facebook.com/apps/
2. Select your app
3. Go to **App Dashboard**
4. Check if these products are added:
   - ✅ **Facebook Login** (required)
   - ✅ **Instagram** (for Instagram features)
5. If missing, click **Add Product** and add them

---

## Solution 5: Use Business Manager (If Applicable)

If your page is owned by a Business Manager:

1. Go to https://business.facebook.com/
2. Click **Business Settings**
3. Go to **Users** → **System Users**
4. Create a new System User or select existing
5. Assign your page to the System User
6. Generate a System User Token with page permissions
7. Use this token instead of personal user token

---

## Solution 6: Verify Page Ownership

Make sure you're actually an admin:

1. Go to your Facebook Page
2. Click **Settings** → **Page Roles** or **Page Access**
3. Verify you're listed as **Admin** (not Editor, Moderator, etc.)
4. If not, ask the page owner to make you an admin

---

## Quick Diagnostic Commands

### Check which account the token belongs to:
```bash
curl -X GET "https://graph.facebook.com/v19.0/me?fields=id,name,email&access_token=YOUR_TOKEN"
```

### Check token permissions:
```bash
curl -X GET "https://graph.facebook.com/v19.0/debug_token?input_token=YOUR_TOKEN&access_token=YOUR_TOKEN"
```

### Try to access page directly (if you know Page ID):
```bash
curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?fields=id,name,access_token&access_token=YOUR_TOKEN"
```

---

## Alternative: Use Long-Lived User Token

If you can't get page tokens to work, you can use a long-lived user token with page permissions:

1. Generate user token with `pages_show_list,pages_manage_posts,pages_read_engagement`
2. Exchange for long-lived token (60 days)
3. Use this token for both `FACEBOOK_PAGE_ACCESS_TOKEN` and `INSTAGRAM_BUSINESS_ACCESS_TOKEN`
4. Set `FACEBOOK_PAGE_ID` to your page ID (get from page About section)

**Note:** User tokens expire after 60 days, while page tokens never expire.

---

## Still Not Working?

If none of the above work, there might be a Meta platform issue. Try:

1. **Wait 15-30 minutes** - Meta's permission system sometimes has delays
2. **Revoke app access** - Go to facebook.com/settings/apps → Remove your app → Re-authorize
3. **Create a new app** - Sometimes starting fresh resolves permission issues
4. **Contact Meta Support** - Use the "Get Support" button in your app dashboard

---

## Success Verification

Once you get the token, verify it works:

```bash
# Should return your page info
curl -X GET "https://graph.facebook.com/v19.0/me/accounts?access_token=YOUR_TOKEN"

# Should return page details
curl -X GET "https://graph.facebook.com/v19.0/YOUR_PAGE_ID?fields=id,name,fan_count&access_token=YOUR_PAGE_TOKEN"
```

If both commands return valid data, your setup is complete!
