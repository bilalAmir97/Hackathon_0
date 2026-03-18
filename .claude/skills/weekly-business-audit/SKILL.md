# Weekly Business Audit & CEO Briefing

**Skill Name:** weekly-business-audit
**Category:** Gold Tier - Business Intelligence & Reporting
**MCP Required:** No (uses existing integrations)

## Purpose

Automatically generate comprehensive weekly business audits and CEO briefings by analyzing data from Odoo accounting, social media, email, WhatsApp, and task completion. Provides actionable insights, identifies bottlenecks, and makes proactive recommendations.

## Prerequisites

- All Silver Tier skills operational
- Odoo accounting integration configured
- Social media integrations active (LinkedIn, Facebook, Instagram, Twitter)
- Gmail and WhatsApp watchers running
- Business_Goals.md configured

## Setup

### 1. Configure Business Goals

Create or update `AI_Employee_Vault/Business_Goals.md`:

```markdown
---
last_updated: 2026-03-14
review_frequency: weekly
fiscal_year_start: 2026-01-01
---

# Business Goals - Q1 2026

## Revenue Targets

- **Monthly Goal:** $10,000
- **Q1 Goal:** $30,000
- **Annual Goal:** $120,000

## Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Social media engagement | > 3% | < 2% |
| Monthly recurring revenue | $5,000 | < $4,000 |
| Client retention rate | > 95% | < 90% |

## Active Projects

1. **Project Alpha** - Due: 2026-03-31 - Budget: $5,000 - Status: On Track
2. **Project Beta** - Due: 2026-04-15 - Budget: $8,000 - Status: At Risk
3. **Project Gamma** - Due: 2026-04-30 - Budget: $3,500 - Status: On Track

## Subscription Audit Rules

Flag for review if:
- No usage in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool
- Annual renewal approaching

## Business Priorities

1. Increase monthly recurring revenue
2. Improve client response time
3. Grow social media presence
4. Optimize operational costs
5. Launch new service offering
```

### 2. Schedule Weekly Audit

Add to crontab:

```bash
# Weekly business audit - Sunday at 8 PM
0 20 * * 0 cd $PROJECT_DIR && /home/bilal-amir/.local/bin/uv run python scripts/weekly_audit.py >> /tmp/ai-employee-cron.log 2>&1
```

Or use Claude Code directly:

```bash
# Every Sunday at 8 PM
0 20 * * 0 cd $PROJECT_DIR && claude --print "/weekly-business-audit generate"
```

## Usage

### Invoke the Skill

```bash
/weekly-business-audit [action] [options]
```

### Available Actions

1. **Generate Full Audit**
   ```
   /weekly-business-audit generate
   ```

2. **Generate Specific Section**
   ```
   /weekly-business-audit generate --section "financial"
   /weekly-business-audit generate --section "social-media"
   /weekly-business-audit generate --section "operations"
   ```

3. **Compare with Previous Week**
   ```
   /weekly-business-audit compare --weeks 2
   ```

4. **Generate Monthly Summary**
   ```
   /weekly-business-audit monthly-summary --month "2026-03"
   ```

## Audit Components

### 1. Financial Analysis (from Odoo)

```python
# Data collected:
- Total revenue (week, month, quarter)
- Outstanding invoices
- Overdue payments
- Expenses by category
- Profit margin
- Cash flow projection
```

### 2. Social Media Performance

```python
# Data collected from all platforms:
- Total reach and impressions
- Engagement rates
- Follower growth
- Top performing posts
- Lead generation
- Response time to mentions
```

### 3. Communication Analysis

```python
# Data from Gmail and WhatsApp:
- Emails processed
- Response time metrics
- Urgent items handled
- Client satisfaction indicators
- Pending action items
```

### 4. Task Completion

```python
# Data from Done folder:
- Tasks completed
- Average completion time
- Bottlenecks identified
- Project progress
- Deadline adherence
```

### 5. Operational Efficiency

```python
# System metrics:
- Watcher uptime
- Error rates
- Approval response time
- Automation success rate
```

## CEO Briefing Template

Generated file: `AI_Employee_Vault/Briefings/YYYY-MM-DD_Weekly_Briefing.md`

```markdown
---
generated: 2026-03-14T20:00:00Z
period: 2026-03-08 to 2026-03-14
week_number: 11
fiscal_quarter: Q1
---

# Weekly CEO Briefing - Week of March 8, 2026

## 📊 Executive Summary

Strong week with revenue ahead of target. Social media engagement up 25%. One project at risk requires attention.

**Overall Health Score:** 8.5/10 ⭐⭐⭐⭐

---

## 💰 Financial Performance

### Revenue

- **This Week:** $2,850
- **Month-to-Date:** $8,450 (84.5% of $10,000 target)
- **Quarter-to-Date:** $24,300 (81% of $30,000 target)
- **Trend:** ✅ On track to exceed monthly goal

### Outstanding Invoices

| Client | Amount | Due Date | Days Overdue | Status |
|--------|--------|----------|--------------|--------|
| Client A | $1,500 | 2026-03-10 | 4 days | ⚠️ Follow up |
| Client B | $2,000 | 2026-03-20 | - | ✅ On time |
| Client C | $800 | 2026-03-25 | - | ✅ On time |

**Total Outstanding:** $4,300

### Expenses

| Category | This Week | Budget | Variance |
|----------|-----------|--------|----------|
| Software | $150 | $200 | ✅ -$50 |
| Marketing | $300 | $400 | ✅ -$100 |
| Operations | $100 | $150 | ✅ -$50 |

**Total Expenses:** $550
**Net Profit:** $2,300 (83% margin)

---

## 📱 Social Media Performance

### Overall Metrics

| Platform | Posts | Reach | Engagement | Followers |
|----------|-------|-------|------------|-----------|
| LinkedIn | 5 | 3,421 | 4.2% | +15 |
| Facebook | 4 | 2,856 | 3.8% | +12 |
| Instagram | 5 | 2,134 | 6.2% | +23 |
| Twitter | 12 | 5,678 | 3.5% | +18 |

**Total Reach:** 14,089 (+22% vs last week)
**Average Engagement:** 4.4% (+0.8% vs last week)
**New Followers:** +68 (+35% vs last week)

### Top Performing Content

1. **LinkedIn:** "5 ways AI transforms business" - 1,234 reach, 67 engagements
2. **Instagram:** "Behind the scenes" - 856 reach, 53 engagements
3. **Twitter:** "Automation tips thread" - 2,345 impressions, 89 engagements

### Lead Generation

- **Inquiries from Social:** 8 (5 LinkedIn, 2 Twitter, 1 Instagram)
- **Qualified Leads:** 3
- **Conversion Rate:** 37.5%

---

## 📧 Communication Metrics

### Email Performance

- **Emails Processed:** 127
- **Average Response Time:** 18 hours ✅ (target: < 24h)
- **Urgent Items:** 5 (all handled within 4 hours)
- **Client Satisfaction:** 4.8/5.0

### WhatsApp Activity

- **Messages Processed:** 43
- **Urgent Keywords Detected:** 7
- **Average Response Time:** 2.3 hours ✅
- **Client Inquiries:** 12 (10 responded, 2 pending)

---

## ✅ Task Completion

### This Week's Achievements

- ✅ Client A invoice sent and paid
- ✅ Project Alpha milestone 3 delivered (on time)
- ✅ Weekly social media content scheduled
- ✅ Monthly financial report generated
- ✅ New service page launched

**Total Tasks Completed:** 23
**On-Time Completion Rate:** 91% ✅

### Bottlenecks Identified

| Task | Expected | Actual | Delay | Reason |
|------|----------|--------|-------|--------|
| Client B proposal | 2 days | 5 days | +3 days | Awaiting client feedback |
| Project Beta design | 3 days | 6 days | +3 days | Scope creep |

---

## 🎯 Project Status

### Active Projects

1. **Project Alpha** (Client A - $5,000)
   - Status: ✅ On Track
   - Progress: 75% complete
   - Next Milestone: Final delivery (March 31)
   - Risk Level: Low

2. **Project Beta** (Client B - $8,000)
   - Status: ⚠️ At Risk
   - Progress: 45% complete (expected 60%)
   - Next Milestone: Design approval (March 20)
   - Risk Level: Medium
   - **Action Required:** Schedule client meeting to address scope changes

3. **Project Gamma** (Client C - $3,500)
   - Status: ✅ On Track
   - Progress: 30% complete
   - Next Milestone: Phase 1 delivery (April 15)
   - Risk Level: Low

---

## 💡 Proactive Recommendations

### Cost Optimization

1. **Notion Subscription** - $15/month
   - Last activity: 52 days ago
   - Recommendation: ❌ Cancel subscription
   - Savings: $180/year
   - **Action:** Move to Pending_Approval/CANCEL_notion_subscription.md

2. **Adobe Creative Cloud** - $54.99/month
   - Usage: 2 hours this month
   - Recommendation: ⚠️ Consider downgrading to Photography plan ($9.99/month)
   - Potential Savings: $540/year

### Revenue Opportunities

1. **Upsell to Client A**
   - Project Alpha completing ahead of schedule
   - Client satisfaction: 5/5
   - Recommendation: Propose Phase 2 expansion ($3,000)
   - **Action:** Draft proposal by March 18

2. **Social Media Leads**
   - 3 qualified leads from LinkedIn this week
   - Recommendation: Schedule discovery calls within 48 hours
   - Potential Revenue: $5,000-$8,000

### Operational Improvements

1. **Response Time**
   - Current: 18 hours average
   - Target: < 12 hours
   - Recommendation: Implement auto-response templates for common inquiries

2. **Social Media Posting**
   - Best engagement: 10 AM - 12 PM weekdays
   - Recommendation: Reschedule 60% of posts to this window

---

## 🚨 Alerts & Action Items

### High Priority

- [ ] Follow up on Client A overdue invoice ($1,500) - **Due: March 15**
- [ ] Schedule Project Beta scope meeting - **Due: March 16**
- [ ] Respond to 3 LinkedIn leads - **Due: March 15**

### Medium Priority

- [ ] Review and approve Notion cancellation
- [ ] Draft upsell proposal for Client A
- [ ] Update Project Beta timeline

### Low Priority

- [ ] Optimize social media posting schedule
- [ ] Review Adobe subscription usage
- [ ] Update Company_Handbook.md with new guidelines

---

## 📈 Trends & Insights

### Positive Trends

- ✅ Revenue growth: +15% vs last week
- ✅ Social media engagement: +25% vs last week
- ✅ Email response time: Improved from 22h to 18h
- ✅ Client satisfaction: Maintained 4.8/5.0

### Areas for Improvement

- ⚠️ Project Beta timeline slippage
- ⚠️ Invoice collection time increasing (avg 8 days, target 5 days)
- ⚠️ Subscription costs not optimized

### Key Insights

1. **LinkedIn is top lead source** - 62% of social media inquiries
2. **Morning posts perform best** - 40% higher engagement
3. **Client A is expansion opportunity** - High satisfaction + budget available
4. **Project Beta needs attention** - Risk of timeline/budget overrun

---

## 📅 Upcoming This Week

### Key Deadlines

- March 15: Client A invoice follow-up
- March 16: Project Beta scope meeting
- March 18: Client A upsell proposal due
- March 20: Project Beta design approval
- March 21: Monthly financial report

### Scheduled Activities

- 5 social media posts (LinkedIn, Facebook, Instagram, Twitter)
- 2 client check-in calls
- 1 project milestone delivery
- Weekly team sync (if applicable)

---

## 🎯 Goals for Next Week

1. Collect overdue invoice from Client A
2. Resolve Project Beta scope issues
3. Convert 2 of 3 LinkedIn leads
4. Maintain < 20 hour email response time
5. Increase social media engagement to 5%

---

**Generated by AI Employee v1.0**
*Next briefing: Sunday, March 21, 2026 at 8:00 PM*
```

## Audit Script Implementation

The audit script (`scripts/weekly_audit.py`) collects data from:

```python
# Data sources
1. Odoo API - Financial data
2. Social media APIs - Engagement metrics
3. Gmail API - Email statistics
4. WhatsApp session - Message counts
5. Vault folders - Task completion
6. Logs - System performance
```

## Integration with Dashboard

Updates `AI_Employee_Vault/Dashboard.md` with summary:

```markdown
# AI Employee Dashboard

**Last Updated:** 2026-03-14 20:00

## This Week's Highlights

- 💰 Revenue: $2,850 (on track for monthly goal)
- 📱 Social reach: 14,089 (+22%)
- ✅ Tasks completed: 23 (91% on-time)
- ⚠️ 1 project at risk (Project Beta)

## Quick Actions Needed

- [ ] Follow up on overdue invoice ($1,500)
- [ ] Schedule Project Beta meeting
- [ ] Respond to 3 LinkedIn leads

[View Full Weekly Briefing →](Briefings/2026-03-14_Weekly_Briefing.md)
```

## Notification System

After generating briefing, create notification:

```markdown
---
type: notification
priority: high
created: 2026-03-14T20:00:00Z
---

# Weekly Business Briefing Ready

Your weekly CEO briefing for March 8-14, 2026 is ready for review.

**Key Highlights:**
- Revenue: $2,850 this week (on track)
- Social media reach up 22%
- 3 high-priority action items

[View Full Briefing](Briefings/2026-03-14_Weekly_Briefing.md)
```

## Customization

Configure audit preferences in `Company_Handbook.md`:

```markdown
## Weekly Audit Configuration

### Report Sections
- Financial: ✅ Enabled
- Social Media: ✅ Enabled
- Communication: ✅ Enabled
- Projects: ✅ Enabled
- Recommendations: ✅ Enabled

### Alert Thresholds
- Revenue below target: 80%
- Overdue invoices: > 7 days
- Response time: > 24 hours
- Project delay: > 3 days
- Engagement rate: < 2%

### Notification Preferences
- Email summary: ✅ Enabled
- Dashboard update: ✅ Enabled
- Slack notification: ❌ Disabled
```

## Error Handling

- **Data Source Unavailable:** Use cached data, note in report
- **API Rate Limit:** Retry with exponential backoff
- **Incomplete Data:** Generate partial report, flag missing sections
- **Generation Failed:** Alert user, save debug log

## Logging

All audit operations logged to `AI_Employee_Vault/Logs/audit_YYYYMMDD.log`:

```json
{
  "timestamp": "2026-03-14T20:00:00Z",
  "action": "weekly_audit_generated",
  "period": "2026-03-08 to 2026-03-14",
  "sections": ["financial", "social", "communication", "tasks"],
  "data_sources": {
    "odoo": "success",
    "linkedin": "success",
    "facebook": "success",
    "instagram": "success",
    "twitter": "success",
    "gmail": "success",
    "whatsapp": "success"
  },
  "recommendations": 5,
  "alerts": 3,
  "result": "success"
}
```

## Troubleshooting

**Q: Audit report is incomplete**
- Check if all data sources are accessible
- Verify API credentials are valid
- Review error logs for specific failures

**Q: Financial data is incorrect**
- Verify Odoo connection
- Check date range configuration
- Ensure fiscal year is set correctly

**Q: Social media metrics missing**
- Confirm all platform integrations are active
- Check API rate limits
- Verify access tokens haven't expired

## References

- [Business Intelligence Best Practices](https://example.com/bi-practices)
- [KPI Tracking Guide](https://example.com/kpi-guide)

## Gold Tier Completion Criteria

- ✅ Weekly audit script implemented
- ✅ CEO briefing template configured
- ✅ All data sources integrated
- ✅ Proactive recommendations enabled
- ✅ Notification system working
- ✅ Dashboard integration complete
- ✅ Scheduled execution via cron
- ✅ Error handling implemented
