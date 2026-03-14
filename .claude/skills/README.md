# Silver Tier Skills - Complete Guide

This directory contains all Agent Skills required to build a Silver tier AI Employee.

## 📚 Skills Overview

### Phase 1: Foundation (Week 1)
Core infrastructure for email monitoring and sending.

1. **[monitor-gmail](./monitor-gmail/SKILL.md)** ⏱️ 3-4 hours
   - Monitor Gmail inbox for important emails
   - Create action items automatically
   - Priority detection based on keywords
   - **Prerequisites**: Gmail API, OAuth credentials

2. **[send-email](./send-email/SKILL.md)** ⏱️ 4-5 hours
   - Send emails via MCP server
   - Human approval workflow
   - Gmail API integration
   - **Prerequisites**: MCP server, Gmail API with send scope

3. **[process-emails](./process-emails/SKILL.md)** ⏱️ 2-3 hours
   - Analyze email action items
   - Draft appropriate responses
   - Create approval requests
   - **Prerequisites**: monitor-gmail, Company_Handbook.md

4. **[approve-actions](./approve-actions/SKILL.md)** ⏱️ 2-3 hours
   - Manage approval workflow
   - Track pending/approved/rejected actions
   - Execute approved actions
   - **Prerequisites**: Folder structure, Company_Handbook.md

**Phase 1 Total**: ~12-15 hours

---

### Phase 2: Monitoring (Week 2)
Expand monitoring to additional channels.

5. **[monitor-whatsapp](./monitor-whatsapp/SKILL.md)** ⏱️ 5-6 hours
   - Monitor WhatsApp Web for messages
   - Keyword-based priority detection
   - Create action items from messages
   - **Prerequisites**: Playwright, WhatsApp account
   - **⚠️ Warning**: May violate WhatsApp ToS

**Phase 2 Total**: ~5-6 hours

---

### Phase 3: Automation (Week 3)
Enable continuous operation and autonomous task completion.

6. **[schedule-tasks](./schedule-tasks/SKILL.md)** ⏱️ 2-3 hours
   - Schedule watchers to run 24/7
   - Configure cron or Task Scheduler
   - Process management with PM2
   - **Prerequisites**: PM2 or supervisord, system access

7. **[reasoning-loop](./reasoning-loop/SKILL.md)** ⏱️ 3-4 hours
   - Claude autonomous task completion
   - Ralph Wiggum Stop hook pattern
   - Multi-step task processing
   - **Prerequisites**: Claude Code hooks, orchestrator

**Phase 3 Total**: ~5-7 hours

---

### Phase 4: Business Value (Week 4)
Add business-focused automation for lead generation.

8. **[post-linkedin](./post-linkedin/SKILL.md)** ⏱️ 4-5 hours
   - Automatically post to LinkedIn
   - Content generation from vault
   - Human approval workflow
   - **Prerequisites**: LinkedIn account, API or Playwright
   - **⚠️ Warning**: Automation may violate LinkedIn ToS

**Phase 4 Total**: ~4-5 hours

---

## 🎯 Silver Tier Requirements Checklist

- [x] All Bronze requirements
- [x] Two or more Watcher scripts (Gmail + WhatsApp)
- [x] Automatically Post on LinkedIn
- [x] Claude reasoning loop with Plan.md files
- [x] One working MCP server (email sending)
- [x] Human-in-the-loop approval workflow
- [x] Basic scheduling via cron or Task Scheduler
- [x] All AI functionality as Agent Skills

**Total Estimated Time**: 26-33 hours (within 20-30 hour estimate)

---

## 🚀 Quick Start Guide

### Step 1: Prerequisites (Day 0)
```bash
# Install dependencies
pip install google-auth google-auth-oauthlib google-api-python-client
pip install playwright
playwright install chromium
npm install -g pm2

# Verify installations
python --version  # 3.10+
node --version    # 18+
claude --version  # Latest
```

### Step 2: Gmail Setup (Day 1-2)
```bash
# 1. Enable Gmail API in Google Cloud Console
# 2. Download credentials.json
# 3. Test authentication
python utils/gmail_auth.py

# 4. Test monitoring
claude /monitor-gmail
```

### Step 3: Email MCP Server (Day 3-4)
```bash
# 1. Create MCP server
cd mcp-servers/email-server
npm init -y

# 2. Configure Claude Code
# Edit ~/.config/claude-code/mcp.json

# 3. Test sending
claude /send-email
```

### Step 4: WhatsApp Setup (Day 5-6)
```bash
# 1. Setup WhatsApp session
python utils/whatsapp_setup.py
# Scan QR code with phone

# 2. Test monitoring
claude /monitor-whatsapp
```

### Step 5: Scheduling (Day 7)
```bash
# 1. Start watchers with PM2
pm2 start ecosystem.config.js

# 2. Configure cron jobs
crontab -e
# Add scheduled tasks

# 3. Verify running
pm2 status
```

### Step 6: Testing (Day 8-9)
```bash
# End-to-end test
# 1. Send test email to yourself
# 2. Verify action item created
# 3. Process with /process-emails
# 4. Approve draft
# 5. Verify email sent
```

---

## 📖 Usage Examples

### Process All Pending Emails
```bash
claude /process-emails
```

### Monitor and Respond to Gmail
```bash
# Start monitoring
claude /monitor-gmail

# Process detected emails
claude /process-emails

# Review approvals
claude /approve-actions

# Send approved emails
# (Automatic when moved to Approved/)
```

### Post to LinkedIn
```bash
# Generate post from recent work
claude "Create a LinkedIn post about the TechStartup project completion and submit for approval"

# Review in Pending_Approval/
# Move to Approved/ to publish
```

### Run Autonomous Task Loop
```bash
# Process specific task until complete
python scripts/orchestrator.py --task EMAIL_client_inquiry.md

# Process all pending tasks
python scripts/orchestrator.py --all
```

---

## 🔧 Configuration Files

### Required Files

```
.
├── .env                          # Environment variables
├── .claude/
│   ├── config.json              # Claude Code config
│   ├── hooks/
│   │   └── stop.sh              # Ralph Wiggum hook
│   └── skills/                  # This directory
├── credentials.json             # Gmail OAuth credentials
├── token.json                   # Gmail access token
├── ecosystem.config.js          # PM2 configuration
├── mcp-servers/
│   └── email-server/            # Email MCP server
├── AI_Employee_Vault/    # Obsidian vault
│   ├── Company_Handbook.md      # Rules and guidelines
│   ├── Dashboard.md             # Status dashboard
│   ├── Needs_Action/            # Pending tasks
│   ├── Pending_Approval/        # Awaiting approval
│   ├── Approved/                # Approved actions
│   ├── Done/                    # Completed tasks
│   └── Logs/                    # Activity logs
└── scripts/
    ├── orchestrator.py          # Task orchestrator
    ├── daily_briefing.py        # Daily briefing
    └── weekly_audit.py          # Weekly audit
```

### .env Template

```bash
# Gmail Configuration
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
GMAIL_CHECK_INTERVAL=120
GMAIL_QUERY=is:unread is:important

# WhatsApp Configuration
WHATSAPP_SESSION_PATH=./whatsapp_session
WHATSAPP_CHECK_INTERVAL=30
WHATSAPP_HEADLESS=true

# LinkedIn Configuration
LINKEDIN_SESSION_PATH=./linkedin_session
LINKEDIN_HEADLESS=true

# Vault Configuration
VAULT_PATH=./AI_Employee_Vault

# Approval Configuration
APPROVAL_CHECK_INTERVAL=60
APPROVAL_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

# Notifications
NOTIFICATION_EMAIL=your@email.com

# Safety
DRY_RUN=false
MAX_ITERATIONS=10
```

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] Gmail watcher detects emails
- [ ] WhatsApp watcher detects messages
- [ ] Email MCP server sends emails
- [ ] Approval workflow moves files correctly
- [ ] LinkedIn poster creates posts
- [ ] Reasoning loop completes tasks

### Integration Tests
- [ ] Email → Action Item → Draft → Approval → Send
- [ ] WhatsApp → Action Item → Dashboard Update
- [ ] LinkedIn Post → Approval → Publish
- [ ] Reasoning Loop → Multi-step Task → Completion

### End-to-End Tests
- [ ] Send email to self → Auto-response sent
- [ ] WhatsApp message → Action created
- [ ] Project completion → LinkedIn post published
- [ ] Daily briefing generated automatically

---

## 🐛 Common Issues

### Gmail API Issues
**Problem**: "Authentication failed"
**Solution**: Delete token.json and re-authorize

**Problem**: "Rate limit exceeded"
**Solution**: Increase CHECK_INTERVAL to 300+ seconds

### WhatsApp Issues
**Problem**: "Session expired"
**Solution**: Delete whatsapp_session/ and re-login

**Problem**: "No messages detected"
**Solution**: Verify keywords in Company_Handbook.md

### MCP Server Issues
**Problem**: "MCP server not found"
**Solution**: Check mcp.json path and restart Claude Code

**Problem**: "Email not sent"
**Solution**: Check MCP server logs and Gmail API quota

### Scheduling Issues
**Problem**: "PM2 not found"
**Solution**: Install globally: npm install -g pm2

**Problem**: "Cron job not running"
**Solution**: Use absolute paths in crontab

---

## 📊 Performance Metrics

Track these metrics to optimize your AI Employee:

- **Email Processing Time**: Detection → Response sent
- **Approval Rate**: Approved vs Rejected actions
- **Task Completion Rate**: Completed vs Timeout
- **Watcher Uptime**: % time watchers are running
- **API Usage**: Calls per day, quota remaining
- **Response Quality**: Human feedback on drafts

---

## 🔒 Security Best Practices

1. **Credentials**
   - Never commit credentials.json or token.json
   - Use .env for configuration
   - Rotate tokens monthly

2. **Approval Workflow**
   - Always require approval for sensitive actions
   - Set reasonable expiration times
   - Review approval logs weekly

3. **Rate Limiting**
   - Respect API quotas
   - Implement backoff strategies
   - Monitor usage daily

4. **Data Privacy**
   - Keep vault local
   - Encrypt sensitive data
   - Regular backups

5. **Access Control**
   - Restrict file permissions
   - Use minimal privileges
   - Audit access logs

---

## 📈 Upgrade Path to Gold Tier

After completing Silver tier, upgrade to Gold by adding:

1. **Odoo Integration** - Accounting system with MCP
2. **Facebook/Instagram** - Social media integration
3. **Twitter/X** - Additional social platform
4. **Weekly CEO Briefing** - Business audit automation
5. **Error Recovery** - Graceful degradation
6. **Comprehensive Logging** - Full audit trail
7. **Multi-Step Autonomy** - Advanced reasoning loops

---

## 🎓 Learning Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [MCP Protocol Docs](https://modelcontextprotocol.io)
- [Playwright Documentation](https://playwright.dev)
- [PM2 Documentation](https://pm2.keymetrics.io)
- [Claude Code Hooks](https://github.com/anthropics/claude-code)
- [Agent Skills Guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

---

## 💡 Tips for Success

1. **Start Small** - Test each skill individually before combining
2. **Use Dry Run** - Set DRY_RUN=true while testing
3. **Monitor Logs** - Check logs regularly for issues
4. **Iterate Quickly** - Make small changes and test
5. **Document Changes** - Keep notes on customizations
6. **Backup Regularly** - Backup vault and credentials
7. **Ask for Help** - Join Wednesday research meetings

---

## 🤝 Support

- **Weekly Meetings**: Wednesdays 10 PM on Zoom
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Refer to individual SKILL.md files
- **Community**: Share learnings with other participants

---

**Created**: 2026-02-19
**Version**: 1.0
**Tier**: Silver
**Total Skills**: 8
**Estimated Completion**: 26-33 hours
