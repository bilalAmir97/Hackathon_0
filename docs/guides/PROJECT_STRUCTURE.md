# AI Employee - Incremental Tier Structure

## 📁 Project Structure

```
Hackathon_0/                              # Root directory
├── .claude/
│   ├── skills/                           # Silver Tier Agent Skills
│   │   ├── README.md                     # Skills guide
│   │   ├── monitor-gmail/
│   │   │   └── SKILL.md
│   │   ├── send-email/
│   │   │   └── SKILL.md
│   │   ├── process-emails/
│   │   │   └── SKILL.md
│   │   ├── approve-actions/
│   │   │   └── SKILL.md
│   │   ├── monitor-whatsapp/
│   │   │   └── SKILL.md
│   │   ├── post-linkedin/
│   │   │   └── SKILL.md
│   │   ├── schedule-tasks/
│   │   │   └── SKILL.md
│   │   └── reasoning-loop/
│   │       └── SKILL.md
│   └── hooks/                            # Claude Code hooks (to be created)
│       └── stop.sh                       # Ralph Wiggum hook
│
├── AI_Employee_Vault/                    # Obsidian Vault (Bronze tier base)
│   ├── Dashboard.md                      # Real-time dashboard
│   ├── Company_Handbook.md               # Rules and guidelines
│   ├── Inbox/                            # File drop zone
│   ├── Needs_Action/                     # Pending action items
│   ├── Done/                             # Completed tasks
│   ├── Plans/                            # Task plans
│   ├── Logs/                             # Activity logs
│   ├── Pending_Approval/                 # Awaiting approval
│   ├── Approved/                         # Approved actions
│   └── Rejected/                         # Rejected actions
│
├── watchers/                             # Monitoring scripts (Bronze + Silver)
│   ├── __init__.py
│   ├── base_watcher.py                   # Base class
│   ├── filesystem_watcher.py             # Bronze: File system
│   ├── gmail_watcher.py                  # Silver: Gmail (to implement)
│   └── whatsapp_watcher.py               # Silver: WhatsApp (to implement)
│
├── scripts/                              # Automation scripts
│   ├── orchestrator.py                   # Silver: Task orchestrator
│   ├── daily_briefing.py                 # Silver: Daily briefing (to create)
│   ├── weekly_audit.py                   # Gold: Weekly audit (to create)
│   └── setup_vault.py                    # Utility: Vault setup (to create)
│
├── tests/                                # Test suite
│   ├── README.md                         # Test documentation
│   ├── verify_setup.py                   # Environment verification
│   ├── test_all_skills.py                # Unit tests
│   ├── test_integration.py               # Integration tests
│   └── run_all_tests.py                  # Master test runner
│
├── mcp-servers/                          # MCP servers (Silver tier)
│   └── email-server/                     # Email MCP (to create)
│       ├── index.js                      # Node.js implementation
│       └── package.json
│
├── utils/                                # Utility modules (to create)
│   ├── gmail_auth.py                     # Gmail OAuth helper
│   ├── whatsapp_setup.py                 # WhatsApp session setup
│   ├── linkedin_setup.py                 # LinkedIn session setup
│   └── email_processor.py                # Email processing utilities
│
├── .env.example                          # Environment template
├── .env                                  # Environment config (create from example)
├── .gitignore                            # Git ignore rules
├── pyproject.toml                        # Python dependencies
├── ecosystem.config.js                   # PM2 configuration (to create)
├── credentials.json                      # Gmail OAuth (to obtain)
├── token.json                            # Gmail token (auto-generated)
│
├── README.md                             # Project overview (this file)
├── SILVER_TIER_COMPLETE.md               # Silver tier documentation
├── Bronze/                               # Original Bronze tier (archived)
│   └── (original files kept for reference)
│
└── Personal AI Employee Hackathon 0...md # Hackathon guide
```

## 🎯 Tier Progression

### ✅ Bronze Tier (Complete)
**Location**: Root directory base structure
- Obsidian vault with Dashboard and Company Handbook
- File system watcher
- Basic folder structure
- Claude Code integration

### 🔨 Silver Tier (In Progress)
**Location**: `.claude/skills/` + `scripts/orchestrator.py`
- Gmail monitoring
- Email MCP server
- WhatsApp monitoring
- LinkedIn posting
- Task scheduling
- Reasoning loops
- Approval workflow

### 🚧 Gold Tier (Future)
**Location**: Additional integrations
- Odoo accounting integration
- Facebook/Instagram integration
- Twitter/X integration
- Weekly CEO briefing
- Error recovery
- Comprehensive audit logging

### 💎 Platinum Tier (Future)
**Location**: Cloud deployment
- Cloud VM deployment (24/7)
- Work-zone specialization
- Vault synchronization
- Advanced delegation

## 🔄 Incremental Development Approach

### Why This Structure?

1. **Single Vault**: All tiers use the same `AI_Employee_Vault/`
2. **Additive Skills**: Each tier adds skills without removing previous ones
3. **Shared Watchers**: Bronze file watcher + Silver email/WhatsApp watchers
4. **Progressive Enhancement**: Build on top of existing functionality
5. **No Rebuilding**: Each tier extends, not replaces

### Development Flow

```
Bronze (Base) → Silver (Add Skills) → Gold (Add Integrations) → Platinum (Deploy)
     ↓               ↓                      ↓                        ↓
  Vault +        Watchers +            Accounting +              Cloud +
  Basic          Email/WhatsApp        Social Media             Always-On
  Watcher        MCP Servers           CEO Briefing             Sync
```

## 📝 Configuration

### Environment Variables (.env)

All tiers share the same `.env` file:

```bash
# Vault Configuration (Bronze)
VAULT_PATH=./AI_Employee_Vault

# Gmail Configuration (Silver)
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
GMAIL_CHECK_INTERVAL=120

# WhatsApp Configuration (Silver)
WHATSAPP_SESSION_PATH=./whatsapp_session
WHATSAPP_CHECK_INTERVAL=30

# LinkedIn Configuration (Silver)
LINKEDIN_SESSION_PATH=./linkedin_session

# Approval Configuration (Silver)
APPROVAL_CHECK_INTERVAL=60
APPROVAL_EXPIRATION_HOURS=24

# Odoo Configuration (Gold - future)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

## 🚀 Getting Started

### 1. Verify Structure
```bash
# Check current structure
ls -la

# Should see:
# - AI_Employee_Vault/
# - .claude/skills/
# - watchers/
# - scripts/
# - tests/
```

### 2. Run Tests
```bash
# Verify environment
python tests/verify_setup.py

# Run all tests
python tests/run_all_tests.py
```

### 3. Start Silver Tier Implementation
```bash
# Phase 1: Gmail setup
cat .claude/skills/monitor-gmail/SKILL.md

# Phase 2: Create MCP server
mkdir -p mcp-servers/email-server

# Phase 3: Implement watchers
# Follow skills documentation
```

## 📊 Current Status

### ✅ Completed
- Bronze tier vault structure
- Silver tier skills documentation (8 skills)
- Orchestrator script
- Comprehensive test suite (41 tests)
- Path migration to root directory

### 🔨 In Progress
- Environment setup (dependencies)
- Gmail API configuration
- MCP server implementation

### 📋 To Do
- Implement Gmail watcher
- Create email MCP server
- Set up WhatsApp automation
- Configure PM2 scheduling
- Implement reasoning loops
- Add LinkedIn integration

## 🔧 Migration Notes

### What Changed
- **Before**: `Bronze/AI_Employee_Vault/`
- **After**: `AI_Employee_Vault/`

### Updated Files
- All test scripts (tests/*.py)
- Orchestrator script (scripts/orchestrator.py)
- All skill documentation (.claude/skills/*/SKILL.md)
- Configuration templates (.env.example)

### No Changes Needed
- Vault contents (Dashboard.md, Company_Handbook.md)
- Folder structure (Inbox, Needs_Action, Done, etc.)
- Bronze tier functionality

## 💡 Benefits of This Structure

1. **Incremental**: Build Silver on top of Bronze
2. **Testable**: Tests work across all tiers
3. **Maintainable**: Single vault, single config
4. **Scalable**: Easy to add Gold and Platinum
5. **Clear**: Each tier's files are organized logically

## 📚 Documentation

- **Skills Guide**: `.claude/skills/README.md`
- **Test Guide**: `tests/README.md`
- **Silver Tier**: `SILVER_TIER_COMPLETE.md`
- **Hackathon Guide**: `Personal AI Employee Hackathon 0...md`

---

**Structure Version**: 2.0 (Incremental Tiers)
**Last Updated**: 2026-02-24
**Current Tier**: Bronze → Silver (In Progress)
