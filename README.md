# AI Employee - Personal FTE Hackathon

Build your own autonomous AI Employee using Claude Code and Obsidian. This project implements a local-first, agent-driven system that proactively manages personal and business affairs 24/7.

## 🎯 Incremental Tier Structure

This project uses an **incremental tier-based** approach where each tier builds on top of the previous one:

- **Bronze Tier** ✅ - Foundation (File monitoring, basic vault) - **COMPLETE**
- **Silver Tier** ✅ - Gmail Watcher + Approval Workflow - **COMPLETE**
- **Gold Tier** 📋 - Autonomous Employee (Accounting, social media, CEO briefing) - **FUTURE**
- **Platinum Tier** 💎 - Always-On Cloud (24/7 deployment, work-zone specialization) - **FUTURE**

**Current Status**: Bronze Complete → Silver Complete ✅

## ✅ What's Included

### Bronze Tier (Complete)
- ✅ Obsidian vault with Dashboard.md and Company_Handbook.md
- ✅ File system watcher for monitoring the Inbox folder
- ✅ Claude Code integration for reading and writing to the vault
- ✅ Basic folder structure: /Inbox, /Needs_Action, /Done
- ✅ All AI functionality implemented as Agent Skills

### Silver Tier (Complete)
- ✅ Gmail watcher with OAuth 2.0 authentication
- ✅ Priority email detection (configurable keywords)
- ✅ Idempotent state management (no duplicates across restarts)
- ✅ File-based approval workflow (Pending → Approved/Rejected → Done)
- ✅ Watchdog-based folder monitoring
- ✅ Plan.md generation before action execution
- ✅ JSON Lines logging with complete audit trail
- ✅ Network outage recovery with operation queuing
- ✅ Token expiration handling with alerts
- ✅ Vault structure validation and recovery
- ✅ Graceful shutdown handlers (SIGTERM/SIGINT)
- ✅ Comprehensive test suite (51 tests, 94% passing)
- ✅ Constitution-driven development (10 core principles)

## 📁 Project Structure

```
Hackathon_0/                              # Root directory
├── AI_Employee_Vault/                    # Obsidian vault (all tiers)
│   ├── Dashboard.md                      # Real-time status dashboard
│   ├── Company_Handbook.md               # Rules and guidelines
│   ├── Inbox/                            # Drop files here
│   ├── Needs_Action/                     # Action items created by watchers
│   ├── Done/                             # Completed tasks
│   ├── Plans/                            # Task plans
│   ├── Logs/                             # Activity logs
│   ├── Pending_Approval/                 # Items awaiting approval
│   ├── Approved/                         # Approved actions
│   └── Rejected/                         # Rejected actions
│
├── .claude/skills/                       # Silver tier agent skills (8 skills)
│   ├── README.md                         # Skills guide
│   ├── monitor-gmail/SKILL.md
│   ├── send-email/SKILL.md
│   ├── process-emails/SKILL.md
│   ├── approve-actions/SKILL.md
│   ├── monitor-whatsapp/SKILL.md
│   ├── post-linkedin/SKILL.md
│   ├── schedule-tasks/SKILL.md
│   └── reasoning-loop/SKILL.md
│
├── watchers/                             # Monitoring scripts (Bronze + Silver)
│   ├── base_watcher.py                   # Base class
│   └── filesystem_watcher.py             # Bronze: File system monitor
│
├── scripts/                              # Automation scripts
│   └── orchestrator.py                   # Silver: Task orchestrator
│
├── tests/                                # Comprehensive test suite
│   ├── README.md                         # Test documentation
│   ├── verify_setup.py                   # Environment verification
│   ├── test_all_skills.py                # Unit tests (25 tests)
│   ├── test_integration.py               # Integration tests (4 workflows)
│   └── run_all_tests.py                  # Master test runner
│
├── .env.example                          # Environment template
├── pyproject.toml                        # Python dependencies
├── PROJECT_STRUCTURE.md                  # Complete structure guide
├── SILVER_TIER_COMPLETE.md               # Silver tier documentation
└── README.md                             # This file
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for complete details.

## 🚀 Quick Start

### 1. Verify Environment

```bash
python tests/verify_setup.py
```

This checks:
- Python 3.10+, Node.js 18+, Claude Code
- Required packages
- Vault structure
- Skills directory

### 2. Install Dependencies

```bash
# Python packages (Silver tier)
pip install google-auth google-auth-oauthlib google-api-python-client
pip install playwright watchdog

# Playwright browsers
playwright install chromium

# PM2 (process manager)
npm install -g pm2
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 4. Run Tests

```bash
# Full test suite
python tests/run_all_tests.py

# Quick test (skip integration)
python tests/run_all_tests.py --quick
```

## Prerequisites

### Required
- **Python 3.10+** - Core language
- **Node.js 18+** - For MCP servers
- **Claude Code** - AI reasoning engine
- **Git** - Version control

### Optional (for Silver tier)
- **PM2** - Process management
- **Playwright** - Browser automation
- **Gmail API** - Email integration
- **Obsidian** - Vault visualization

## 💻 Usage

### Bronze Tier - File System Watcher

The watcher monitors the `Inbox` folder and creates action items when new files are dropped:

```bash
# Start the file system watcher
python watchers/filesystem_watcher.py
```

### Using Claude Code

1. **Open the vault in Claude Code:**
   ```bash
   cd AI_Employee_Vault
   claude
   ```

2. **Process action items:**
   ```
   Read all files in the Needs_Action folder and process them according to Company_Handbook.md
   ```

3. **Update the dashboard:**
   ```
   Update Dashboard.md with current status and recent activity
   ```

### Silver Tier - Gmail Watcher + Approval Workflow

The Silver tier implements a production-grade email monitoring system with human-in-the-loop approval:

```bash
# Start Gmail watcher (monitors inbox for priority emails)
python -m watchers.gmail_watcher

# In another terminal, start approval executor (monitors approval workflow)
python -m scripts.approval_executor

# Or use the quickstart script to start both
./scripts/start_silver_tier.sh
```

**Workflow:**
1. Gmail watcher polls inbox every 2 minutes (configurable)
2. Priority emails (matching keywords) create action files in `Needs_Action/`
3. Human reviews and moves to `Pending_Approval/` with approval request
4. Human approves (move to `Approved/`) or rejects (move to `Rejected/`)
5. Approved actions execute via MCP, create Plan.md, log to JSON Lines
6. Completed actions move to `Done/` with full audit trail

**Configuration:**
```bash
# Required: Gmail OAuth setup
python test_gmail_oauth.py  # First-time authentication

# Edit .env for customization
GMAIL_CHECK_INTERVAL=120
PRIORITY_KEYWORDS=urgent,important,asap,invoice,payment,client,deadline
DRY_RUN=false
```

### Autonomous Task Completion

Use the orchestrator for multi-step tasks:

```bash
# Process specific task
python scripts/orchestrator.py --task EMAIL_client.md

# Process all pending tasks
python scripts/orchestrator.py --all
```

## 📋 Workflow Example

### Bronze Tier Workflow

1. **Drop a file** into `AI_Employee_Vault/Inbox/`
2. **Watcher detects** the file and creates an action item in `Needs_Action/`
3. **Claude Code processes** the action item (manually or via skill)
4. **Task is completed** and moved to `Done/`
5. **Dashboard is updated** with the activity

### Silver Tier Workflow (Once Implemented)

1. **Email arrives** → Gmail watcher detects → Creates action item
2. **Claude processes** → Drafts response → Creates approval request
3. **Human approves** → Moves to Approved folder
4. **MCP server sends** → Email sent → Task moved to Done
5. **Dashboard updated** → Activity logged

## 🧪 Testing the System

### Bronze Tier Test

1. **Start the watcher:**
   ```bash
   python watchers/filesystem_watcher.py
   ```

2. **In another terminal, drop a test file:**
   ```bash
   echo "Test document" > AI_Employee_Vault/Inbox/test.txt
   ```

3. **Check Needs_Action folder:**
   ```bash
   ls AI_Employee_Vault/Needs_Action/
   ```

4. **Use Claude Code to process:**
   ```bash
   cd AI_Employee_Vault
   claude
   # Then: "Process the file in Needs_Action and move it to Done"
   ```

### Comprehensive Testing

```bash
# Environment verification
python tests/verify_setup.py

# Unit tests (individual skills)
python tests/test_all_skills.py

# Integration tests (complete workflows)
python tests/test_integration.py

# Full test suite
python tests/run_all_tests.py
```

See `tests/README.md` for complete testing documentation.

## ✨ Key Features

### Bronze Tier (Complete)
- **File System Watcher** - Monitors Inbox folder continuously
- **Obsidian Integration** - Local-first, human-readable markdown
- **Claude Code Integration** - Read/write vault files, follow handbook rules
- **Structured Action Items** - Includes metadata, suggested actions
- **Dashboard Updates** - Real-time status tracking

### Silver Tier (Ready to Build)
- **Gmail Monitoring** - Detect important emails automatically
- **Email MCP Server** - Send emails with human approval
- **WhatsApp Monitoring** - Monitor messages for priority keywords
- **LinkedIn Posting** - Auto-post business updates
- **Approval Workflow** - Human-in-the-loop for sensitive actions
- **Task Scheduling** - Run watchers 24/7 with PM2
- **Reasoning Loops** - Autonomous multi-step task completion
- **Comprehensive Testing** - 41 tests covering all functionality

### Incremental Development
- **Single Vault** - All tiers use the same AI_Employee_Vault/
- **Additive Skills** - Each tier adds without removing previous
- **Shared Watchers** - Bronze + Silver watchers work together
- **Progressive Enhancement** - Build on existing functionality
- **No Rebuilding** - Each tier extends, not replaces

## ⚙️ Configuration

Edit `.env` to customize (copy from `.env.example`):

```bash
# Bronze Tier
VAULT_PATH=./AI_Employee_Vault
CHECK_INTERVAL=60
LOG_LEVEL=INFO

# Silver Tier (when implementing)
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_CHECK_INTERVAL=120
WHATSAPP_SESSION_PATH=./whatsapp_session
LINKEDIN_SESSION_PATH=./linkedin_session
APPROVAL_EXPIRATION_HOURS=24

# Safety
DRY_RUN=false
MAX_ITERATIONS=10
```

See `.env.example` for complete configuration options.

## 🐛 Troubleshooting

### Environment Issues

**"Python packages missing"**
```bash
pip install google-auth google-auth-oauthlib google-api-python-client playwright watchdog
```

**"PM2 not found"**
```bash
npm install -g pm2
```

**"Vault structure incorrect"**
```bash
cd AI_Employee_Vault
mkdir -p Inbox Needs_Action Done Plans Logs Pending_Approval Approved Rejected
```

### Watcher Issues

**Watcher not detecting files:**
- Ensure the Inbox folder exists
- Check file permissions
- Try restarting the watcher

**Claude Code can't read vault:**
- Verify you're in the vault directory
- Check file paths are correct
- Ensure files aren't locked by another process

### Test Failures

**Tests failing:**
```bash
# Run with verbose mode
python tests/run_all_tests.py --verbose

# Check specific test
python tests/test_all_skills.py --skill gmail

# Verify environment first
python tests/verify_setup.py
```

See `tests/README.md` for detailed troubleshooting.

## 🚀 Next Steps - Building Silver Tier

### Phase 1: Gmail Setup (Week 1)

1. **Read the skill documentation:**
   ```bash
   cat .claude/skills/monitor-gmail/SKILL.md
   ```

2. **Set up Gmail API:**
   - Create Google Cloud project
   - Enable Gmail API
   - Download credentials.json
   - Place in project root

3. **Implement Gmail watcher:**
   - Follow skill documentation
   - Test with: `python tests/test_all_skills.py --skill gmail`

4. **Create email MCP server:**
   - Read: `.claude/skills/send-email/SKILL.md`
   - Create: `mcp-servers/email-server/`
   - Configure Claude Code MCP settings

### Phase 2: Expand Monitoring (Week 2)

5. **Add WhatsApp monitoring:**
   - Read: `.claude/skills/monitor-whatsapp/SKILL.md`
   - Set up Playwright session
   - Test keyword detection

### Phase 3: Automation (Week 3)

6. **Configure scheduling:**
   - Read: `.claude/skills/schedule-tasks/SKILL.md`
   - Set up PM2 for watchers
   - Configure cron jobs

7. **Implement reasoning loops:**
   - Read: `.claude/skills/reasoning-loop/SKILL.md`
   - Create Stop hook
   - Test with orchestrator

### Phase 4: Business Value (Week 4)

8. **Add LinkedIn integration:**
   - Read: `.claude/skills/post-linkedin/SKILL.md`
   - Set up LinkedIn session
   - Test posting workflow

### Complete Guide

See `.claude/skills/README.md` for the complete Silver tier implementation guide with:
- Detailed setup instructions for each skill
- Code examples and templates
- Troubleshooting guides
- Best practices

**Estimated Time**: 26-33 hours total for Silver tier

## 📚 Documentation

### Core Documentation
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Complete project structure and tier progression
- **[SILVER_TIER_COMPLETE.md](SILVER_TIER_COMPLETE.md)** - Silver tier comprehensive guide
- **[Hackathon Guide](Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)** - Full hackathon documentation

### Skills Documentation
- **[Skills Guide](.claude/skills/README.md)** - All 8 Silver tier skills overview
- **Individual Skills** - `.claude/skills/[skill-name]/SKILL.md` for each skill

### Testing Documentation
- **[Test Guide](tests/README.md)** - Complete testing documentation
- **Environment Verification** - `tests/verify_setup.py`
- **Unit Tests** - `tests/test_all_skills.py`
- **Integration Tests** - `tests/test_integration.py`

## 🔒 Security Notes

- **Local-First**: All data stays on your machine (until Platinum tier)
- **No Cloud Dependencies**: Bronze and Silver tiers are fully local
- **Credentials**: Never stored in vault, use .env for configuration
- **Approval Workflow**: Human-in-the-loop for sensitive actions
- **Audit Trail**: All actions logged in Logs/ folder
- **Encryption**: Consider encrypting vault for sensitive data

## 📄 License

This is a hackathon project for educational purposes.

## 📖 Resources

### Learning Materials
- [Claude Code Documentation](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [Agent Skills Guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Gmail API](https://developers.google.com/gmail/api)
- [Playwright](https://playwright.dev)
- [Obsidian Documentation](https://help.obsidian.md/)

### Weekly Meetings
- **Wednesdays 10 PM** on Zoom
- Share progress and learn from others
- Get help with implementation challenges

---

## 🎉 Getting Started Checklist

- [ ] Run `python tests/verify_setup.py`
- [ ] Install missing dependencies
- [ ] Copy `.env.example` to `.env`
- [ ] Run `python tests/run_all_tests.py`
- [ ] Read `.claude/skills/README.md`
- [ ] Start Phase 1: Gmail setup
- [ ] Test each skill as you build
- [ ] Join Wednesday research meetings

**Ready to build your AI Employee!** 🚀

---

**Version**: 2.0 (Incremental Tiers)
**Last Updated**: 2026-02-24
**Current Tier**: Bronze ✅ → Silver 🔨 (In Progress)
**Built for Personal AI Employee Hackathon 0**
