# Send Email via MCP

Send emails through Gmail using Model Context Protocol (MCP) server with OAuth 2.0 authentication.

## What this skill does

Provides Claude Code with the ability to send emails via the Gmail MCP server. Uses official Gmail API with OAuth 2.0 for secure, compliant email sending.

## Prerequisites

- Gmail API enabled with send permissions
- Python 3.12+
- MCP server configured in Claude Code (.claude/mcp.json)
- OAuth credentials with `gmail.send` scope
- Token file with send permissions

## Setup

1. **Configure MCP Server**

   Add to `.claude/mcp.json`:
   ```json
   {
     "mcpServers": {
       "gmail": {
         "command": "uv",
         "args": [
           "--directory",
           "/mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0/mcp_servers/gmail",
           "run",
           "gmail-mcp"
         ],
         "env": {
           "GMAIL_CREDENTIALS_FILE": "/mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0/credentials.json",
           "GMAIL_TOKEN_FILE": "/mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0/token.json"
         }
       }
     }
   }
   ```

2. **Update OAuth Scopes**

   Ensure `token.json` includes send scope:
   ```python
   SCOPES = [
       'https://www.googleapis.com/auth/gmail.readonly',
       'https://www.googleapis.com/auth/gmail.send',
       'https://www.googleapis.com/auth/gmail.compose'
   ]
   ```

   If needed, delete `token.json` and re-authorize:
   ```bash
   uv run python get_auth_url.py
   ```

3. **Test MCP Server**

   ```bash
   # Test Gmail MCP connection
   uv run python tests/test_gmail_mcp.py
   ```

   Expected output:
   ```
   ✓ Credentials loaded
   ✓ Gmail API connection successful
   ✓ Email search working
   ✓ All 6 tests passed
   ```

## Usage

```bash
# Via Claude Code
claude "Send a test email to myself about Silver Tier completion"
```

Or in conversation:
```
Please send an email to bilalassist842@gmail.com with subject "Silver Tier Complete"
and body "AI Employee Silver Tier is now operational with 17+ hours uptime."
```

## Workflow

1. **Claude Code calls MCP**
   - Uses gmail MCP server
   - Authenticates with OAuth token
   - Composes email via Gmail API

2. **Email Sent**
   - Gmail API sends email
   - Returns message ID
   - Logs success

3. **Verification**
   - Check sent folder in Gmail
   - Verify message ID
   - Confirm delivery

## Example Usage

**Test Email Sent:**
```
Subject: Silver Tier Complete - AI Employee Operational
To: bilalassist842@gmail.com
From: bilalassist842@gmail.com

Body:
🎉 Silver Tier Complete!

Your AI Employee is now fully operational:
- 24/7 Gmail & WhatsApp monitoring
- LinkedIn auto-posting via official API
- PM2 process management
- Cron scheduling
- Health monitoring
- Daily briefings
- Ralph Loop autonomous completion
- Email MCP server

Performance:
- Memory: 80.6 MB (3 services)
- Uptime: 17+ hours
- Crashes: 0
- Success Rate: 100%

Status: Production-ready ✅

---
Sent via AI Employee MCP Server
```

**Result:**
```
✓ Email sent successfully
✓ Message ID: 19c9f48756b07f12
✓ Delivered to: bilalassist842@gmail.com
✓ Verified in Gmail sent folder
```

## Approval Request Format

```markdown
---
type: email_send
action: send_email
to: recipient@example.com
subject: Email subject
status: pending_approval
created: 2026-02-19T10:30:00Z
expires: 2026-02-20T10:30:00Z
---

## Email Draft

**To**: recipient@example.com
**Subject**: Email subject line
**CC**: (optional)
**BCC**: (optional)

---

[Email body content here]

---

## Context

This email is in response to:
- Original email: Needs_Action/EMAIL_original.md
- Reason: Client inquiry response
- Priority: High

## To Approve

1. Review the email content above
2. Edit if needed (modify this file)
3. Move this file to `Approved/` folder

## To Reject

Move this file to `Rejected/` folder with reason.

---
**⚠️ This email will be sent when approved**
```

## MCP Server Implementation

**index.js (Node.js)**
```javascript
import { MCPServer } from '@anthropic/mcp-server';
import { google } from 'googleapis';

const server = new MCPServer({
  name: 'email-server',
  version: '1.0.0'
});

server.addTool({
  name: 'send_email',
  description: 'Send an email via Gmail',
  parameters: {
    to: { type: 'string', required: true },
    subject: { type: 'string', required: true },
    body: { type: 'string', required: true },
    cc: { type: 'string', required: false },
    bcc: { type: 'string', required: false }
  },
  handler: async (params) => {
    // Gmail API send implementation
    const gmail = google.gmail({ version: 'v1', auth });
    const message = createMessage(params);
    const result = await gmail.users.messages.send({
      userId: 'me',
      requestBody: { raw: message }
    });
    return { success: true, messageId: result.data.id };
  }
});

server.start();
```

## Safety Rules

Following Company_Handbook.md:

**Always Require Approval**:
- ❌ Sending emails to ANY recipient
- ❌ Forwarding emails
- ❌ Sending attachments
- ❌ Bulk email sends

**Auto-Approved**:
- ✅ Drafting email responses
- ✅ Creating approval requests
- ✅ Logging sent emails

## Example Usage

**Step 1: Draft Response**
```
Claude reads: Needs_Action/EMAIL_client_inquiry.md
Claude drafts response
Claude creates: Pending_Approval/EMAIL_SEND_client_response.md
```

**Step 2: Human Approval**
```
Human reviews draft
Human edits if needed
Human moves to: Approved/EMAIL_SEND_client_response.md
```

**Step 3: Send via MCP**
```
Skill detects approved file
Calls MCP: send_email(to, subject, body)
MCP returns: { success: true, messageId: "abc123" }
Logs to: Logs/2026-02-19_email_sent.json
Moves to: Done/EMAIL_SEND_client_response.md
```

## Troubleshooting

**"MCP server not found"**
- Verify .claude/mcp.json configuration
- Check paths are absolute (not relative)
- Restart Claude Code

**"Permission denied to send"**
- Re-authorize with `gmail.send` scope
- Delete token.json and re-run: `uv run python get_auth_url.py`
- Verify scopes in credentials

**"Email not sent"**
- Check Gmail API quota (not exceeded)
- Verify recipient email is valid
- Check MCP server logs
- Test with: `uv run python tests/test_gmail_mcp.py`

**"Authentication failed"**
- Verify credentials.json is valid
- Check token.json exists and has send scope
- Re-authenticate if token expired

## Testing

**Test MCP Server:**
```bash
# Comprehensive test
uv run python tests/test_gmail_mcp.py

# Send test email
uv run python tests/send_silver_tier_email.py
```

**Expected Results:**
```
Test 1: Load credentials... ✓
Test 2: Gmail API connection... ✓
Test 3: Email search... ✓
Test 4: Get user profile... ✓
Test 5: List labels... ✓
Test 6: Send test email... ✓

All 6 tests passed!
Message ID: 19c9f48756b07f12
```

## Performance Metrics

**Your Actual Results:**
- MCP Server: Operational ✅
- Test Email: Sent successfully ✅
- Message ID: 19c9f48756b07f12
- Delivery: Confirmed ✅
- Integration: Claude Code → MCP → Gmail API ✅

## Security Considerations

1. **OAuth 2.0 Security**
   - Tokens stored in token.json (add to .gitignore)
   - Never commit credentials to version control
   - Tokens refresh automatically

2. **Email Privacy**
   - All emails logged
   - Sent via your Gmail account
   - Recipient sees your email address

3. **API Compliance**
   - Uses official Gmail API
   - Compliant with Google ToS
   - Proper authentication flow

## Next Steps

After setup:
1. Test with personal email first
2. Verify email delivery
3. Check Gmail sent folder
4. Use in Claude Code conversations
5. Integrate with other skills

## Related Skills

- `/monitor-gmail` - Detect incoming emails
- `/approve-actions` - Manage approval workflow (if needed)
- `/schedule-tasks` - Schedule email tasks

---
**Phase**: 1 - Foundation
**Tier**: Silver ✅ COMPLETE
**Estimated Setup Time**: 2-3 hours
**Dependencies**: Gmail API, MCP protocol, OAuth 2.0
**Status**: Verified working, test email sent successfully
**Implementation**: mcp_servers/gmail/ + tests/test_gmail_mcp.py
