# QuickStart: WhatsApp Watcher

**Feature**: 002-whatsapp-watcher
**Time to Complete**: 15-20 minutes
**Prerequisites**: Python 3.13, uv package manager, WhatsApp account

## Overview

This guide walks you through setting up and testing the WhatsApp Watcher - a sensor component that monitors WhatsApp Web for priority messages and creates action files for human review.

## Step 1: Install Dependencies (5 minutes)

### Install Python Dependencies

```bash
# From project root
uv sync
```

This installs:
- Playwright 1.40+ (browser automation)
- watchdog, pyyaml, python-dotenv (already installed)

### Install Playwright Browsers

```bash
# Install Chromium browser (~300MB download)
uv run playwright install chromium

# Verify installation
uv run playwright --version
```

**Expected output**: `Version 1.40.0` (or higher)

## Step 2: Verify Vault Structure (1 minute)

```bash
# Check required directories exist
ls -la AI_Employee_Vault/Needs_Action/
ls -la AI_Employee_Vault/.state/
ls -la AI_Employee_Vault/Logs/
```

**Expected**: All directories should exist (created by existing Gmail watcher setup)

## Step 3: First Run - QR Code Authentication (5 minutes)

### Start the Watcher

```bash
# Run watcher manually (for first-time setup)
uv run python watchers/whatsapp_watcher.py
```

**What happens**:
1. Browser window opens to WhatsApp Web
2. QR code appears
3. Watcher waits for you to scan

### Scan QR Code

1. Open WhatsApp on your phone
2. Go to **Settings** → **Linked Devices** → **Link a Device**
3. Scan the QR code in the browser window
4. Wait for WhatsApp Web to load

**Expected output**:
```
============================================================
📱 WhatsApp Watcher - Silver Tier
============================================================
Vault: AI_Employee_Vault
Session: .whatsapp_session
Keywords: urgent, asap, important, help, invoice, payment, emergency, critical, deadline
Check interval: 30s
============================================================
✓ WhatsApp Web loaded
✓ No priority messages
```

### Stop the Watcher

Press `Ctrl+C` to stop gracefully.

**Expected output**:
```
⏹️  WhatsApp watcher stopped
```

**Session saved**: `.whatsapp_session/` directory now contains your login session (no QR code needed on next run)

## Step 4: Test Priority Message Detection (5 minutes)

### Send Test Message

1. From another phone or WhatsApp account, send yourself a message containing a priority keyword:
   ```
   URGENT: Test message for WhatsApp watcher
   ```

2. **Do not read the message** (must remain unread for detection)

### Run Watcher Again

```bash
uv run python watchers/whatsapp_watcher.py
```

**Expected output**:
```
✓ WhatsApp Web loaded
🔍 Checking WhatsApp Web... (10:30:45)
🔔 Priority message from [Your Name]
📝 Created action file: WHATSAPP_20260225_103045_your_name.md
✅ Found 1 priority message(s)
```

### Verify Action File Created

```bash
ls -lh AI_Employee_Vault/Needs_Action/WHATSAPP_*
```

**Expected**: One `.md` file with current timestamp

### View Action File

```bash
cat AI_Employee_Vault/Needs_Action/WHATSAPP_*.md
```

**Expected content**:
```yaml
---
type: whatsapp_message
from: Your Name
received: 2026-02-25T10:30:45.123456Z
priority: high
status: pending
original_timestamp: 10:30 AM
---

## WhatsApp Message from Your Name

**Received**: 10:30 AM

### Message Content

URGENT: Test message for WhatsApp watcher

### Suggested Actions

- [ ] Reply to Your Name
- [ ] Forward to relevant party
- [ ] Create task or reminder
- [ ] Archive after processing
```

### Stop Watcher

Press `Ctrl+C`

## Step 5: Test Idempotency (2 minutes)

### Restart Watcher

```bash
uv run python watchers/whatsapp_watcher.py
```

**Expected output**:
```
✓ WhatsApp Web loaded
✓ No priority messages
```

**Verify**: No duplicate action file created (idempotent operation working)

### Check State File

```bash
cat AI_Employee_Vault/.state/whatsapp_watcher_state.json
```

**Expected content**:
```json
{
  "processed_ids": [
    "Your_Name_10:30 AM_URGENT: Test message for WhatsApp watcher"
  ],
  "last_check": "2026-02-25T10:30:45.123456Z",
  "session_status": "active",
  "total_messages_processed": 1
}
```

## Step 6: Production Deployment (Optional)

### Run with PM2

```bash
# Start watcher as background service
pm2 start watchers/whatsapp_watcher.py --name whatsapp-watcher --interpreter python3

# Save PM2 configuration
pm2 save

# Enable startup on boot
pm2 startup
```

### Monitor Watcher

```bash
# Check status
pm2 status whatsapp-watcher

# View logs
pm2 logs whatsapp-watcher

# Stop watcher
pm2 stop whatsapp-watcher
```

## Configuration

### Change Priority Keywords

Edit `watchers/whatsapp_watcher.py`:

```python
watcher = WhatsAppWatcher(
    priority_keywords=['urgent', 'asap', 'custom', 'keyword']
)
```

### Change Polling Interval

```python
watcher = WhatsAppWatcher(
    check_interval=60  # Check every 60 seconds instead of 30
)
```

### Enable Dry-Run Mode

```python
# Set environment variable
export DRY_RUN=true

# Or modify code
watcher = WhatsAppWatcher(dry_run=True)
```

**Dry-run mode**: Detections logged but no action files created (for testing)

## Troubleshooting

### Issue: QR Code Not Appearing

**Cause**: Browser not launching or WhatsApp Web not loading

**Solution**:
```bash
# Check Playwright installation
uv run playwright install chromium --force

# Try with visible browser (default)
uv run python watchers/whatsapp_watcher.py
```

### Issue: "Please scan QR code" Every Time

**Cause**: Session not persisting

**Solution**:
```bash
# Check session directory exists
ls -la .whatsapp_session/

# Ensure directory is writable
chmod 700 .whatsapp_session/

# Don't run multiple instances simultaneously
```

### Issue: No Messages Detected

**Cause**: Multiple possibilities

**Debug**:
1. Verify message is unread in WhatsApp
2. Check message contains priority keyword
3. Verify watcher is running: `pm2 status whatsapp-watcher`
4. Check logs: `tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`

### Issue: Browser Closes Immediately

**Cause**: Playwright not installed correctly

**Solution**:
```bash
uv run playwright install chromium
uv run playwright install-deps
```

### Issue: Session Expired

**Symptom**: QR code appears despite previous login

**Solution**:
1. Scan QR code again (sessions expire ~30 days)
2. Check for alert file in `/Needs_Action`
3. Session will persist after re-authentication

## Testing Checklist

- [ ] Playwright browsers installed
- [ ] Watcher starts without errors
- [ ] QR code scan successful (first run)
- [ ] Session persists across restarts
- [ ] Priority message detected
- [ ] Action file created in `/Needs_Action`
- [ ] Action file has valid YAML frontmatter
- [ ] No duplicate files on restart (idempotency)
- [ ] State file updated correctly
- [ ] Logs written to `/Logs/YYYY-MM-DD.json`
- [ ] Graceful shutdown on Ctrl+C

## Integration with Approval Workflow

The WhatsApp Watcher integrates seamlessly with the existing approval workflow:

```
WhatsApp message arrives
  ↓
Watcher detects (if priority keyword)
  ↓
Action file created in /Needs_Action
  ↓
Human reviews message
  ↓
Human creates APPROVAL_*.md (if reply needed)
  ↓
Human moves to /Approved
  ↓
Approval executor processes (future: WhatsApp MCP for replies)
```

**Current limitation**: WhatsApp reply MCP not yet implemented (Silver Tier is monitoring only)

## Next Steps

1. ✅ WhatsApp Watcher operational
2. ⏭️ Test with real business messages
3. ⏭️ Configure custom priority keywords
4. ⏭️ Run 24-hour stability test
5. ⏭️ Integrate with daily workflow

## Support

- **Specification**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **Existing Code**: `watchers/whatsapp_watcher.py`

## Success Criteria

✅ **Complete** when:
- Priority messages detected within 60 seconds
- Action files created with valid format
- No duplicates across restarts
- 24-hour continuous operation without crashes
- Integration with approval workflow verified

**Estimated time to production-ready**: 1-2 hours (including testing)
