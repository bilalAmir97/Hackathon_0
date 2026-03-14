# Quickstart Guide: Gmail Watcher + Approval Workflow

**Feature**: 001-gmail-approval-workflow
**Created**: 2026-02-25
**Audience**: Developers setting up Silver Tier for the first time

## Prerequisites

- Python 3.10+ installed
- Gmail account with API access
- Google Cloud Console access
- Obsidian installed (optional, for vault visualization)
- Git repository cloned

## Setup Steps

### 1. Gmail API Credentials Setup

**Create Google Cloud Project:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "AI-Employee-Gmail"
3. Enable Gmail API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

**Create OAuth 2.0 Credentials:**

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Configure OAuth consent screen (if first time):
   - User Type: External
   - App name: "AI Employee Gmail Watcher"
   - User support email: your email
   - Developer contact: your email
   - Add test users: your Gmail address
4. Application type: "Desktop app"
5. Name: "AI Employee Desktop Client"
6. Click "Create"
7. Download credentials JSON file
8. Save as `credentials.json` in project root

**Set OAuth Scopes:**

1. Go to "OAuth consent screen"
2. Click "Edit App"
3. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
4. Save and continue

### 2. Environment Configuration

**Create .env file:**

```bash
# Copy example environment file
cp .env.example .env
```

**Edit .env with your settings:**

```bash
# Gmail Configuration
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
GMAIL_CHECK_INTERVAL=120  # seconds (2 minutes)

# Priority Keywords Configuration
# Comma-separated list of keywords to detect important emails
PRIORITY_KEYWORDS=urgent,important,asap,invoice,payment,client,deadline,action required,critical,emergency

# Priority Matching Rules:
# - Case-insensitive: "URGENT" matches "urgent"
# - Searches: Both subject AND body
# - Whole word: "urgent" does NOT match "urgently"
# - Logic: ANY keyword triggers priority (OR logic)
PRIORITY_MATCH_CASE_SENSITIVE=false
PRIORITY_MATCH_LOCATION=subject_and_body
PRIORITY_MATCH_WHOLE_WORD=true
PRIORITY_MATCH_LOGIC=any

# Vault Configuration
VAULT_PATH=./AI_Employee_Vault

# Logging
LOG_LEVEL=INFO
DRY_RUN=false  # Set to true for testing without sending emails

# Retry Configuration
# Exponential backoff: delay = (base ** attempt) + random(0, jitter)
# Example: attempt 1 = 2s + jitter, attempt 2 = 4s + jitter, attempt 3 = 8s + jitter
MAX_RETRIES=3
RETRY_BACKOFF_BASE=2
RETRY_JITTER_MAX=1.0
RETRY_MAX_TOTAL_WAIT=30  # Max total wait across all retries (seconds)

# Rate limit handling (longer delays for API quota issues)
RETRY_RATE_LIMIT_BACKOFF_BASE=5
RETRY_RATE_LIMIT_MAX_RETRIES=5
```

### 3. Python Environment Setup

**Install dependencies:**

```bash
# Activate virtual environment (if using uv)
source .venv/bin/activate

# Install Silver tier dependencies
pip install google-auth-oauthlib google-auth google-api-python-client watchdog python-dotenv pytest

# Or using uv
uv pip install google-auth-oauthlib google-auth google-api-python-client watchdog python-dotenv pytest
```

### 4. OAuth Token Generation

**Run OAuth flow:**

```bash
# Activate virtual environment
source .venv/bin/activate

# Run OAuth setup script
python test_gmail_oauth.py
```

**Follow the prompts:**

1. Script will display authorization URL
2. Copy URL and open in browser
3. Select your Gmail account
4. Grant permissions (read and send)
5. Copy authorization code from browser
6. Paste code back in terminal
7. Script will create `token.json`

**Verify token creation:**

```bash
ls -lh token.json
# Should show file with ~2KB size
```

### 5. Vault Structure Validation

**Verify vault directories exist:**

```bash
ls -la AI_Employee_Vault/
```

**Expected structure:**

```
AI_Employee_Vault/
├── Inbox/
├── Needs_Action/
├── Pending_Approval/
├── Approved/
├── Rejected/
├── Done/
├── Plans/
├── Logs/
├── Company_Handbook.md
└── Dashboard.md
```

**Create missing directories (if needed):**

```bash
mkdir -p AI_Employee_Vault/{Inbox,Needs_Action,Pending_Approval,Approved,Rejected,Done,Plans,Logs}
```

### 6. Test Gmail Watcher

**Run watcher in dry-run mode:**

```bash
# Set dry-run mode
export DRY_RUN=true

# Run Gmail watcher
python watchers/gmail_watcher.py
```

**Expected output:**

```
============================================================
📧 Gmail Watcher - Silver Tier
============================================================
Vault: ./AI_Employee_Vault
Check interval: 120 seconds
============================================================
✅ Authenticated as: your-email@gmail.com
📬 Found 3 unread messages
🔍 Detected 1 priority email
✅ Created action item: EMAIL_20260225_143022_sender.md
```

**Verify action file created:**

```bash
ls -lh AI_Employee_Vault/Needs_Action/
# Should show EMAIL_*.md file
```

### 7. Test Approval Workflow

**Manual approval test:**

1. Check action file in `Needs_Action/`
2. Review email details
3. Move file to `Pending_Approval/`
4. Review approval request
5. Move to `Approved/` (to approve) or `Rejected/` (to reject)
6. Check `Logs/` for execution log

**Run approval executor:**

```bash
# Disable dry-run mode for actual execution
export DRY_RUN=false

# Run approval executor
python scripts/approval_executor.py
```

### 8. Verify Logging

**Check log file:**

```bash
# View today's log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq .
```

**Expected log entry:**

```json
{
  "timestamp": "2026-02-25T14:30:22.123Z",
  "log_id": "550e8400-e29b-41d4-a716-446655440000",
  "action_type": "email_detected",
  "email_id": "abc123xyz",
  "status": "success",
  "inputs": {
    "from": "sender@example.com",
    "subject": "Urgent: Client Request"
  }
}
```

## Running in Production

### Start Gmail Watcher (Background)

```bash
# Using PM2
pm2 start watchers/gmail_watcher.py --name gmail-watcher --interpreter python3

# Or using nohup
nohup python watchers/gmail_watcher.py > logs/gmail-watcher.log 2>&1 &
```

### Start Approval Executor (Background)

```bash
# Using PM2
pm2 start scripts/approval_executor.py --name approval-executor --interpreter python3

# Or using nohup
nohup python scripts/approval_executor.py > logs/approval-executor.log 2>&1 &
```

### Monitor Processes

```bash
# PM2 status
pm2 status

# PM2 logs
pm2 logs gmail-watcher
pm2 logs approval-executor

# Or check nohup logs
tail -f logs/gmail-watcher.log
tail -f logs/approval-executor.log
```

## Troubleshooting

### OAuth Token Expired

**Symptom**: "Token expired" error in logs

**Solution**:
```bash
# Delete old token
rm token.json

# Re-run OAuth flow
python test_gmail_oauth.py
```

### Gmail API Rate Limit

**Symptom**: "Rate limit exceeded" error

**Solution**:
- Increase `GMAIL_CHECK_INTERVAL` in .env (e.g., 300 seconds)
- Wait for quota reset (usually 1 minute)
- Check quota usage in Google Cloud Console

### No Emails Detected

**Symptom**: Watcher runs but no action files created

**Solution**:
- Check `PRIORITY_KEYWORDS` in .env
- Verify emails are unread in Gmail
- Check watcher logs for filtering logic
- Test with known priority email

### File Permission Errors

**Symptom**: "Permission denied" when creating files

**Solution**:
```bash
# Fix vault permissions
chmod -R u+rw AI_Employee_Vault/

# Verify ownership
ls -la AI_Employee_Vault/
```

### Duplicate Action Files

**Symptom**: Same email creates multiple action files

**Solution**:
- Check `AI_Employee_Vault/.state/gmail_watcher_state.json`
- Verify `processed_email_ids` contains email IDs
- If corrupted, delete state file (will reprocess all unread emails once)

## Testing Checklist

- [ ] OAuth token created successfully
- [ ] Gmail watcher detects priority emails
- [ ] Action files created in Needs_Action/
- [ ] No duplicate action files after restart
- [ ] Approval workflow moves files correctly
- [ ] Approved actions execute (in dry-run mode first)
- [ ] Rejected actions skip execution
- [ ] Logs created with all required fields
- [ ] Token refresh works automatically
- [ ] Error handling creates alerts

## Next Steps

1. Review [data-model.md](./data-model.md) for entity schemas
2. Review [contracts/](./contracts/) for file format specifications
3. Run `/sp.tasks` to generate implementation tasks
4. Implement user stories in priority order (P1 → P2 → P3 → P4)
5. Create ADRs for significant architectural decisions

## Support

- Constitution: `.specify/memory/constitution.md`
- Spec: `specs/001-gmail-approval-workflow/spec.md`
- Plan: `specs/001-gmail-approval-workflow/plan.md`
- Issues: Create in project repository
