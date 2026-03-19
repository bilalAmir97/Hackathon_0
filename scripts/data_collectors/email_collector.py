"""
Email Data Collector

Collects email activity data from Gmail.
Retrieves sent/received counts, approval workflow activity.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class EmailDataCollector:
    """Collects email activity data."""

    def __init__(self):
        """Initialize email data collector."""
        self.gmail_available = self._check_gmail_credentials()

    def _check_gmail_credentials(self) -> bool:
        """Check if Gmail credentials are available."""
        credentials_path = Path('credentials.json')
        token_path = Path('token.json')
        return credentials_path.exists() or token_path.exists()

    def collect_email_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Collect email activity data.

        Args:
            days: Number of days to look back

        Returns:
            Dict with email counts and activity
        """
        if not self.gmail_available:
            return {
                'available': False,
                'message': 'Gmail credentials not configured'
            }

        try:
            from mcp_servers.email_client import get_email_client

            client = get_email_client()

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get sent emails (simplified - would need actual query implementation)
            # For now, return structure with placeholder data
            return {
                'available': True,
                'period_days': days,
                'emails_sent': 0,  # Would be populated by actual query
                'emails_received': 0,
                'approval_requests_sent': 0,
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }


def collect_email_data(days: int = 7) -> Dict[str, Any]:
    """
    Convenience function to collect email data.

    Args:
        days: Number of days to look back

    Returns:
        Dict with email activity data
    """
    collector = EmailDataCollector()
    return collector.collect_email_data(days)


if __name__ == "__main__":
    """Test the collector."""
    print("Collecting email data...")
    data = collect_email_data()

    print("\n=== Email Summary ===")
    if data.get('available'):
        if 'error' in data:
            print(f"Error: {data['error']}")
        else:
            print(f"Emails Sent: {data.get('emails_sent', 0)}")
            print(f"Emails Received: {data.get('emails_received', 0)}")
            print(f"Approval Requests: {data.get('approval_requests_sent', 0)}")
    else:
        print("Gmail not configured")
