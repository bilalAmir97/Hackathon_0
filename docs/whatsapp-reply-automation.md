# WhatsApp Reply Automation - Setup Guide

## Overview

The WhatsApp reply automation system enables your AI Employee to automatically respond to WhatsApp messages through a human-in-the-loop approval workflow.

## Architecture

```
WhatsApp Web → Watcher (Detect) → Processor (Classify) → Approval Request → Human Approval → MCP Server (Send)
```

## Components

### 1. WhatsApp Watcher (`watchers/whatsapp_watcher.py`)
- Monitors WhatsApp Web for unread messages
- Detects priority keywords
- Creates action files in `Needs_Action/`

### 2. WhatsApp Processor (`scripts/whatsapp_processor.py`)
- Processes action files from `Needs_Action/`
- Classifies messages (priority, personal, group, ignored)
- Generates auto-response suggestions
- Creates approval requests in `Pending_Approval/`

### 3. WhatsApp MCP Server (`mcp_servers/whatsapp_mcp_server.py`)
- Sends messages via Playwright automation
- Uses persistent browser session
- Includes retry logic and circuit breaker

### 4. Approval Executor (`scripts/approval_executor.py`)
- Monitors `Approved/` folder
- Executes approved WhatsApp replies
- Logs all actions to audit trail

## Setup Instructions

### Step 1: Configure Auto-Responses

Edit `config/whatsapp_rules.json`:

```json
{
  "auto_response_settings": {
    "enabled": true
  },
  "keyword_responses": {
    "urgent": {
      "enabled": true,
      "response": "I understand this is urgent. I'm on it!"
    }
  }
}
```

### Step 2: Start WhatsApp Watcher

```bash
# Start watcher (will prompt for QR code on first run)
uv run python watchers/whatsapp_watcher.py
```

Scan QR code with your phone. Session persists for ~30 days.

### Step 3: Start WhatsApp Processor

```bash
# Start processor (monitors Needs_Action folder)
uv run python scripts/auto_process_whatsapp.py
```

### Step 4: Start Approval Executor

```bash
# Start executor (monitors Approved folder)
uv run python scripts/approval_executor.py
```

## Complete Workflow Example

### 1. Message Arrives
Someone sends: "Hi, I need urgent help with the invoice"

### 2. Watcher Detects
- Detects unread message with keyword "urgent"
- Creates `WHATSAPP_John_Doe_20260319_200000.md` in `Needs_Action/`

### 3. Processor Classifies
- Reads action file
- Classifies as "priority" (keyword: urgent)
- Generates auto-response: "I understand this is urgent. I'm on it!"
- Creates `APPROVAL_whatsapp_reply_John_Doe_20260319_200000.md` in `Pending_Approval/`

### 4. Human Reviews
- Open `Pending_Approval/` folder
- Review approval request
- Move to `Approved/` folder to approve (or `Rejected/` to reject)

### 5. Executor Sends
- Detects file in `Approved/`
- Calls WhatsApp MCP server
- Sends reply via Playwright
- Logs action to audit trail
- Moves file to `Done/`

## Testing

### Test Direct Sending

```bash
# Test sending a message directly
uv run python tests/test_whatsapp_reply.py
# Select option 1
```

### Test Approval Workflow

```bash
# Test the complete workflow
uv run python tests/test_whatsapp_reply.py
# Select option 2
```

### Manual Test via CLI

```bash
# Send a test message
uv run python mcp_servers/whatsapp_mcp_server.py "John Doe" "Test message"
```

## Configuration Options

### Priority Keywords
Messages containing these keywords trigger priority classification:
- urgent, asap, important, help, invoice, payment, emergency, critical, deadline

### Sender-Specific Rules
Configure custom responses for specific contacts:

```json
{
  "sender_rules": {
    "Boss": {
      "classification": "priority",
      "auto_respond": true,
      "response_template": "Got it! I'll handle this right away."
    }
  }
}
```

### Keyword-Based Responses
Configure responses for specific keywords:

```json
{
  "keyword_responses": {
    "invoice": {
      "enabled": true,
      "response": "Thank you for your inquiry about the invoice..."
    }
  }
}
```

## Troubleshooting

### Session Expired
If WhatsApp session expires:
1. Stop the watcher
2. Delete `.whatsapp_session/` directory
3. Restart watcher and scan QR code

### Message Not Detected
- Check if keyword is in `priority_keywords` list
- Verify watcher is running
- Check `.state/whatsapp_watcher_state.json` for processed messages

### Reply Not Sent
- Verify WhatsApp Web session is active
- Check browser is not in headless mode (WhatsApp blocks headless)
- Review error logs in `Logs/YYYY-MM-DD.json`

### Approval Not Executed
- Verify approval executor is running
- Check file is in `Approved/` folder (not `Pending_Approval/`)
- Verify approval file has correct YAML frontmatter

## PM2 Integration

Add to `ecosystem.config.json`:

```json
{
  "name": "whatsapp-processor",
  "script": "uv",
  "args": "run python scripts/auto_process_whatsapp.py",
  "autorestart": true
}
```

Start with PM2:
```bash
pm2 start ecosystem.config.json
pm2 status
```

## Security Notes

- WhatsApp session stored in `.whatsapp_session/` (gitignored)
- All replies require human approval
- Audit trail logs all sent messages
- Session expires after ~30 days of inactivity

## Gold Tier Compliance

✅ **Read Messages**: Playwright-based detection with keyword filtering
✅ **Reply to Messages**: Playwright automation with approval workflow
✅ **Session Persistence**: Persistent browser context
✅ **Error Recovery**: Retry logic and circuit breakers
✅ **Audit Logging**: Complete audit trail
✅ **Human-in-the-Loop**: All replies require approval

## Next Steps

1. Configure `config/whatsapp_rules.json` with your keywords and responses
2. Start all services (watcher, processor, executor)
3. Test with a real WhatsApp message
4. Review and approve the generated approval request
5. Verify message is sent successfully
