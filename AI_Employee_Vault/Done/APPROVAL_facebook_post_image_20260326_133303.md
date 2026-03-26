---
approval_id: facebook_post_image_20260326_133303
action_type: facebook_post_image
created_at: 2026-03-26T13:33:03Z
expires_at: 2026-03-27T13:33:03Z
status: pending
risk_assessment: low
action_params:
  image_path: "test_post.png"
  caption: "Testing the AI Employee automation system! 🤖 This post was created through an approval workflow with intelligent routing and audit logging. #AIEmployee #Automation"
reasoning: |
  Manual test of Facebook image posting workflow.
  Testing approval executor and Facebook Graph API integration.
---

## Facebook Image Post Approval Request

**Image**: test_post.png
**Caption**: Testing the AI Employee automation system! 🤖 This post was created through an approval workflow with intelligent routing and audit logging. #AIEmployee #Automation

### Test Purpose
This is a test to verify:
1. Approval executor detects file movement
2. Facebook MCP server posts image correctly
3. Audit logging captures the action
4. Post appears on Facebook page

### To Approve and Post
Move this file to the `Approved/` folder:
```bash
mv AI_Employee_Vault/Pending_Approval/APPROVAL_facebook_post_image_20260326_133303.md AI_Employee_Vault/Approved/
```

The approval-executor will automatically:
1. Detect the file movement
2. Execute the Facebook post action
3. Log the result in audit trail
4. Move the file to Done/

### To Reject
Move this file to the `Rejected/` folder instead.

### Notes
- Image will be posted via Facebook Graph API
- Facebook page access token must be configured
- Post will be logged in audit trail
- Check PM2 logs: `pm2 logs approval-executor`
