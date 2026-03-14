# Approve Actions Workflow

Manage human-in-the-loop approval workflow for sensitive actions requiring authorization before execution.

## What this skill does

Monitors the Pending_Approval folder, presents actions requiring human review, tracks approvals/rejections, and triggers execution of approved actions following Company_Handbook.md safety rules.

## Prerequisites

- Pending_Approval, Approved, and Rejected folders in vault
- Company_Handbook.md with approval rules
- Action execution skills (send-email, post-linkedin, etc.)
- Logging system configured

## Setup

1. **Verify Folder Structure**
   ```bash
   cd AI_Employee_Vault
   mkdir -p Pending_Approval Approved Rejected
   ```

2. **Configure Approval Rules**

   Add to Company_Handbook.md:
   ```markdown
   ## Approval Requirements

   ### Always Require Approval
   - Financial transactions (any amount)
   - Sending emails to new contacts
   - Posting on social media
   - Deleting files or data
   - Making commitments or promises
   - Sharing sensitive information

   ### Auto-Approve Thresholds
   - Reading and analyzing content
   - Creating summaries and reports
   - Moving files between folders
   - Logging activities

   ### Approval Expiration
   - High priority: 24 hours
   - Medium priority: 48 hours
   - Low priority: 72 hours
   - Expired approvals move to Rejected
   ```

3. **Set Environment Variables**
   ```bash
   # Add to .env
   APPROVAL_CHECK_INTERVAL=60
   APPROVAL_EXPIRATION_HOURS=24
   APPROVAL_NOTIFICATION=true
   ```

## Usage

```bash
claude /approve-actions
```

Or in conversation:
```
Please show me all pending approvals and help me review them.
```

## Workflow

### 1. Detection Phase
```
Scan Pending_Approval/ folder
├── Find all approval request files
├── Check expiration times
├── Sort by priority (high → medium → low)
└── Present to human for review
```

### 2. Review Phase
```
For each approval request:
├── Display action details
├── Show context and reasoning
├── Highlight risks or concerns
├── Present approve/reject/edit options
└── Wait for human decision
```

### 3. Execution Phase
```
If approved:
├── Move file to Approved/
├── Trigger appropriate action skill
├── Log execution result
└── Move to Done/ when complete

If rejected:
├── Move file to Rejected/
├── Log rejection reason
└── Update Dashboard
```

### 4. Cleanup Phase
```
Check for expired approvals:
├── Find requests past expiration time
├── Move to Rejected/ with reason
├── Notify human of expiration
└── Log expired items
```

## Approval Request Format

```markdown
---
type: approval_request
action: send_email | post_linkedin | payment | etc.
priority: high | medium | low
status: pending_approval
created: 2026-02-19T10:30:00Z
expires: 2026-02-20T10:30:00Z
risk_level: low | medium | high
---

## Action Summary
Brief description of what will happen when approved.

## Details
[Detailed information about the action]

## Context
Why this action is needed:
- Original trigger: [file or event]
- Related to: [project or task]
- Expected outcome: [result]

## Risk Assessment
- **Risk Level**: [low/medium/high]
- **Reversible**: [yes/no]
- **Impact**: [description]
- **Mitigation**: [safety measures]

## To Approve
1. Review all details above
2. Edit if needed (modify this file)
3. Move this file to `Approved/` folder

## To Reject
1. Move this file to `Rejected/` folder
2. Add rejection reason below:

**Rejection Reason**: [Your reason here]

---
**⚠️ This action will execute when approved**
```

## Approval Categories

### 1. Email Send Approval
```markdown
---
type: approval_request
action: send_email
to: recipient@example.com
subject: Email subject
risk_level: medium
---

## Email Draft
**To**: recipient@example.com
**Subject**: Subject line
**Body**: [email content]

## Context
Response to: Needs_Action/EMAIL_client_inquiry.md
```

### 2. Social Media Post Approval
```markdown
---
type: approval_request
action: post_linkedin
platform: linkedin
risk_level: high
---

## Post Content
[Post text with hashtags]

## Media
- Image: path/to/image.jpg
- Link: https://example.com

## Context
Scheduled post for business promotion
```

### 3. Payment Approval
```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Vendor Name
risk_level: high
---

## Payment Details
- Amount: $500.00
- To: Vendor Name (Account: XXXX1234)
- Reference: Invoice #1234
- Due Date: 2026-02-25

## Context
Monthly service payment
```

### 4. File Deletion Approval
```markdown
---
type: approval_request
action: delete_file
file_path: /path/to/file.txt
risk_level: high
---

## File Information
- Name: old_data.csv
- Size: 2.5 MB
- Last Modified: 2025-12-01
- Backup: Yes (in archive/)

## Reason
Cleanup of outdated data
```

## Safety Features

### 1. Expiration Tracking
```python
def check_expiration(approval_file):
    created = approval_file.metadata['created']
    expires = approval_file.metadata['expires']
    now = datetime.now()

    if now > expires:
        move_to_rejected(approval_file, reason="Expired")
        notify_human(f"Approval expired: {approval_file.name}")
```

### 2. Risk Assessment
```python
def assess_risk(action_type, details):
    risk_factors = {
        'new_recipient': +2,
        'large_amount': +3,
        'irreversible': +3,
        'public_post': +2,
        'sensitive_data': +3
    }

    score = sum(risk_factors[f] for f in detect_factors(details))

    if score >= 6:
        return 'high'
    elif score >= 3:
        return 'medium'
    else:
        return 'low'
```

### 3. Audit Trail
```json
{
  "timestamp": "2026-02-19T10:30:00Z",
  "action_type": "email_send",
  "approval_id": "APPROVAL_123",
  "decision": "approved",
  "approved_by": "human",
  "executed": true,
  "result": "success",
  "notes": "Client response approved after review"
}
```

## Example Usage

**Scenario**: Email response needs approval

**Step 1: Detection**
```
Scanning Pending_Approval/...

Found 3 pending approvals:

1. HIGH PRIORITY - Email to new client (expires in 4 hours)
   File: EMAIL_SEND_techstartup_2026-02-19.md
   Action: Send email to sarah@techstartup.io
   Risk: Medium (new contact)

2. MEDIUM PRIORITY - LinkedIn post (expires in 24 hours)
   File: LINKEDIN_POST_2026-02-19.md
   Action: Post business update
   Risk: High (public post)

3. LOW PRIORITY - Archive old files (expires in 48 hours)
   File: FILE_CLEANUP_2026-02-19.md
   Action: Delete 10 old files
   Risk: Low (backed up)
```

**Step 2: Review**
```
Reviewing: EMAIL_SEND_techstartup_2026-02-19.md

Action: Send email
To: sarah@techstartup.io
Subject: Re: Website Redesign Project Inquiry

Email Content:
---
Hi Sarah,

Thank you for reaching out about the website redesign...
[full email content]
---

Context:
- Response to client inquiry
- High priority (deadline Feb 21st)
- New contact (first email)

Risk Assessment:
- Risk Level: Medium
- Reversible: No (email cannot be unsent)
- Impact: Client relationship
- Mitigation: Professional tone, clear content

Options:
1. Approve (move to Approved/)
2. Reject (move to Rejected/)
3. Edit (modify content and re-review)
```

**Step 3: Human Decision**
```
Human reviews and approves by moving file to Approved/
```

**Step 4: Execution**
```
Detected approval: EMAIL_SEND_techstartup_2026-02-19.md
Executing: /send-email
Result: Email sent successfully (ID: msg_abc123)
Logged: Logs/2026-02-19_email_sent.json
Moved to: Done/EMAIL_SEND_techstartup_2026-02-19.md
Dashboard updated: 1 action completed
```

## Implementation

**utils/approval_manager.py**
```python
class ApprovalManager:
    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.pending = vault_path / 'Pending_Approval'
        self.approved = vault_path / 'Approved'
        self.rejected = vault_path / 'Rejected'

    def scan_pending(self):
        """Find all pending approval requests"""
        return list(self.pending.glob('*.md'))

    def check_expiration(self):
        """Move expired approvals to rejected"""
        for file in self.scan_pending():
            if self.is_expired(file):
                self.reject(file, reason="Expired")

    def execute_approved(self):
        """Execute actions in Approved folder"""
        for file in self.approved.glob('*.md'):
            action = self.parse_action(file)
            result = self.execute_action(action)
            self.log_result(file, result)
            self.move_to_done(file)

    def execute_action(self, action):
        """Route to appropriate action handler"""
        handlers = {
            'send_email': self.send_email,
            'post_linkedin': self.post_linkedin,
            'payment': self.make_payment,
            'delete_file': self.delete_file
        }
        return handlers[action.type](action)
```

## Troubleshooting

**"Approval not detected"**
- Verify file is in Pending_Approval/
- Check file format matches expected structure
- Ensure watcher is running

**"Action not executing after approval"**
- Check Approved/ folder for file
- Verify action type is supported
- Check logs for errors

**"Expired approvals not moving"**
- Verify expiration check is running
- Check timestamp format
- Review approval manager logs

**"Cannot edit approval request"**
- Open file in text editor
- Modify content
- Save and leave in Pending_Approval/

## Best Practices

1. **Review Promptly**
   - Check pending approvals daily
   - Prioritize high-risk actions
   - Don't let approvals expire

2. **Edit When Needed**
   - Fix typos in email drafts
   - Adjust post content
   - Modify amounts or details

3. **Document Rejections**
   - Always add rejection reason
   - Helps AI learn preferences
   - Improves future drafts

4. **Monitor Execution**
   - Check logs after approval
   - Verify actions completed
   - Review results

5. **Regular Audits**
   - Weekly review of approved actions
   - Monthly security audit
   - Quarterly policy review

## Security Considerations

1. **Access Control**
   - Only authorized users can approve
   - Vault should be password-protected
   - Consider 2FA for sensitive actions

2. **Audit Logging**
   - All approvals logged
   - Execution results tracked
   - Rejections documented

3. **Risk Thresholds**
   - High-risk actions require extra review
   - Multiple approvers for critical actions
   - Automatic rejection for policy violations

4. **Expiration Policy**
   - Prevents stale approvals
   - Forces re-review of old requests
   - Reduces security risk

## Metrics to Track

- Approval rate (approved vs rejected)
- Average review time
- Expiration rate
- Execution success rate
- Actions by type
- Risk distribution

## Next Steps

After setup:
1. Test with low-risk action
2. Review approval workflow
3. Adjust expiration times
4. Configure notifications
5. Train on approval process

## Related Skills

- `/send-email` - Email execution
- `/post-linkedin` - Social media posting
- `/monitor-gmail` - Email detection
- `/process-emails` - Email drafting

---
**Phase**: 1 - Foundation
**Tier**: Silver
**Estimated Setup Time**: 2-3 hours
**Dependencies**: Folder structure, Company_Handbook.md
