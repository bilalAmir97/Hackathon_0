---
approval_id: whatsapp_reply_20260319_example
action_type: whatsapp_reply
created_at: 2026-03-19T20:00:00Z
expires_at: 2026-03-20T20:00:00Z
status: pending
risk_assessment: low
action_params:
  chat_name: "John Doe"
  message_text: "Thank you for your message! I'll get back to you shortly."
reasoning: |
  Automated reply to WhatsApp message from John Doe.
  Message detected with priority keyword "urgent".
  Suggested response acknowledges receipt and sets expectation.
---

## WhatsApp Reply Approval Request

**To**: John Doe
**Message**: "Thank you for your message! I'll get back to you shortly."

### Original Message Context
- **From**: John Doe
- **Received**: 2026-03-19 19:45:00
- **Content**: "Hi, I need urgent help with the invoice"
- **Priority**: High (keyword: urgent)

### Suggested Action
Send automated acknowledgment reply via WhatsApp Web.

### To Approve
Move this file to `/Approved` folder.

### To Reject
Move this file to `/Rejected` folder.

### Notes
- Reply will be sent via Playwright automation to WhatsApp Web
- Session must be active (logged in)
- Message will be logged in audit trail
