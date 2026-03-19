"""
Data Aggregator

Main script to collect data from all sources for business intelligence.
Aggregates data from Odoo, social media, email, and audit logs.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.data_collectors.odoo_collector import collect_odoo_data
from scripts.data_collectors.social_media_collector import collect_social_media_data
from scripts.data_collectors.email_collector import collect_email_data
from scripts.data_collectors.audit_log_collector import collect_audit_data


class DataAggregator:
    """Aggregates data from all integrated systems."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize data aggregator.

        Args:
            cache_dir: Directory to cache collected data (default: .data_cache)
        """
        self.cache_dir = Path(cache_dir or '.data_cache')
        self.cache_dir.mkdir(exist_ok=True)

    def collect_all_data(
        self,
        days: int = 7,
        use_cache: bool = True,
        cache_ttl_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Collect data from all sources.

        Args:
            days: Number of days to look back
            use_cache: Whether to use cached data if available
            cache_ttl_minutes: Cache time-to-live in minutes

        Returns:
            Dict with data from all sources
        """
        # Check cache
        if use_cache:
            cached_data = self._get_cached_data(cache_ttl_minutes)
            if cached_data:
                print("✅ Using cached data")
                return cached_data

        print("📊 Collecting data from all sources...")

        # Collect from all sources
        data = {
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'period_days': days,
                'version': '1.0'
            },
            'odoo': self._collect_with_error_handling('Odoo', lambda: collect_odoo_data()),
            'social_media': self._collect_with_error_handling('Social Media', lambda: collect_social_media_data(days)),
            'email': self._collect_with_error_handling('Email', lambda: collect_email_data(days)),
            'audit': self._collect_with_error_handling('Audit Logs', lambda: collect_audit_data(days))
        }

        # Cache the data
        self._cache_data(data)

        return data

    def _collect_with_error_handling(self, source_name: str, collector_func) -> Dict[str, Any]:
        """
        Collect data with error handling.

        Args:
            source_name: Name of data source
            collector_func: Function to collect data

        Returns:
            Collected data or error dict
        """
        try:
            print(f"  📥 Collecting {source_name} data...")
            data = collector_func()
            print(f"  ✅ {source_name} data collected")
            return data
        except Exception as e:
            print(f"  ❌ {source_name} collection failed: {e}")
            return {
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }

    def _get_cached_data(self, ttl_minutes: int) -> Optional[Dict[str, Any]]:
        """
        Get cached data if available and not expired.

        Args:
            ttl_minutes: Cache TTL in minutes

        Returns:
            Cached data or None
        """
        cache_file = self.cache_dir / 'aggregated_data.json'

        if not cache_file.exists():
            return None

        # Check if cache is expired
        cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
        if cache_age > ttl_minutes * 60:
            return None

        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def _cache_data(self, data: Dict[str, Any]) -> None:
        """
        Cache collected data.

        Args:
            data: Data to cache
        """
        cache_file = self.cache_dir / 'aggregated_data.json'

        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to cache data: {e}")

    def generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary from collected data.

        Args:
            data: Aggregated data

        Returns:
            Dict with summary metrics
        """
        summary = {
            'period_days': data.get('metadata', {}).get('period_days', 7),
            'collected_at': data.get('metadata', {}).get('collected_at'),
            'sources': {}
        }

        # Odoo summary
        odoo = data.get('odoo', {})
        if 'financial' in odoo:
            financial = odoo['financial'].get('summary', {})
            summary['sources']['odoo'] = {
                'available': True,
                'revenue': financial.get('total_revenue', 0),
                'expenses': financial.get('total_expenses', 0),
                'net_profit': financial.get('net_profit', 0),
                'invoices': financial.get('invoice_count', 0)
            }
        else:
            summary['sources']['odoo'] = {'available': False}

        # Social media summary
        social = data.get('social_media', {})
        summary['sources']['social_media'] = {
            'platforms_configured': social.get('summary', {}).get('platforms_configured', 0),
            'twitter_followers': social.get('twitter', {}).get('followers_count', 0),
            'twitter_mentions': social.get('twitter', {}).get('mentions_count', 0)
        }

        # Audit summary
        audit = data.get('audit', {})
        if 'audit_logs' in audit:
            audit_summary = audit['audit_logs'].get('summary', {})
            summary['sources']['audit'] = {
                'available': True,
                'total_actions': audit_summary.get('total_actions', 0),
                'approvals_granted': audit_summary.get('approvals_granted', 0),
                'approval_rate': audit_summary.get('approval_rate', 0),
                'errors': audit_summary.get('error_count', 0)
            }
        else:
            summary['sources']['audit'] = {'available': False}

        # System health
        if 'system_health' in audit:
            health = audit['system_health']
            summary['system_health'] = {
                'status': health.get('system_status', 'unknown'),
                'alerts': health.get('alert_count', 0)
            }

        return summary


def aggregate_data(days: int = 7, use_cache: bool = True) -> Dict[str, Any]:
    """
    Convenience function to aggregate data from all sources.

    Args:
        days: Number of days to look back
        use_cache: Whether to use cached data

    Returns:
        Dict with aggregated data
    """
    aggregator = DataAggregator()
    return aggregator.collect_all_data(days=days, use_cache=use_cache)


def main():
    """Main entry point for data aggregation."""
    import argparse

    parser = argparse.ArgumentParser(description='Aggregate data from all sources')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back')
    parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    parser.add_argument('--output', type=str, help='Output file path (JSON)')
    parser.add_argument('--summary', action='store_true', help='Show summary only')

    args = parser.parse_args()

    # Collect data
    aggregator = DataAggregator()
    data = aggregator.collect_all_data(days=args.days, use_cache=not args.no_cache)

    # Generate summary
    if args.summary:
        summary = aggregator.generate_summary(data)
        print("\n" + "=" * 60)
        print("EXECUTIVE SUMMARY")
        print("=" * 60)
        print(json.dumps(summary, indent=2))
    else:
        print("\n" + "=" * 60)
        print("DATA COLLECTION COMPLETE")
        print("=" * 60)
        print(f"Period: Last {args.days} days")
        print(f"Collected at: {data['metadata']['collected_at']}")

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✅ Data saved to: {output_path}")


if __name__ == "__main__":
    main()
