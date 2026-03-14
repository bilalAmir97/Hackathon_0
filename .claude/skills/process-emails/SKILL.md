# Process Email Action Items

Process email action items from Needs_Action folder, analyze content, and draft appropriate responses.

## What this skill does

Reads email action items created by `/monitor-gmail`, analyzes the content using Company_Handbook.md rules, drafts appropriate responses, and creates approval requests for sending.

## Prerequisites

- Email action items in Needs_Action/ folder
- Company_Handbook.md with response guidelines
- Access to previous email history (optional)
- Email templates (optional)

## Setup

1. **Create Email Templates** (optional)
   ```bash
   mkdir -p AI_Employee_Vault/Templates/Email
   ```

2. **Configure Response Rules**

   Add to Company_Handbook.md:
   ```markdown
   ## Email Response Guidelines

   ### Response Time
   - High priority: Within 4 hours
   - Medium priority: Within 24 hours
   - Low priority: Within 48 hours

   ### Tone
   - Professional and courteous
   - Clear and concise
   - Action-oriented

   ### Auto-Response Scenarios
   - Out of office: Auto-reply with return date
   - Common questions: Use template responses
   - Spam/Newsletter: Archive without response
   ```

3. **Set Environment Variables**
   ```bash
   # Add to .env
   EMAIL_SIGNATURE="Best regards,\nYour Name\nYour Title\nCompany Name"
   EMAIL_RESPONSE_DELAY=300  # seconds before drafting
   ```

## Usage

```bash
claude /process-emails
```

Or in conversation:
```
Please process all email action items in Needs_Action and draft responses.
```

## Workflow

1. **Scan Needs_Action**
   - Find all files with `type: email`
   - Sort by priority (high → medium → low)
   - Check status (pending only)

2. **Analyze Each Email**
   - Read email content
   - Identify intent (question, request, inquiry, etc.)
   - Check Company_Handbook.md for relevant rules
   - Determine if response is needed

3. **Draft Response**
   - Generate appropriate reply based on context
   - Include relevant information
   - Add signature
   - Format professionally

4. **Create Approval Request**
   - Write draft to Pending_Approval/
   - Include original email context
   - Add suggested actions
   - Set expiration time

5. **Update Dashboard**
   - Log processing activity
   - Update stats
   - Flag urgent items

## Response Types

### 1. Client Inquiry Response
```markdown
Subject: Re: [Original Subject]

Hi [Client Name],

Thank you for reaching out regarding [topic].

[Answer their questions]

[Provide next steps]

[Call to action]

Best regards,
[Your Name]
```

### 2. Meeting Request Response
```markdown
Subject: Re: [Meeting Request]

Hi [Name],

Thank you for the meeting invitation.

I'm available on:
- [Option 1]
- [Option 2]
- [Option 3]

Please let me know which works best for you.

Best regards,
[Your Name]
```

### 3. Information Request Response
```markdown
Subject: Re: [Information Request]

Hi [Name],

Here's the information you requested:

[Provide information]

Let me know if you need anything else.

Best regards,
[Your Name]
```

### 4. No Response Needed
```markdown
# Action: Archive

This email is:
- Newsletter/Marketing
- Automated notification
- FYI only

No response required. Moving to Done.
```

## Analysis Process

**Step 1: Intent Detection**
```
Question → Provide answer
Request → Confirm or decline
Inquiry → Provide information
Meeting → Suggest times
Complaint → Acknowledge and resolve
Spam → Archive
```

**Step 2: Context Gathering**
```
- Previous emails from sender
- Related projects or tasks
- Company policies
- Available resources
```

**Step 3: Response Generation**
```
- Address all questions
- Provide clear next steps
- Set expectations
- Include relevant links/attachments
```

**Step 4: Quality Check**
```
- Professional tone
- No typos or errors
- All questions answered
- Clear call to action
```

## Example Processing

**Input**: Email action item
```markdown
---
type: email
from: sarah@techstartup.io
subject: Website Redesign Project Inquiry
priority: high
---

Hi, we need a website redesign by March 25th.
Budget is $15K-$25K. Can you help?
```

**Processing**:
1. Detect: Client inquiry, high priority
2. Analyze: Website project, tight timeline, defined budget
3. Context: Check portfolio, availability, pricing
4. Draft response addressing timeline, experience, next steps

**Output**: Approval request
```markdown
---
type: email_send
to: sarah@techstartup.io
subject: Re: Website Redesign Project Inquiry
status: pending_approval
---

Hi Sarah,

Thank you for reaching out about the website redesign project.

I've reviewed your requirements and I'm interested in working
with TechStartup Inc. The March 25th timeline is ambitious but
potentially feasible.

I'd love to discuss this in detail. Are you available for a
call this week?

Best regards,
[Your Name]
```

## Safety Rules

Following Company_Handbook.md:

**Auto-Approved**:
- ✅ Reading email action items
- ✅ Analyzing content
- ✅ Drafting responses
- ✅ Creating approval requests

**Requires Approval**:
- ❌ Sending any email
- ❌ Making commitments
- ❌ Providing pricing
- ❌ Scheduling meetings

## Advanced Features

### 1. Template Matching
```python
# Match email to template
if "meeting" in subject.lower():
    template = "meeting_response"
elif "inquiry" in subject.lower():
    template = "client_inquiry"
else:
    template = "general_response"
```

### 2. Sentiment Analysis
```python
# Detect urgency and tone
if any(word in body for word in ["urgent", "asap", "critical"]):
    priority = "high"
    response_time = "4 hours"
```

### 3. Smart Suggestions
```python
# Suggest actions based on content
if "invoice" in body:
    suggest_actions = ["Check payment status", "Send invoice", "Follow up"]
```

### 4. Context Enrichment
```python
# Add relevant context
previous_emails = get_email_history(sender)
related_projects = find_related_projects(keywords)
```

## Troubleshooting

**"No email action items found"**
- Run `/monitor-gmail` first
- Check Needs_Action/ folder
- Verify file format

**"Draft quality is poor"**
- Improve Company_Handbook.md guidelines
- Add more context to action items
- Use email templates

**"Wrong response type"**
- Refine intent detection keywords
- Add more examples to handbook
- Review email classification

**"Missing information in draft"**
- Ensure action item has full email content
- Add context from previous emails
- Include relevant project details

## Implementation Files

**utils/email_processor.py**
```python
class EmailProcessor:
    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.handbook = self.load_handbook()

    def process_email_action(self, action_file):
        # Read action item
        # Analyze content
        # Draft response
        # Create approval request
        pass

    def detect_intent(self, email_content):
        # Intent detection logic
        pass

    def draft_response(self, email, intent):
        # Response generation
        pass
```

**Templates/Email/**
- `client_inquiry.md` - Client inquiry template
- `meeting_request.md` - Meeting response template
- `general_response.md` - General response template
- `out_of_office.md` - Auto-reply template

## Performance Metrics

Track these metrics:
- Emails processed per day
- Average processing time
- Response quality score (human feedback)
- Approval rate (approved vs rejected)
- Response time (detection to send)

## Best Practices

1. **Always include context** - Reference original email
2. **Be specific** - Provide clear next steps
3. **Set expectations** - Timeline, deliverables, process
4. **Professional tone** - Courteous, clear, action-oriented
5. **Proofread** - Check for errors before approval

## Next Steps

After processing:
1. Review drafts in Pending_Approval/
2. Edit if needed
3. Move to Approved/ to send
4. Use `/send-email` to execute

## Related Skills

- `/monitor-gmail` - Detect incoming emails
- `/send-email` - Send approved responses
- `/approve-actions` - Manage approval workflow

---
**Phase**: 1 - Foundation
**Tier**: Silver
**Estimated Setup Time**: 2-3 hours
**Dependencies**: monitor-gmail, Company_Handbook.md
