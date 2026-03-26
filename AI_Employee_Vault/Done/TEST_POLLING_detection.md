---
approval_id: TEST_POLLING_20260326_164500
action_type: email_send
email_action_ref: send_email
action_params:
  recipient: test@example.com
  subject: "Test Polling Detection"
  body: |
    This is a test email to verify that the polling mechanism detects files automatically without requiring a restart.
risk_assessment: low
reasoning: Testing the new polling mechanism for watchdog fallback
created_at: 2026-03-26T16:45:00Z
metadata:
  test: true
  purpose: verify_polling_detection
---

# Test Approval Request - Polling Detection

This file is created to test if the approval-executor's new polling mechanism (every 30 seconds) can detect files moved to Approved/ folder without requiring a manual restart.

## Test Instructions

1. Move this file to Approved/ folder
2. Wait up to 30 seconds (do NOT restart approval-executor)
3. Check logs to see if polling detected the file
4. Expected: File should be processed automatically

## Approval Decision

**[ ] APPROVE** - Move to Approved/ to test polling
**[ ] REJECT** - Move to Rejected/ to cancel test
