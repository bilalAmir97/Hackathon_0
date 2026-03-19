"""
Weekly Business Audit Generator

Generates comprehensive weekly business intelligence reports by:
- Aggregating data from all sources (Odoo, social media, email, audit logs)
- Analyzing trends and performance metrics
- Generating actionable recommendations
- Creating formatted markdown reports in the vault

Usage:
    python scripts/generate_weekly_audit.py
    python scripts/generate_weekly_audit.py --days 7 --output custom_report.md
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_collectors.aggregate_data import DataAggregator


class WeeklyAuditGenerator:
    """Generates weekly business intelligence reports."""

    def __init__(self, vault_path: str = None):
        """
        Initialize weekly audit generator.

        Args:
            vault_path: Path to AI Employee Vault
        """
        self.vault_path = Path(vault_path or os.getenv('VAULT_PATH', './AI_Employee_Vault'))
        self.briefings_path = self.vault_path / 'Briefings'
        self.briefings_path.mkdir(parents=True, exist_ok=True)

        self.aggregator = DataAggregator()

    def generate_report(self, days: int = 7) -> str:
        """
        Generate weekly business audit report.

        Args:
            days: Number of days to analyze

        Returns:
            Path to generated report file
        """
        print(f"📊 Generating Weekly Business Audit ({days} days)...")

        # Collect data
        data = self.aggregator.collect_all_data(days=days, use_cache=False)

        # Generate report content
        report_content = self._build_report(data, days)

        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"WEEKLY_AUDIT_{timestamp}.md"
        report_path = self.briefings_path / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"✅ Report generated: {report_path}")

        return str(report_path)

    def _build_report(self, data: Dict[str, Any], days: int) -> str:
        """
        Build formatted markdown report.

        Args:
            data: Aggregated data from all sources
            days: Number of days analyzed

        Returns:
            Formatted markdown report
        """
        metadata = data.get('metadata', {})
        collected_at = metadata.get('collected_at', datetime.now().isoformat())

        # Build report sections
        sections = [
            self._build_header(days, collected_at),
            self._build_executive_summary(data),
            self._build_financial_section(data.get('odoo', {})),
            self._build_social_media_section(data.get('social_media', {})),
            self._build_system_health_section(data.get('audit', {})),
            self._build_recommendations(data),
            self._build_footer()
        ]

        return '\n\n'.join(sections)

    def _build_header(self, days: int, collected_at: str) -> str:
        """Build report header."""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        return f"""---
report_type: weekly_business_audit
period_days: {days}
period_start: {start_date}
period_end: {end_date}
generated_at: {collected_at}
version: 1.0
---

# 📊 Weekly Business Audit

**Period**: {start_date} to {end_date} ({days} days)
**Generated**: {datetime.fromisoformat(collected_at).strftime('%B %d, %Y at %I:%M %p')}

---"""

    def _build_executive_summary(self, data: Dict[str, Any]) -> str:
        """Build executive summary section."""
        summary = self.aggregator.generate_summary(data)

        odoo = summary.get('sources', {}).get('odoo', {})
        audit = summary.get('sources', {}).get('audit', {})
        social = summary.get('sources', {}).get('social_media', {})
        health = summary.get('system_health', {})

        # Calculate key metrics
        revenue = odoo.get('revenue', 0)
        net_profit = odoo.get('net_profit', 0)
        total_actions = audit.get('total_actions', 0)
        approval_rate = audit.get('approval_rate', 0)

        return f"""## 📈 Executive Summary

### Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Revenue** | ${revenue:,.2f} | {self._get_status_emoji(revenue > 0)} |
| **Net Profit** | ${net_profit:,.2f} | {self._get_status_emoji(net_profit > 0)} |
| **System Actions** | {total_actions} | {self._get_status_emoji(total_actions > 0)} |
| **Approval Rate** | {approval_rate:.0%} | {self._get_status_emoji(approval_rate > 0.5)} |
| **System Health** | {health.get('status', 'unknown').title()} | {self._get_health_emoji(health.get('status'))} |

### Quick Insights

- **Financial**: {self._get_financial_insight(odoo)}
- **Operations**: {self._get_operations_insight(audit)}
- **Social Media**: {self._get_social_insight(social)}
- **System**: {self._get_system_insight(health)}"""

    def _build_financial_section(self, odoo_data: Dict[str, Any]) -> str:
        """Build financial performance section."""
        if 'error' in odoo_data or not odoo_data.get('financial', {}).get('summary'):
            return """## 💰 Financial Performance

**Status**: Odoo not configured or no data available

Configure Odoo integration to track financial metrics."""

        financial = odoo_data['financial']['summary']
        customers = odoo_data.get('customers', {})

        revenue = financial.get('total_revenue', 0)
        expenses = financial.get('total_expenses', 0)
        net_profit = financial.get('net_profit', 0)
        invoices = financial.get('invoice_count', 0)
        paid = financial.get('paid_count', 0)
        pending = financial.get('pending_count', 0)

        return f"""## 💰 Financial Performance

### Revenue & Expenses

| Category | Amount | Percentage |
|----------|--------|------------|
| **Total Revenue** | ${revenue:,.2f} | 100% |
| **Total Expenses** | ${expenses:,.2f} | {(expenses/revenue*100 if revenue > 0 else 0):.1f}% |
| **Net Profit** | ${net_profit:,.2f} | {(net_profit/revenue*100 if revenue > 0 else 0):.1f}% |

### Invoices

- **Total Invoices**: {invoices}
- **Paid**: {paid} ({(paid/invoices*100 if invoices > 0 else 0):.0f}%)
- **Pending**: {pending} ({(pending/invoices*100 if invoices > 0 else 0):.0f}%)

### Customers

- **Total Customers**: {customers.get('customer_count', 0)}

### Analysis

{self._analyze_financial_performance(financial)}"""

    def _build_social_media_section(self, social_data: Dict[str, Any]) -> str:
        """Build social media performance section."""
        summary = social_data.get('summary', {})
        platforms_configured = summary.get('platforms_configured', 0)

        if platforms_configured == 0:
            return """## 📱 Social Media Performance

**Status**: No social media platforms configured

Configure Facebook, Instagram, or Twitter to track social media metrics."""

        twitter = social_data.get('twitter', {})
        facebook = social_data.get('facebook', {})
        instagram = social_data.get('instagram', {})

        sections = ["""## 📱 Social Media Performance

### Platform Overview"""]

        # Twitter
        if twitter.get('available') and 'error' not in twitter:
            sections.append(f"""
#### Twitter

- **Followers**: {twitter.get('followers_count', 0):,}
- **Total Tweets**: {twitter.get('tweet_count', 0):,}
- **Mentions**: {twitter.get('mentions_count', 0)}""")

        # Facebook
        if facebook.get('available') and 'error' not in facebook:
            sections.append(f"""
#### Facebook

- **Posts**: {facebook.get('posts_count', 0)}
- **Total Engagement**: {facebook.get('total_likes', 0) + facebook.get('total_comments', 0) + facebook.get('total_shares', 0)}""")

        # Instagram
        if instagram.get('available') and 'error' not in instagram:
            sections.append(f"""
#### Instagram

- **Posts**: {instagram.get('posts_count', 0)}
- **Total Engagement**: {instagram.get('total_likes', 0) + instagram.get('total_comments', 0)}""")

        sections.append(f"""
### Analysis

{self._analyze_social_performance(social_data)}""")

        return '\n'.join(sections)

    def _build_system_health_section(self, audit_data: Dict[str, Any]) -> str:
        """Build system health section."""
        audit_logs = audit_data.get('audit_logs', {})
        workflow = audit_data.get('workflow_metrics', {})
        health = audit_data.get('system_health', {})

        if not audit_logs.get('available'):
            return """## 🏥 System Health

**Status**: Audit logs not available"""

        summary = audit_logs.get('summary', {})
        actions_by_type = audit_logs.get('actions_by_type', {})

        return f"""## 🏥 System Health

### Activity Summary

- **Total Actions**: {summary.get('total_actions', 0)}
- **Approvals Granted**: {summary.get('approvals_granted', 0)}
- **Approvals Denied**: {summary.get('approvals_denied', 0)}
- **Approval Rate**: {summary.get('approval_rate', 0):.0%}
- **Errors**: {summary.get('error_count', 0)}

### Workflow Status

- **Pending Approvals**: {workflow.get('pending_count', 0)}
- **Completed**: {workflow.get('done_count', 0)}

### System Status

- **Health**: {health.get('system_status', 'unknown').title()}
- **Active Alerts**: {health.get('alert_count', 0)}

### Top Actions

{self._format_top_actions(actions_by_type)}

### Analysis

{self._analyze_system_health(summary, health)}"""

    def _build_recommendations(self, data: Dict[str, Any]) -> str:
        """Build recommendations section."""
        recommendations = self._generate_recommendations(data)

        if not recommendations:
            return """## 💡 Recommendations

No specific recommendations at this time. System is operating normally."""

        rec_list = '\n'.join([f"{i+1}. **{rec['title']}**: {rec['description']}"
                              for i, rec in enumerate(recommendations)])

        return f"""## 💡 Recommendations

{rec_list}"""

    def _build_footer(self) -> str:
        """Build report footer."""
        return """---

## 📝 Notes

This report was automatically generated by the AI Employee system. Review the data and take action on recommendations as needed.

**Next Steps**:
- [ ] Review financial performance
- [ ] Address pending approvals
- [ ] Investigate any system alerts
- [ ] Implement recommendations

---

*Generated by AI Employee - Weekly Business Audit System*"""

    def _get_status_emoji(self, is_positive: bool) -> str:
        """Get status emoji based on condition."""
        return "✅" if is_positive else "⚠️"

    def _get_health_emoji(self, status: str) -> str:
        """Get health emoji based on status."""
        if status == 'healthy':
            return "✅"
        elif status == 'needs_attention':
            return "⚠️"
        else:
            return "❓"

    def _get_financial_insight(self, odoo: Dict[str, Any]) -> str:
        """Generate financial insight."""
        if not odoo.get('available'):
            return "Not configured"

        revenue = odoo.get('revenue', 0)
        net_profit = odoo.get('net_profit', 0)

        if revenue == 0:
            return "No revenue recorded this period"
        elif net_profit > 0:
            return f"Profitable with {(net_profit/revenue*100):.1f}% margin"
        else:
            return "Operating at a loss"

    def _get_operations_insight(self, audit: Dict[str, Any]) -> str:
        """Generate operations insight."""
        if not audit.get('available'):
            return "Not available"

        total = audit.get('total_actions', 0)
        approval_rate = audit.get('approval_rate', 0)

        if total == 0:
            return "No activity recorded"
        else:
            return f"{total} actions with {approval_rate:.0%} approval rate"

    def _get_social_insight(self, social: Dict[str, Any]) -> str:
        """Generate social media insight."""
        platforms = social.get('platforms_configured', 0)
        followers = social.get('twitter_followers', 0)

        if platforms == 0:
            return "Not configured"
        else:
            return f"{platforms} platform(s) active, {followers} Twitter followers"

    def _get_system_insight(self, health: Dict[str, Any]) -> str:
        """Generate system health insight."""
        status = health.get('status', 'unknown')
        alerts = health.get('alerts', 0)

        if status == 'healthy':
            return "System operating normally"
        else:
            return f"{alerts} alert(s) need attention"

    def _analyze_financial_performance(self, financial: Dict[str, Any]) -> str:
        """Analyze financial performance."""
        revenue = financial.get('total_revenue', 0)
        net_profit = financial.get('net_profit', 0)
        pending = financial.get('pending_count', 0)

        insights = []

        if revenue == 0:
            insights.append("⚠️ No revenue recorded this period. Consider reviewing sales activities.")
        elif net_profit > 0:
            margin = (net_profit / revenue * 100)
            insights.append(f"✅ Profitable operations with {margin:.1f}% profit margin.")
        else:
            insights.append("⚠️ Operating at a loss. Review expenses and revenue streams.")

        if pending > 0:
            insights.append(f"⚠️ {pending} invoice(s) pending payment. Follow up with customers.")

        return '\n'.join(insights) if insights else "Financial performance is stable."

    def _analyze_social_performance(self, social_data: Dict[str, Any]) -> str:
        """Analyze social media performance."""
        twitter = social_data.get('twitter', {})
        mentions = twitter.get('mentions_count', 0)

        insights = []

        if mentions > 0:
            insights.append(f"✅ {mentions} Twitter mention(s) - engage with your audience.")
        else:
            insights.append("Consider increasing social media activity to boost engagement.")

        return '\n'.join(insights) if insights else "Social media presence is stable."

    def _analyze_system_health(self, summary: Dict[str, Any], health: Dict[str, Any]) -> str:
        """Analyze system health."""
        errors = summary.get('error_count', 0)
        alerts = health.get('alert_count', 0)
        approval_rate = summary.get('approval_rate', 0)

        insights = []

        if errors > 0:
            insights.append(f"⚠️ {errors} error(s) detected. Review audit logs for details.")

        if alerts > 0:
            insights.append(f"⚠️ {alerts} system alert(s) in Needs_Action folder. Address promptly.")

        if approval_rate < 0.5 and summary.get('approvals_granted', 0) + summary.get('approvals_denied', 0) > 0:
            insights.append(f"⚠️ Low approval rate ({approval_rate:.0%}). Review approval criteria.")

        return '\n'.join(insights) if insights else "✅ System is operating normally with no critical issues."

    def _format_top_actions(self, actions_by_type: Dict[str, int]) -> str:
        """Format top actions list."""
        if not actions_by_type:
            return "No actions recorded"

        sorted_actions = sorted(actions_by_type.items(), key=lambda x: x[1], reverse=True)[:5]
        return '\n'.join([f"- **{action}**: {count}" for action, count in sorted_actions])

    def _generate_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations."""
        recommendations = []

        # Financial recommendations
        odoo = data.get('odoo', {})
        if odoo.get('financial', {}).get('summary', {}).get('pending_count', 0) > 0:
            recommendations.append({
                'title': 'Follow up on pending invoices',
                'description': 'Contact customers with outstanding invoices to improve cash flow'
            })

        # System health recommendations
        audit = data.get('audit', {})
        alerts = audit.get('system_health', {}).get('alert_count', 0)
        if alerts > 10:
            recommendations.append({
                'title': 'Address system alerts',
                'description': f'{alerts} alerts in Needs_Action folder require attention'
            })

        # Social media recommendations
        social = data.get('social_media', {})
        if social.get('summary', {}).get('platforms_configured', 0) < 3:
            recommendations.append({
                'title': 'Expand social media presence',
                'description': 'Configure additional platforms (Facebook, Instagram, Twitter) for broader reach'
            })

        return recommendations


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate weekly business audit report')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--output', type=str, help='Custom output filename')

    args = parser.parse_args()

    generator = WeeklyAuditGenerator()
    report_path = generator.generate_report(days=args.days)

    print(f"\n✅ Weekly audit report generated successfully!")
    print(f"📄 Report location: {report_path}")
    print(f"\nView the report to see:")
    print("  - Financial performance summary")
    print("  - Social media metrics")
    print("  - System health analysis")
    print("  - Actionable recommendations")


if __name__ == "__main__":
    main()
