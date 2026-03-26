# Reports Data Guide

**What Data Do Weekly Audit and Daily Briefing Generate?**

This guide explains exactly what data is collected, analyzed, and presented in both automated reports.

---

## 📊 Weekly Business Audit

**Generated**: Every Sunday at 8 PM (with fallbacks)
**File Location**: `AI_Employee_Vault/Briefings/WEEKLY_AUDIT_YYYYMMDD_HHMMSS.md`
**Analysis Period**: Last 7 days

### Data Sources

The weekly audit aggregates data from **5 sources**:

1. **Odoo ERP** (`scripts/data_collectors/odoo_collector.py`)
   - Financial data (revenue, expenses, profit)
   - Invoice status (paid, pending, overdue)
   - Customer information

2. **Social Media** (`scripts/data_collectors/social_media_collector.py`)
   - Facebook posts and engagement
   - Instagram posts and engagement
   - Twitter tweets, followers, mentions

3. **Email Activity** (`scripts/data_collectors/email_collector.py`)
   - Emails processed
   - Priority emails detected
   - Response times

4. **Audit Logs** (`scripts/data_collectors/audit_log_collector.py`)
   - System actions performed
   - Approval workflow metrics
   - Error counts

5. **System Health** (`scripts/health_check.py`)
   - Pending approvals count
   - Active alerts
   - Service status

### Report Structure

#### 1. **Executive Summary**

**Key Metrics Table**:
```
| Metric              | Value      | Status |
|---------------------|------------|--------|
| Revenue             | $172.50    | ✅     |
| Net Profit          | $172.50    | ✅     |
| System Actions      | 3          | ✅     |
| Approval Rate       | 0%         | ⚠️     |
| System Health       | Needs_Attention | ⚠️  |
```

**Quick Insights**:
- Financial: "Profitable with 100.0% margin"
- Operations: "3 actions with 0% approval rate"
- Social Media: "2 platform(s) active, 0 Twitter followers"
- System: "5546 alert(s) need attention"

#### 2. **Financial Performance** (from Odoo)

**Revenue & Expenses**:
```
| Category          | Amount    | Percentage |
|-------------------|-----------|------------|
| Total Revenue     | $172.50   | 100%       |
| Total Expenses    | $0.00     | 0.0%       |
| Net Profit        | $172.50   | 100.0%     |
```

**Invoices**:
- Total Invoices: 1
- Paid: 1 (100%)
- Pending: 0 (0%)

**Customers**:
- Total Customers: 1

**Analysis**:
- Automated insights about profitability
- Warnings about pending invoices
- Recommendations for cash flow improvement

#### 3. **Social Media Performance**

**Platform Overview**:

**Twitter** (if configured):
- Followers count
- Total tweets
- Mentions count

**Facebook** (if configured):
- Posts count
- Total engagement (likes + comments + shares)

**Instagram** (if configured):
- Posts count
- Total engagement (likes + comments)

**Analysis**:
- Engagement trends
- Recommendations for increasing activity

#### 4. **System Health**

**Activity Summary**:
- Total Actions: 3
- Approvals Granted: 0
- Approvals Denied: 0
- Approval Rate: 0%
- Errors: 0

**Workflow Status**:
- Pending Approvals: 7
- Completed: 42

**System Status**:
- Health: Needs_Attention
- Active Alerts: 5546

**Top Actions**:
- social_media_post: 3
- email_send: 2
- invoice_create: 1

**Analysis**:
- Warnings about high alert counts
- Recommendations for addressing issues

#### 5. **Recommendations**

Actionable recommendations based on data:
1. "Address system alerts: 5546 alerts in Needs_Action folder require attention"
2. "Expand social media presence: Configure additional platforms for broader reach"
3. "Follow up on pending invoices: Contact customers to improve cash flow"

#### 6. **Next Steps Checklist**

```
- [ ] Review financial performance
- [ ] Address pending approvals
- [ ] Investigate any system alerts
- [ ] Implement recommendations
```

---

## 📋 Daily Briefing

**Generated**: Every day at 9 PM (with fallbacks)
**File Location**: `AI_Employee_Vault/Briefings/BRIEFING_YYYY-MM-DD.md`
**Analysis Period**: Today + Yesterday

### Data Sources

The daily briefing collects data from **4 sources**:

1. **Needs_Action Folder**
   - Counts pending tasks by type
   - Identifies urgent items

2. **Done Folder**
   - Counts completed tasks from yesterday
   - Tracks completion rate

3. **Audit Logs**
   - Yesterday's activity breakdown
   - Action types and counts

4. **System Status**
   - Watcher service status
   - Last check timestamp

### Report Structure

#### 1. **System Status**

```
Watchers: Running ✓
Last Check: 15:16:04
```

Shows if all monitoring services are operational.

#### 2. **Pending Tasks** (Real-time count)

```
📥 Pending Tasks (5553 total)

- 📧 Email: 4
- 📱 WhatsApp: 2
- ✋ Approval: 5
- ⚠️ Alert: 5541
- 📄 Other: 1
```

**Task Types Detected**:
- **Email**: Files with "EMAIL" in name
- **WhatsApp**: Files with "WHATSAPP" in name
- **Approval**: Files with "APPROVAL" in name
- **Alert**: Files with "ALERT" in name
- **Other**: Everything else

#### 3. **Yesterday's Activity**

```
- Total Actions: 0
- Tasks Completed: 29
```

**Breakdown** (if available):
- email_send: 5
- social_media_post: 3
- invoice_create: 2

Shows what the AI Employee accomplished yesterday.

#### 4. **Today's Focus**

**Priority Items** (files with "URGENT" in name):
```
- URGENT_CLIENT_TechStartup_2026-02-19
- URGENT_INVOICE_Payment_Due
```

Lists up to 5 most urgent items requiring immediate attention.

---

## Data Collection Process

### Weekly Audit Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Data Aggregator (aggregate_data.py)                     │
│    Orchestrates collection from all sources                 │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Odoo         │   │ Social Media │   │ Audit Logs   │
│ Collector    │   │ Collector    │   │ Collector    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────┐
│ 2. Data Aggregation                                  │
│    Combines all data into unified structure          │
└──────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│ 3. Analysis & Insights                               │
│    Calculates metrics, trends, recommendations       │
└──────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│ 4. Report Generation                                 │
│    Formats markdown report with all sections         │
└──────────────────────────────────────────────────────┘
```

### Daily Briefing Data Flow

```
┌─────────────────────────────────────────────────────┐
│ 1. Scan Needs_Action Folder                        │
│    Count files by type (email, whatsapp, etc.)     │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 2. Scan Done Folder                                │
│    Count files modified yesterday                   │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 3. Read Yesterday's Audit Logs                     │
│    Parse JSONL logs for activity breakdown          │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 4. Identify Priority Items                         │
│    Find files with "URGENT" in name                 │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 5. Generate Briefing                               │
│    Format markdown with all sections                │
└─────────────────────────────────────────────────────┘
```

---

## Example: Real Data from Your System

### Weekly Audit (March 26, 2026)

**Financial Performance**:
- Revenue: $172.50 (from 1 paid invoice)
- Net Profit: $172.50 (100% margin - no expenses)
- 1 customer in system

**Social Media**:
- 2 platforms configured
- 3 social media posts made
- No Twitter followers yet

**System Health**:
- 3 total actions performed
- 0% approval rate (no approvals granted/denied)
- 5546 active alerts (needs attention!)
- 7 pending approvals
- 42 completed tasks

**Recommendations**:
1. Address 5546 system alerts
2. Expand social media presence
3. Review approval workflow

### Daily Briefing (March 26, 2026)

**Pending Tasks**: 5553 total
- 4 emails
- 2 WhatsApp messages
- 5 approvals
- 5541 alerts (mostly old gmail watcher alerts)
- 1 other

**Yesterday's Activity**:
- 0 actions logged
- 29 tasks completed

**Today's Focus**:
- 1 urgent item: URGENT_CLIENT_TechStartup_2026-02-19

---

## Data Accuracy & Reliability

### What's Included

✅ **Real-time data** from vault folders (Needs_Action, Done)
✅ **Historical data** from audit logs (JSONL format)
✅ **Live API data** from Odoo, Facebook, Instagram, Twitter
✅ **Calculated metrics** (approval rate, profit margin, etc.)
✅ **Automated insights** based on thresholds and patterns

### What's NOT Included

❌ **Predictive analytics** (no forecasting)
❌ **External market data** (only your business data)
❌ **Manual notes** (unless added to vault files)
❌ **Real-time alerts** (reports are snapshots)

### Data Freshness

| Data Source | Freshness | Update Frequency |
|-------------|-----------|------------------|
| Vault Folders | Real-time | Instant |
| Audit Logs | Near real-time | Every action |
| Odoo Data | Live | API call during generation |
| Social Media | Live | API call during generation |
| System Health | Real-time | Calculated on demand |

---

## Customization Options

### Weekly Audit

**Change analysis period**:
```bash
python scripts/generate_weekly_audit.py --days 14  # 2 weeks
python scripts/generate_weekly_audit.py --days 30  # 1 month
```

**Custom output location**:
```bash
python scripts/generate_weekly_audit.py --output custom_report.md
```

### Daily Briefing

Currently no customization options, but you can modify:
- `scripts/daily_briefing.py` to add custom sections
- Task type detection logic
- Priority item identification

---

## Troubleshooting

### "No data available" in reports

**Cause**: Data source not configured or no activity

**Solutions**:
- **Odoo**: Verify Odoo is running and credentials in `.env`
- **Social Media**: Check API tokens in `.env`
- **Audit Logs**: Ensure audit logger is enabled
- **Activity**: Generate some test data (send email, create invoice)

### High alert count (5546 alerts)

**Cause**: Old gmail watcher alerts accumulating

**Solution**:
```bash
# Move old alerts to archive
mv AI_Employee_Vault/Needs_Action/ALERT_*.md AI_Employee_Vault/.archive/

# Or delete if not needed
rm AI_Employee_Vault/Needs_Action/ALERT_202603*.md
```

### Missing social media data

**Cause**: Platforms not configured or no posts

**Solution**:
- Configure Facebook/Instagram/Twitter in `.env`
- Create test posts to generate data
- Wait for API rate limits to reset

---

## Summary

### Weekly Audit Provides:
- 📊 **Financial overview** (revenue, expenses, profit, invoices)
- 📱 **Social media metrics** (posts, engagement, followers)
- 🏥 **System health** (actions, approvals, errors, alerts)
- 💡 **Actionable recommendations** based on data analysis
- 📈 **7-day trends** and performance insights

### Daily Briefing Provides:
- 📥 **Pending task count** by type (email, WhatsApp, approvals, alerts)
- 📈 **Yesterday's activity** (actions performed, tasks completed)
- 🎯 **Today's priorities** (urgent items requiring attention)
- 📊 **System status** (watchers running, last check time)
- 📋 **Quick snapshot** for daily planning

Both reports are automatically generated, saved to `AI_Employee_Vault/Briefings/`, and provide comprehensive visibility into your AI Employee's operations and your business performance.
