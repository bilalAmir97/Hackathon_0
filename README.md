# AI Employee - Personal FTE Hackathon

Build your own autonomous AI Employee using Claude Code and Obsidian. This project implements a local-first, agent-driven system that proactively manages personal and business affairs 24/7.

## 🎯 Tier Structure

This project uses an **incremental tier-based** approach where each tier builds on top of the previous one:

- **Bronze Tier** ✅ - Foundation (File monitoring, basic vault) - **COMPLETE**
- **Silver Tier** ✅ - Gmail Watcher + Approval Workflow - **COMPLETE**
- **Gold Tier** ✅ - Autonomous Employee (Accounting, social media, business intelligence) - **COMPLETE**
- **Platinum Tier** 💎 - Always-On Cloud (24/7 deployment, work-zone specialization) - **FUTURE**

**Current Status**: Gold Tier Complete ✅

---

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
- ✅ Comprehensive test suite
- ✅ Constitution-driven development (10 core principles)

### Gold Tier (Complete)
- ✅ **Odoo ERP Integration**: Invoice creation, payment recording, financial operations
- ✅ **Facebook & Instagram Integration**: Post text, images, carousels with approval workflow
- ✅ **Twitter Integration**: Tweet posting, threads, mentions monitoring, engagement metrics
- ✅ **Business Intelligence System**: Data collectors for all sources
- ✅ **Weekly Business Audit**: Automated comprehensive reports with recommendations
- ✅ **System Health Monitoring**: Automated alerts for stale approvals, errors, disk space
- ✅ **Error Recovery System**: Retry logic, circuit breakers, graceful degradation
- ✅ **Comprehensive Audit Logging**: All actions logged with sensitive data masking
- ✅ **Automated Scheduling**: Cron jobs for weekly audits, health checks, log rotation
- ✅ **Cross-Domain Integration**: End-to-end workflows tested
- ✅ **Complete Documentation**: Architecture, security model, MCP servers, watcher system

---

## 📁 Project Structure

```
Hackathon_0/
├── AI_Employee_Vault/              # Obsidian vault
│   ├── Dashboard.md                # Real-time status dashboard
│   ├── Company_Handbook.md         # Rules and guidelines
│   ├── Inbox/                      # Drop files here
│   ├── Needs_Action/               # Action items + health alerts
│   ├── Done/                       # Completed tasks
│   ├── Plans/                      # Task plans
│   ├── Logs/                       # Audit logs (JSONL)
│   ├── Briefings/                  # Weekly audit reports
│   ├── Pending_Approval/           # Awaiting approval
│   ├── Approved/                   # Approved actions
│   ├── Rejected/                   # Rejected actions
│   └── .quarantine/                # Corrupted files
│
├── mcp_servers/                    # MCP protocol servers
│   ├── email_client.py             # Gmail integration
│   ├── odoo_client.py              # Odoo ERP client
│   ├── odoo_mcp_server.py          # Odoo MCP server
│   ├── facebook_instagram_client.py # Facebook/Instagram client
│   ├── facebook_instagram_mcp_server.py # Social media MCP
│   ├── twitter_client.py           # Twitter API client
│   ├── twitter_mcp_server.py       # Twitter MCP server
│   ├── twitter_rate_limiter.py     # Rate limiting
│   └── image_validator.py          # Image validation
│
├── watchers/                       # Event-driven monitoring
│   ├── base_watcher.py             # Base class
│   ├── filesystem_watcher.py       # File system monitor
│   ├── gmail_watcher.py            # Gmail monitor
│   └── vault_watcher.py            # Vault folder monitor
│
├── scripts/                        # Automation scripts
│   ├── approval_executor.py        # Executes approved actions
│   ├── audit_logger.py             # Comprehensive logging
│   ├── generate_weekly_audit.py    # Business intelligence
│   ├── health_check.py             # System health monitoring
│   ├── setup_cron.sh               # Automated scheduling
│   ├── error_recovery/             # Error recovery system
│   │   ├── decorators.py           # Retry, circuit breaker
│   │   └── service_health.py       # Service health tracking
│   └── data_collectors/            # Business intelligence
│       ├── odoo_collector.py       # Financial data
│       ├── social_media_collector.py # Social metrics
│       ├── email_collector.py      # Email activity
│       ├── audit_log_collector.py  # System activity
│       └── aggregate_data.py       # Unified aggregation
│
├── tests/                          # Comprehensive testing
│   ├── integration/                # Cross-domain workflows
│   │   ├── test_email_to_invoice_workflow.py
│   │   ├── test_project_to_social_workflow.py
│   │   ├── test_weekly_audit_workflow.py
│   │   └── run_all_tests.py
│   └── verify_setup.py             # Environment verification
│
├── docs/                           # Complete documentation
│   ├── architecture.md             # System architecture
│   ├── watcher-system.md           # Watcher documentation
│   ├── mcp-servers.md              # MCP server guide
│   └── security-model.md           # Security documentation
│
├── specs/                          # Feature specifications
│   ├── 001-gmail-approval-workflow/
│   ├── 005-error-recovery/
│   ├── 006-odoo-mcp-server/
│   ├── 007-facebook-instagram-mcp/
│   └── 008-twitter-mcp/
│
├── .env.example                    # Environment template
├── pyproject.toml                  # Python dependencies
└── README.md                       # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Python packages
pip install -r requirements.txt
# Or with uv:
uv pip install -e .

# PM2 (process manager)
npm install -g pm2
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

Required credentials:
- Gmail API (credentials.json, token.json)
- Odoo ERP (URL, database, username, password)
- Facebook/Instagram (Page Access Token, Account IDs)
- Twitter (API keys and access tokens)

### 3. Verify Setup

```bash
# Verify environment
python tests/verify_setup.py

# Verify specific integrations
python scripts/verify_gmail_setup.py
python scripts/verify_odoo_setup.py
python scripts/verify_twitter_setup.py
```

### 4. Start Services

```bash
# Start all watchers with PM2
pm2 start ecosystem.config.js

# Or start individually
python watchers/gmail_watcher.py &
python scripts/approval_executor.py &

# Setup automated tasks
bash scripts/setup_cron.sh
```

### 5. Run Integration Tests

```bash
# Test all workflows
python tests/integration/run_all_tests.py
```

---

## 💻 Usage

### Approval Workflow

All write operations require human approval:

1. **AI proposes action** → Creates file in `Pending_Approval/`
2. **Human reviews** → Moves to `Approved/` or `Rejected/`
3. **System executes** → Approved actions executed via MCP
4. **Audit logged** → Complete trail in `Logs/`
5. **Completed** → Moved to `Done/`

### Business Intelligence

Generate weekly business audit:

```bash
# Manual generation
python scripts/generate_weekly_audit.py --days 7

# Automated (via cron, Sunday 8 PM)
# Report saved to AI_Employee_Vault/Briefings/
```

### System Health

Monitor system health:

```bash
# Manual health check
python scripts/health_check.py

# Automated (via cron, every 5 minutes)
# Alerts created in AI_Employee_Vault/Needs_Action/
```

### Social Media Posting

Post to social media (requires approval):

```python
# Via MCP server
# 1. Create approval request
# 2. Human approves
# 3. Post published to platform
# 4. Engagement metrics tracked
```

### Financial Operations

Manage invoices and payments (requires approval):

```python
# Via Odoo MCP server
# 1. Create invoice approval request
# 2. Human approves
# 3. Invoice finalized in Odoo
# 4. Payment recorded
# 5. Audit logged
```

---

## ✨ Key Features

### Approval Workflow
- **Human-in-the-Loop**: All write operations require approval
- **File-Based State**: Visible, auditable state transitions
- **Atomic Operations**: No partial states
- **Quarantine**: Corrupted files isolated automatically

### Business Intelligence
- **Data Aggregation**: Unified collection from all sources
- **Weekly Audits**: Comprehensive reports with recommendations
- **Health Monitoring**: Proactive alerts for issues
- **Caching**: 60-minute TTL to reduce API calls

### Error Recovery
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascading failures
- **Graceful Degradation**: Continue operating with reduced functionality
- **Service Health**: Track and recover from sustained failures

### Audit Logging
- **Comprehensive**: Every action logged with full context
- **Structured**: JSONL format for easy parsing
- **Secure**: Sensitive data masked automatically
- **Retention**: 90-day automatic rotation

### Rate Limiting
- **Proactive**: Throttle at 80% capacity
- **Per-Endpoint**: Track limits independently
- **Header Parsing**: Update from API responses
- **Cooldown**: Automatic backoff on violations

### Security
- **Credential Management**: Environment variables only
- **Input Validation**: All inputs validated
- **Approval Required**: Human oversight for writes
- **Audit Trail**: Complete activity log
- **Quarantine**: Isolate suspicious files

---

## 📊 Integrations

### Email (Gmail)
- Monitor inbox for priority emails
- Send emails with approval
- Search and filter messages
- OAuth 2.0 authentication

### Accounting (Odoo ERP)
- Create and finalize invoices
- Record payments
- List invoices with filters
- Customer management

### Social Media
- **Facebook**: Post text, images with approval
- **Instagram**: Post images, carousels with approval
- **Twitter**: Post tweets, threads, monitor mentions, track metrics

### Business Intelligence
- Collect data from all sources
- Generate weekly audit reports
- Track system health
- Provide actionable recommendations

---

## 🧪 Testing

### Integration Tests

Test complete workflows:

```bash
# All workflows
python tests/integration/run_all_tests.py

# Specific workflow
python tests/integration/test_email_to_invoice_workflow.py
python tests/integration/test_project_to_social_workflow.py
python tests/integration/test_weekly_audit_workflow.py
```

### Manual Testing

```bash
# Test data collection
python scripts/data_collectors/aggregate_data.py --summary

# Test weekly audit
python scripts/generate_weekly_audit.py

# Test health check
python scripts/health_check.py
```

---

## ⚙️ Configuration

### Environment Variables

See `.env.example` for complete configuration. Key variables:

```bash
# Vault
VAULT_PATH=./AI_Employee_Vault

# Gmail
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_CHECK_INTERVAL=120

# Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Facebook/Instagram
FACEBOOK_PAGE_ID=123456789
FACEBOOK_PAGE_ACCESS_TOKEN=EAAxxxxx
INSTAGRAM_ACCOUNT_ID=987654321

# Twitter
TWITTER_API_KEY=xxxxx
TWITTER_API_SECRET=xxxxx
TWITTER_ACCESS_TOKEN=xxxxx
TWITTER_ACCESS_TOKEN_SECRET=xxxxx

# System
DRY_RUN=false
LOG_LEVEL=INFO
```

### Cron Jobs

Automated tasks (configured via `scripts/setup_cron.sh`):

- **Weekly Audit**: Sunday 8 PM
- **Health Check**: Every 5 minutes
- **Log Rotation**: Sunday 11 PM (90-day retention)
- **Cache Cleanup**: Daily 2 AM

---

## 📚 Documentation

### Architecture
- **[Architecture Overview](docs/architecture.md)** - Complete system architecture
- **[Watcher System](docs/watcher-system.md)** - Event-driven monitoring
- **[MCP Servers](docs/mcp-servers.md)** - Tool interfaces and protocols
- **[Security Model](docs/security-model.md)** - Security controls and compliance

### Specifications
- **[Gmail Approval Workflow](specs/001-gmail-approval-workflow/)** - Email integration
- **[Error Recovery](specs/005-error-recovery/)** - Resilience patterns
- **[Odoo MCP Server](specs/006-odoo-mcp-server/)** - Financial operations
- **[Facebook/Instagram MCP](specs/007-facebook-instagram-mcp/)** - Social media
- **[Twitter MCP](specs/008-twitter-mcp/)** - Twitter integration

---

## 🔒 Security

### Key Security Features

1. **Approval Workflow**: Human-in-the-loop for all writes
2. **Audit Logging**: Complete activity trail
3. **Credential Management**: Environment variables, never committed
4. **Input Validation**: All inputs validated before processing
5. **Error Quarantine**: Corrupted files isolated
6. **Rate Limiting**: Prevents abuse and quota exhaustion

See [docs/security-model.md](docs/security-model.md) for complete security documentation.

---

## 🐛 Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check PM2 status
pm2 status

# View logs
pm2 logs

# Restart services
pm2 restart all
```

**Approval workflow not working:**
```bash
# Check approval executor
pm2 logs approval_executor

# Verify vault structure
ls -la AI_Employee_Vault/
```

**Integration tests failing:**
```bash
# Verify credentials
python scripts/verify_gmail_setup.py
python scripts/verify_odoo_setup.py

# Check service availability
curl http://localhost:8069  # Odoo
```

**Health alerts appearing:**
```bash
# Check alerts
ls AI_Employee_Vault/Needs_Action/ALERT_*.md

# Review audit logs
tail -100 AI_Employee_Vault/Logs/audit_*.jsonl

# Run health check
python scripts/health_check.py
```

---

## 📈 Performance

### Current Capacity

- **Email Processing**: ~100 emails/hour
- **Social Media Posts**: Limited by API rate limits
- **Odoo Operations**: ~50 operations/hour
- **Audit Logging**: ~1000 actions/hour
- **Data Collection**: ~10 sources/minute

### Optimization

- **Caching**: 60-minute TTL for data collection
- **Rate Limiting**: Proactive throttling at 80% capacity
- **Batch Operations**: Group similar actions
- **Async Processing**: Non-blocking I/O where possible

---

## 🚀 Future Enhancements (Platinum Tier)

- **Cloud Deployment**: 24/7 availability
- **Web Dashboard**: Real-time monitoring and control
- **Mobile App**: Approval workflow on mobile
- **Advanced Analytics**: Machine learning for insights
- **Multi-User Support**: Role-based access control
- **Webhook Support**: Real-time event notifications
- **Database Backend**: Replace file-based state
- **Horizontal Scaling**: Multiple worker processes

---

## 📄 License

This is a hackathon project for educational purposes.

---

## 📖 Resources

### Documentation
- [Claude Code Documentation](https://agentfactory.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Gmail API](https://developers.google.com/gmail/api)
- [Odoo API](https://www.odoo.com/documentation/17.0/developer/reference/external_api.html)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [Twitter API v2](https://developer.twitter.com/en/docs/twitter-api)

### Community
- **Weekly Meetings**: Wednesdays 10 PM on Zoom
- Share progress and learn from others
- Get help with implementation challenges

---

## 🎉 Getting Started Checklist

- [ ] Install dependencies (`pip install -e .`)
- [ ] Copy `.env.example` to `.env`
- [ ] Configure credentials (Gmail, Odoo, social media)
- [ ] Run verification (`python tests/verify_setup.py`)
- [ ] Start services (`pm2 start ecosystem.config.js`)
- [ ] Setup cron jobs (`bash scripts/setup_cron.sh`)
- [ ] Run integration tests (`python tests/integration/run_all_tests.py`)
- [ ] Review documentation (`docs/`)

**Your AI Employee is ready!** 🚀

---

**Version**: 3.0 (Gold Tier Complete)
**Last Updated**: March 2026
**Current Tier**: Gold ✅
**Built for Personal AI Employee Hackathon 0**
