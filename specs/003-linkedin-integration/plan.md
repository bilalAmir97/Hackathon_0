# LinkedIn Auto-Posting Implementation Plan

**Date:** 2026-02-27 00:45:00
**Goal:** Complete Silver Tier by implementing LinkedIn integration
**Estimated Time:** 4-6 hours
**Current Status:** Documentation exists, no implementation

---

## Implementation Approach Decision

### Option A: LinkedIn API (Official)
**Pros:**
- Official, supported method
- More reliable and stable
- Better rate limits
- Compliant with LinkedIn ToS

**Cons:**
- Requires LinkedIn Developer account
- Needs Marketing Developer Platform access (may require approval)
- OAuth setup complexity
- API limitations (may not support all post types)

**Time:** 6-8 hours (including approval wait time)

### Option B: Playwright Automation (Pragmatic) ✅ RECOMMENDED
**Pros:**
- No API approval needed
- Works immediately
- Can handle all post types
- Already have Playwright installed
- Faster implementation

**Cons:**
- May violate LinkedIn ToS (use at own risk)
- Less reliable (UI changes can break it)
- Requires session management
- Rate limiting concerns

**Time:** 4-6 hours

**Decision:** Use Playwright for faster implementation. Can migrate to API later if needed.

---

## Architecture Design

### Component Structure
```
watchers/linkedin_poster.py          # Main posting logic
.claude/skills/post-linkedin/        # Skill documentation (exists)
AI_Employee_Vault/Pending_LinkedIn/  # Posts awaiting approval
AI_Employee_Vault/Posted_LinkedIn/   # Successfully posted
scripts/linkedin_session.py          # Session management
```

### Workflow
```
1. User creates post draft → Pending_LinkedIn/POST_*.md
2. Human reviews and approves → Moves to Approved_LinkedIn/
3. LinkedIn poster picks up approved posts
4. Authenticates with LinkedIn (session cookies)
5. Creates post via Playwright automation
6. Moves to Posted_LinkedIn/ on success
7. Creates alert on failure
```

---

## Implementation Steps

### Phase 1: Session Management (1 hour)
1. Create LinkedIn session manager
2. Implement cookie-based authentication
3. Add session persistence
4. Handle re-authentication

**Files:**
- `scripts/linkedin_session.py`
- `AI_Employee_Vault/.state/linkedin_session.json`

### Phase 2: Post Creation Logic (2 hours)
1. Create LinkedIn poster class
2. Implement Playwright automation
   - Navigate to LinkedIn
   - Click "Start a post"
   - Enter post content
   - Handle media attachments (optional)
   - Click "Post"
3. Add error handling
4. Implement retry logic

**Files:**
- `watchers/linkedin_poster.py`

### Phase 3: Approval Workflow Integration (1 hour)
1. Create folder structure
   - `Pending_LinkedIn/`
   - `Approved_LinkedIn/`
   - `Posted_LinkedIn/`
2. Implement file watcher for approved posts
3. Add post validation
4. Create success/failure alerts

**Files:**
- Folder structure in vault
- Integration in `linkedin_poster.py`

### Phase 4: Scheduling & PM2 Integration (30 min)
1. Add LinkedIn poster to PM2 ecosystem
2. Configure check interval (every 5 minutes)
3. Add logging
4. Test auto-restart

**Files:**
- `ecosystem.config.json`

### Phase 5: Testing & Documentation (1 hour)
1. Create test post
2. Verify approval workflow
3. Test posting to LinkedIn
4. Update documentation
5. Create usage guide

**Files:**
- Test posts
- Updated skill documentation
- Usage examples

---

## Post File Format

### Draft Post (Pending_LinkedIn/)
```markdown
---
type: linkedin_post
status: pending
created: 2026-02-27T00:45:00Z
scheduled: null
---

# LinkedIn Post Draft

## Content
Just completed Phase 3 of my AI Employee automation project! 🤖

✅ 24/7 email monitoring
✅ WhatsApp integration
✅ Automated health checks
✅ Daily briefings

Building autonomous systems that work while you sleep.

#AI #Automation #ProductivityHacks

## Media
- None

## Settings
- Visibility: Public
- Comments: Enabled
- Reactions: Enabled
```

### Approved Post (Approved_LinkedIn/)
Same format, status changes to `approved`

### Posted (Posted_LinkedIn/)
Same format, adds:
```yaml
status: posted
posted_at: 2026-02-27T01:00:00Z
post_url: https://linkedin.com/posts/...
```

---

## Technical Implementation Details

### LinkedIn Automation with Playwright

```python
from playwright.sync_api import sync_playwright
import json
from pathlib import Path

class LinkedInPoster:
    def __init__(self, session_file="AI_Employee_Vault/.state/linkedin_session.json"):
        self.session_file = Path(session_file)
        self.browser = None
        self.context = None
        self.page = None

    def load_session(self):
        """Load saved session cookies."""
        if self.session_file.exists():
            with open(self.session_file) as f:
                return json.load(f)
        return None

    def save_session(self, cookies):
        """Save session cookies for reuse."""
        self.session_file.parent.mkdir(exist_ok=True)
        with open(self.session_file, 'w') as f:
            json.dump(cookies, f)

    def authenticate(self):
        """Authenticate with LinkedIn using saved session or manual login."""
        # Load saved cookies if available
        cookies = self.load_session()

        if cookies:
            self.context.add_cookies(cookies)
            # Verify session is still valid
            self.page.goto("https://www.linkedin.com/feed/")
            if "feed" in self.page.url:
                return True

        # Manual login required
        print("⚠️  LinkedIn session expired. Manual login required.")
        print("1. Browser will open to LinkedIn login page")
        print("2. Log in manually")
        print("3. Session will be saved for future use")

        self.page.goto("https://www.linkedin.com/login")
        # Wait for user to log in manually
        self.page.wait_for_url("**/feed/**", timeout=300000)  # 5 min timeout

        # Save session
        cookies = self.context.cookies()
        self.save_session(cookies)
        return True

    def create_post(self, content: str, media: list = None):
        """Create a LinkedIn post."""
        # Navigate to feed
        self.page.goto("https://www.linkedin.com/feed/")

        # Click "Start a post"
        self.page.click('button:has-text("Start a post")')

        # Wait for editor
        self.page.wait_for_selector('[contenteditable="true"]')

        # Enter content
        editor = self.page.locator('[contenteditable="true"]').first
        editor.fill(content)

        # Handle media if provided
        if media:
            # TODO: Implement media upload
            pass

        # Click Post button
        self.page.click('button:has-text("Post")')

        # Wait for post to complete
        self.page.wait_for_timeout(3000)

        return True
```

---

## Error Handling

### Common Errors
1. **Session Expired**
   - Detect: Login page appears
   - Action: Create alert for manual re-authentication
   - Recovery: Save new session after login

2. **Rate Limiting**
   - Detect: "You're posting too frequently" message
   - Action: Queue post for retry
   - Recovery: Exponential backoff (5min, 15min, 1hour)

3. **Network Errors**
   - Detect: Timeout or connection error
   - Action: Retry up to 3 times
   - Recovery: Create alert if all retries fail

4. **Post Validation Errors**
   - Detect: Content too long, invalid format
   - Action: Create alert with validation errors
   - Recovery: Human fixes and re-approves

---

## Security Considerations

### Session Management
- Store cookies in `.state/` folder (gitignored)
- Encrypt session file (optional enhancement)
- Auto-expire sessions after 30 days
- Never log credentials

### Rate Limiting
- Max 5 posts per hour
- Max 20 posts per day
- Track posting frequency
- Warn before hitting limits

### Content Validation
- Check for spam patterns
- Validate URLs
- Ensure proper formatting
- Respect character limits

---

## Testing Plan

### Test Cases
1. **Session Management**
   - ✓ Save session after login
   - ✓ Load session on restart
   - ✓ Detect expired session
   - ✓ Re-authenticate when needed

2. **Post Creation**
   - ✓ Create text-only post
   - ✓ Create post with hashtags
   - ✓ Create post with mentions
   - ✓ Handle long content
   - ✓ Handle special characters

3. **Approval Workflow**
   - ✓ Detect new approved posts
   - ✓ Process in order (oldest first)
   - ✓ Move to Posted on success
   - ✓ Create alert on failure

4. **Error Handling**
   - ✓ Handle session expiry
   - ✓ Handle network errors
   - ✓ Handle rate limiting
   - ✓ Handle validation errors

---

## Success Criteria

### Functional Requirements
- ✓ Can authenticate with LinkedIn
- ✓ Can create text posts
- ✓ Approval workflow working
- ✓ Posts move to Posted folder
- ✓ Alerts created on errors

### Non-Functional Requirements
- ✓ Runs as PM2 service
- ✓ Checks every 5 minutes
- ✓ Auto-restarts on failure
- ✓ Comprehensive logging
- ✓ Session persists across restarts

### Documentation
- ✓ Usage guide created
- ✓ Examples provided
- ✓ Troubleshooting documented
- ✓ Security notes included

---

## Timeline

**Total Estimated Time:** 4-6 hours

```
Hour 1: Session management + authentication
Hour 2-3: Post creation logic with Playwright
Hour 4: Approval workflow integration
Hour 5: PM2 integration + testing
Hour 6: Documentation + final testing
```

---

## Next Steps

1. Create LinkedIn session manager
2. Implement basic post creation
3. Test with real LinkedIn account
4. Add approval workflow
5. Integrate with PM2
6. Test end-to-end
7. Update documentation

---

**Plan Status:** Ready for implementation
**Approach:** Playwright automation (pragmatic)
**Risk Level:** Medium (ToS concerns, but faster)
**Estimated Completion:** 4-6 hours focused work
