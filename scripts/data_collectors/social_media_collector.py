"""
Social Media Data Collector

Collects engagement data from Facebook, Instagram, and Twitter.
Retrieves post counts, engagement metrics, and audience growth.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class SocialMediaCollector:
    """Collects data from all social media platforms."""

    def __init__(self):
        """Initialize social media collector."""
        self.facebook_available = self._check_facebook_credentials()
        self.instagram_available = self._check_instagram_credentials()
        self.twitter_available = self._check_twitter_credentials()

    def _check_facebook_credentials(self) -> bool:
        """Check if Facebook credentials are available."""
        return bool(os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN'))

    def _check_instagram_credentials(self) -> bool:
        """Check if Instagram credentials are available."""
        return bool(os.getenv('INSTAGRAM_ACCOUNT_ID'))

    def _check_twitter_credentials(self) -> bool:
        """Check if Twitter credentials are available."""
        return bool(os.getenv('TWITTER_API_KEY'))

    def collect_facebook_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Collect Facebook engagement data.

        Args:
            days: Number of days to look back

        Returns:
            Dict with post count and engagement metrics
        """
        if not self.facebook_available:
            return {
                'available': False,
                'message': 'Facebook credentials not configured'
            }

        try:
            from mcp_servers.facebook_instagram_client import FacebookInstagramClient

            client = FacebookInstagramClient()

            # Get recent posts (simplified - actual implementation would filter by date)
            # For now, return placeholder data structure
            return {
                'available': True,
                'platform': 'facebook',
                'period_days': days,
                'posts_count': 0,  # Would be populated by actual API call
                'total_likes': 0,
                'total_comments': 0,
                'total_shares': 0,
                'engagement_rate': 0.0,
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }

    def collect_instagram_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Collect Instagram engagement data.

        Args:
            days: Number of days to look back

        Returns:
            Dict with post count and engagement metrics
        """
        if not self.instagram_available:
            return {
                'available': False,
                'message': 'Instagram credentials not configured'
            }

        try:
            from mcp_servers.facebook_instagram_client import FacebookInstagramClient

            client = FacebookInstagramClient()

            # Get recent posts (simplified)
            return {
                'available': True,
                'platform': 'instagram',
                'period_days': days,
                'posts_count': 0,
                'total_likes': 0,
                'total_comments': 0,
                'engagement_rate': 0.0,
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }

    def collect_twitter_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Collect Twitter engagement data.

        Args:
            days: Number of days to look back

        Returns:
            Dict with tweet count and engagement metrics
        """
        if not self.twitter_available:
            return {
                'available': False,
                'message': 'Twitter credentials not configured'
            }

        try:
            from mcp_servers.twitter_client import TwitterClient

            client = TwitterClient()

            # Get account metrics
            account_metrics = client.get_account_metrics()

            # Get mentions (last 7 days)
            mentions = client.get_mentions(max_results=100)

            return {
                'available': True,
                'platform': 'twitter',
                'period_days': days,
                'followers_count': account_metrics.get('followers_count', 0),
                'tweet_count': account_metrics.get('tweet_count', 0),
                'mentions_count': len(mentions),
                'collected_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'available': True,
                'error': str(e),
                'collected_at': datetime.now().isoformat()
            }

    def collect_all_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Collect data from all available social media platforms.

        Args:
            days: Number of days to look back

        Returns:
            Dict with data from all platforms
        """
        return {
            'facebook': self.collect_facebook_data(days),
            'instagram': self.collect_instagram_data(days),
            'twitter': self.collect_twitter_data(days),
            'summary': {
                'platforms_configured': sum([
                    self.facebook_available,
                    self.instagram_available,
                    self.twitter_available
                ]),
                'period_days': days
            },
            'collected_at': datetime.now().isoformat()
        }


def collect_social_media_data(days: int = 7) -> Dict[str, Any]:
    """
    Convenience function to collect social media data.

    Args:
        days: Number of days to look back

    Returns:
        Dict with data from all platforms
    """
    collector = SocialMediaCollector()
    return collector.collect_all_data(days)


if __name__ == "__main__":
    """Test the collector."""
    print("Collecting social media data...")
    data = collect_social_media_data()

    print("\n=== Social Media Summary ===")
    summary = data.get('summary', {})
    print(f"Platforms Configured: {summary.get('platforms_configured', 0)}/3")

    for platform in ['facebook', 'instagram', 'twitter']:
        platform_data = data.get(platform, {})
        if platform_data.get('available'):
            print(f"\n{platform.title()}:")
            if 'error' in platform_data:
                print(f"  Error: {platform_data['error']}")
            else:
                print(f"  Posts: {platform_data.get('posts_count', platform_data.get('tweet_count', 0))}")
                if platform == 'twitter':
                    print(f"  Followers: {platform_data.get('followers_count', 0)}")
                    print(f"  Mentions: {platform_data.get('mentions_count', 0)}")
        else:
            print(f"\n{platform.title()}: Not configured")
