# AI Employee System - Architecture Documentation

**Version**: 1.0 (Gold Tier)
**Last Updated**: March 2026
**Status**: Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Integration Points](#integration-points)
6. [Deployment Architecture](#deployment-architecture)
7. [Scalability & Performance](#scalability--performance)
8. [Security Architecture](#security-architecture)

---

## System Overview

The AI Employee system is a comprehensive business automation platform that integrates multiple services through a unified approval workflow. It provides:

- **Email Management**: Gmail integration for automated email handling
- **Financial Management**: Odoo ERP integration for invoicing and payments
- **Social Media Management**: Facebook, Instagram, and Twitter integration
- **Business Intelligence**: Automated data collection and weekly audit reports
- **Approval Workflow**: Human-in-the-loop approval for all write operations
- **Audit Logging**: Comprehensive activity tracking and compliance

### Key Characteristics

- **Event-Driven**: File-based state transitions trigger automated actions
- **Human-in-the-Loop**: All write operations require explicit approval
- **Audit-First**: Every action is logged for compliance and debugging
- **Modular**: Each integration is independent and can be deployed separately
- **Resilient**: Error recovery, retry logic, and circuit breakers throughout

---

## Architecture Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility:
- **Watchers**: Monitor file system events
- **MCP Servers**: Provide tool interfaces for external services
- **Approval Executor**: Execute approved actions
- **Audit Logger**: Record all system activity

### 2. File-Based State Management

State transitions are represented as file movements:
```
Pending_Approval/ → Approved/ → Done/
                 ↘ Rejected/ → Done/
```

This provides:
- **Visibility**: State is always visible in the file system
- **Auditability**: File timestamps provide audit trail
- **Simplicity**: No database required for state management
- **Resilience**: State persists across restarts

### 3. Approval-First Design

All write operations follow the approval workflow:
1. AI proposes action → Creates approval request
2. Human reviews → Moves file to Approved/ or Rejected/
3. System executes → Moves file to Done/
4. Audit log captures → Records all steps

### 4. Defense in Depth

Multiple layers of security:
- **Input Validation**: All inputs validated before processing
- **Approval Workflow**: Human approval required for writes
- **Audit Logging**: All actions logged with full context
- **Error Recovery**: Graceful degradation on failures
- **Rate Limiting**: Prevents API quota exhaustion

---

## System Components

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Employee System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Watchers   │  │ MCP Servers  │  │   Approval   │      │
│  │              │  │              │  │   Executor   │      │
│  │ - Gmail      │  │ - Email      │  │              │      │
│  │ - Vault      │  │ - Odoo       │  │ - Validates  │      │
│  │              │  │ - Facebook   │  │ - Executes   │      │
│  │              │  │ - Instagram  │  │ - Logs       │      │
│  │              │  │ - Twitter    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │  Audit Logger   │                        │
│                   │                 │                        │
│                   │ - JSONL format  │                        │
│                   │ - Encryption    │                        │
│                   │ - Rotation      │                        │
│                   └─────────────────┘                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1. Watchers

**Purpose**: Monitor file system events and trigger actions

**Components**:
- `gmail_watcher.py`: Monitors Gmail for new emails
- `vault_watcher.py`: Monitors vault folders for state transitions

**Technology**: Python `watchdog` library for file system events

**Key Features**:
- Real-time file system monitoring
- Atomic file operations (move, not copy)
- State persistence across restarts
- Error recovery and retry logic

### 2. MCP Servers

**Purpose**: Provide tool interfaces for external services

**Servers**:
- **Email MCP**: Gmail integration (send, read, search)
- **Odoo MCP**: Financial operations (invoices, payments)
- **Facebook/Instagram MCP**: Social media posting and metrics
- **Twitter MCP**: Tweet posting, threads, mentions, metrics

**Protocol**: Model Context Protocol (MCP) - JSON-RPC 2.0

**Key Features**:
- Standardized tool interface
- Input validation
- Rate limiting
- Error handling
- Approval workflow integration

### 3. Approval Executor

**Purpose**: Execute approved actions and manage workflow

**Responsibilities**:
- Monitor Approved/ folder for new approvals
- Validate approval files against schema
- Execute approved actions via MCP servers
- Move completed actions to Done/
- Create alerts for errors

**Key Features**:
- Schema validation
- Action routing (email, Odoo, social media)
- Error handling and quarantine
- Audit logging integration

### 4. Audit Logger

**Purpose**: Record all system activity for compliance and debugging

**Format**: JSONL (JSON Lines) for efficient append-only logging

**Features**:
- Structured logging with full context
- Sensitive data masking
- 90-day retention with automatic rotation
- Encryption at rest (planned)
- Searchable by action type, actor, timestamp

### 5. Data Collectors

**Purpose**: Aggregate data from all sources for business intelligence

**Collectors**:
- **Odoo Collector**: Financial data (revenue, expenses, invoices)
- **Social Media Collector**: Engagement metrics from all platforms
- **Email Collector**: Gmail activity and approval metrics
- **Audit Log Collector**: System activity and health metrics

**Features**:
- Unified data aggregation
- 60-minute cache TTL
- Error handling per source
- JSON output format

### 6. Weekly Audit Generator

**Purpose**: Generate comprehensive business intelligence reports

**Features**:
- Executive summary with key metrics
- Financial performance analysis
- Social media performance tracking
- System health assessment
- Actionable recommendations
- Markdown format in Briefings/ folder

---

## Data Flow

### 1. Email to Invoice Workflow

```
┌─────────────┐
│ Gmail       │
│ New Email   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Gmail Watcher   │
│ Detects email   │
└──────┬──────────┘
       │
       ▼
┌─────────────────────────┐
│ Email MCP Server        │
│ Parses invoice request  │
└──────┬──────────────────┘
       │
       ▼
┌────────────────────────┐
│ Odoo MCP Server         │
│ Creates approval request│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Pending_Approval/       │
│ ODOO_INVOICE_*.md       │
└──────┬──────────────────┘
       │
       │ (Human moves file)
       ▼
┌─────────────────────────┐
│ Approved/               │
│ ODOO_INVOICE_*.md       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Approval Executor       │
│ Executes invoice create │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Odoo ERP                │
│ Invoice finalized       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Audit Logger            │
│ Records all steps       │
└─────────────────────────┘
```

### 2. Social Media Posting Workflow

```
┌─────────────────────────┐
│ AI proposes social post │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Social MCP Server       │
│ Creates approval request│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Pending_Approval/       │
│ SOCIAL_*_POST_*.md      │
└──────┬──────────────────┘
       │
       │ (Human approves)
       ▼
┌─────────────────────────┐
│ Approval Executor       │
│ Routes to platform      │
└──────┬──────────────────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Facebook │  │Instagram │  │ Twitter  │
│ Post     │  │ Post     │  │ Tweet    │
└──────────┘  └──────────┘  └──────────┘
```

### 3. Weekly Audit Workflow

```
┌─────────────────────────┐
│ Cron triggers weekly    │
│ (Sunday 8 PM)           │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Data Aggregator         │
│ Collects from all       │
│ sources                 │
└──────┬──────────────────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Odoo     │  │ Social   │  │ Email    │  │ Audit    │
│ Data     │  │ Media    │  │ Data     │  │ Logs     │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                      │
                      ▼
┌─────────────────────────────────────────┐
│ Weekly Audit Generator                  │
│ - Analyzes data                         │
│ - Generates insights                    │
│ - Creates recommendations               │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Briefings/              │
│ WEEKLY_AUDIT_*.md       │
└─────────────────────────┘
```

---

## Integration Points

### External Services

| Service | Purpose | Authentication | Rate Limits |
|---------|---------|----------------|-------------|
| Gmail API | Email management | OAuth 2.0 | 250 quota units/user/second |
| Odoo ERP | Financial operations | XML-RPC | No official limit |
| Facebook Graph API | Social media posting | Page Access Token | 200 calls/hour |
| Instagram Graph API | Social media posting | Page Access Token | 200 calls/hour |
| Twitter API v2 | Tweet posting | OAuth 1.0a | 50 tweets/24h (free tier) |

### Internal Integrations

- **Vault Structure**: Obsidian-compatible markdown files
- **Audit Logs**: JSONL format for log aggregation tools
- **Data Cache**: JSON files with TTL metadata
- **Process Management**: PM2 for service orchestration

---

## Deployment Architecture

### Process Management

```
PM2 Process Manager
├── gmail_watcher (always running)
├── vault_watcher (always running)
├── approval_executor (always running)
└── health_check (cron: */5 * * * *)
```

### Cron Jobs

```
# Weekly Business Audit
0 20 * * 0  python scripts/generate_weekly_audit.py

# Health Check
*/5 * * * * python scripts/health_check.py

# Log Rotation
0 23 * * 0  find AI_Employee_Vault/Logs -name "*.jsonl" -mtime +90 -delete

# Cache Cleanup
0 2 * * *   find .data_cache -name "*.json" -mtime +1 -delete
```

### Directory Structure

```
AI_Employee_Vault/
├── Pending_Approval/    # Awaiting human approval
├── Approved/            # Approved, awaiting execution
├── Rejected/            # Rejected by human
├── Done/                # Completed actions
├── Needs_Action/        # Alerts and errors
├── Briefings/           # Weekly audit reports
├── Logs/                # Audit logs (JSONL)
└── .quarantine/         # Corrupted files
```

---

## Scalability & Performance

### Current Capacity

- **Email Processing**: ~100 emails/hour
- **Social Media Posts**: Limited by API rate limits
- **Odoo Operations**: ~50 operations/hour
- **Audit Logging**: ~1000 actions/hour
- **Data Collection**: ~10 sources/minute

### Bottlenecks

1. **Twitter API**: 50 tweets/24h (free tier)
2. **Facebook/Instagram**: 200 calls/hour
3. **File System**: Watchdog polling interval (1 second)
4. **Audit Logs**: Disk I/O for JSONL writes

### Optimization Strategies

1. **Caching**: 60-minute TTL for data collection
2. **Rate Limiting**: Proactive throttling at 80% capacity
3. **Batch Operations**: Group similar actions
4. **Async Processing**: Non-blocking I/O where possible

---

## Security Architecture

See [security-model.md](./security-model.md) for detailed security documentation.

### Key Security Features

1. **Approval Workflow**: Human-in-the-loop for all writes
2. **Audit Logging**: Complete activity trail
3. **Credential Management**: Environment variables, never committed
4. **Input Validation**: All inputs validated before processing
5. **Error Quarantine**: Corrupted files isolated
6. **Rate Limiting**: Prevents abuse and quota exhaustion

---

## Future Enhancements

### Planned Features

1. **Encryption at Rest**: Encrypt audit logs and sensitive data
2. **Multi-User Support**: Role-based access control
3. **Web Dashboard**: Real-time monitoring and control
4. **Webhook Support**: Real-time event notifications
5. **Advanced Analytics**: Machine learning for insights
6. **Mobile App**: Approval workflow on mobile devices

### Scalability Improvements

1. **Database Backend**: Replace file-based state with PostgreSQL
2. **Message Queue**: Redis/RabbitMQ for async processing
3. **Horizontal Scaling**: Multiple worker processes
4. **Cloud Deployment**: Kubernetes orchestration

---

## Conclusion

The AI Employee system provides a robust, secure, and scalable platform for business automation. Its modular architecture, approval-first design, and comprehensive audit logging make it suitable for production use while maintaining human oversight and control.

For more detailed documentation, see:
- [Watcher System](./watcher-system.md)
- [MCP Servers](./mcp-servers.md)
- [Security Model](./security-model.md)
