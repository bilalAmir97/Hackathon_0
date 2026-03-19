"""Rate Limiter for Meta Graph API.

Implements proactive rate limiting to prevent API errors:
- Parses rate limit headers from Meta API responses
- Tracks quota per endpoint
- Proactively throttles at configurable threshold (default 80%)
- Manages request queue when rate limited
- Implements exponential backoff for retries
"""

import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque


class RateLimiter:
    """Manages rate limiting for Meta Graph API requests."""

    def __init__(self, threshold: float = 0.8, cooldown_seconds: int = 3600):
        """
        Initialize RateLimiter.

        Args:
            threshold: Throttle threshold (0.0-1.0). Default 0.8 = throttle at 80% capacity
            cooldown_seconds: Default cooldown period in seconds (default 3600 = 1 hour)
        """
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds

        # Track rate limit state per endpoint
        # Format: {endpoint: {'limit': int, 'remaining': int, 'reset_time': datetime}}
        self._rate_limits: Dict[str, Dict] = {}

        # Request queue for rate-limited requests
        # Format: deque of (endpoint, timestamp, retry_count)
        self._queue: deque = deque()

        # Track last check time for cleanup
        self._last_cleanup = datetime.utcnow()

    def parse_rate_limit_headers(self, headers: Dict[str, str]) -> Dict[str, any]:
        """
        Parse rate limit information from Meta API response headers.

        Meta API returns rate limit info in these headers:
        - X-App-Usage: {"call_count":10,"total_cputime":5,"total_time":8}
        - X-Business-Use-Case-Usage: {"business_id":{"call_count":10,"total_cputime":5}}

        Args:
            headers: Response headers from Meta API

        Returns:
            Dictionary with parsed rate limit info:
            {
                'call_count': int,
                'total_cputime': int,
                'total_time': int,
                'limit': int (estimated),
                'remaining': int (estimated)
            }
        """
        import json

        # Defensive check: ensure headers is a dict
        if not isinstance(headers, dict):
            # If headers is not a dict, return default values
            return {
                'call_count': 0,
                'total_cputime': 0,
                'total_time': 0,
                'limit': 100,
                'remaining': 100
            }

        rate_info = {
            'call_count': 0,
            'total_cputime': 0,
            'total_time': 0,
            'limit': 100,  # Default estimate (Meta doesn't provide explicit limit)
            'remaining': 100
        }

        # Try X-App-Usage header first
        app_usage = headers.get('X-App-Usage') or headers.get('x-app-usage')
        if app_usage:
            try:
                usage_data = json.loads(app_usage)
                rate_info['call_count'] = usage_data.get('call_count', 0)
                rate_info['total_cputime'] = usage_data.get('total_cputime', 0)
                rate_info['total_time'] = usage_data.get('total_time', 0)

                # Estimate remaining based on call_count percentage
                # Meta typically allows 200 calls per hour per user
                rate_info['limit'] = 200
                rate_info['remaining'] = max(0, rate_info['limit'] - rate_info['call_count'])
            except (json.JSONDecodeError, KeyError):
                pass

        # Try X-Business-Use-Case-Usage header (for business accounts)
        business_usage = headers.get('X-Business-Use-Case-Usage') or headers.get('x-business-use-case-usage')
        if business_usage:
            try:
                usage_data = json.loads(business_usage)
                # Extract first business ID data
                for business_id, data in usage_data.items():
                    rate_info['call_count'] = data.get('call_count', rate_info['call_count'])
                    rate_info['total_cputime'] = data.get('total_cputime', rate_info['total_cputime'])
                    rate_info['limit'] = 200
                    rate_info['remaining'] = max(0, rate_info['limit'] - rate_info['call_count'])
                    break
            except (json.JSONDecodeError, KeyError):
                pass

        return rate_info

    def update_rate_limit(self, endpoint: str, headers: Dict[str, str]):
        """
        Update rate limit state from API response headers.

        Args:
            endpoint: API endpoint (e.g., 'facebook_post', 'instagram_post')
            headers: Response headers from Meta API
        """
        rate_info = self.parse_rate_limit_headers(headers)

        # Calculate reset time (1 hour from now by default)
        reset_time = datetime.utcnow() + timedelta(seconds=self.cooldown_seconds)

        self._rate_limits[endpoint] = {
            'limit': rate_info['limit'],
            'remaining': rate_info['remaining'],
            'call_count': rate_info['call_count'],
            'reset_time': reset_time,
            'last_updated': datetime.utcnow()
        }

    def check_rate_limit(self, endpoint: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request should be allowed based on rate limit.

        Args:
            endpoint: API endpoint to check

        Returns:
            Tuple of (is_allowed, reason)
            - (True, None) if request is allowed
            - (False, reason) if request should be throttled
        """
        # Clean up expired rate limits
        self._cleanup_expired_limits()

        # If no rate limit info for this endpoint, allow request
        if endpoint not in self._rate_limits:
            return True, None

        limit_info = self._rate_limits[endpoint]

        # Check if rate limit has reset
        if datetime.utcnow() >= limit_info['reset_time']:
            # Reset has occurred, clear the limit
            del self._rate_limits[endpoint]
            return True, None

        # Calculate usage percentage
        limit = limit_info['limit']
        remaining = limit_info['remaining']
        usage_percent = (limit - remaining) / limit if limit > 0 else 0

        # Check if we're above threshold
        if usage_percent >= self.threshold:
            seconds_until_reset = (limit_info['reset_time'] - datetime.utcnow()).total_seconds()
            return False, (
                f"Rate limit threshold reached ({usage_percent:.0%} of {limit} calls used). "
                f"Throttling until reset in {int(seconds_until_reset)}s"
            )

        # Check if completely rate limited (no remaining calls)
        if remaining <= 0:
            seconds_until_reset = (limit_info['reset_time'] - datetime.utcnow()).total_seconds()
            return False, (
                f"Rate limit exceeded (0 of {limit} calls remaining). "
                f"Retry after {int(seconds_until_reset)}s"
            )

        return True, None

    def wait_for_rate_limit_reset(self, endpoint: str) -> int:
        """
        Calculate wait time until rate limit resets.

        Args:
            endpoint: API endpoint

        Returns:
            Seconds to wait (0 if no rate limit or already reset)
        """
        if endpoint not in self._rate_limits:
            return 0

        limit_info = self._rate_limits[endpoint]
        reset_time = limit_info['reset_time']

        if datetime.utcnow() >= reset_time:
            # Already reset
            del self._rate_limits[endpoint]
            return 0

        seconds_until_reset = (reset_time - datetime.utcnow()).total_seconds()
        return max(0, int(seconds_until_reset))

    def get_rate_limit_status(self, endpoint: Optional[str] = None) -> Dict[str, any]:
        """
        Get current rate limit status.

        Args:
            endpoint: Specific endpoint to check (None for all endpoints)

        Returns:
            Dictionary with rate limit status
        """
        self._cleanup_expired_limits()

        if endpoint:
            if endpoint not in self._rate_limits:
                return {
                    'endpoint': endpoint,
                    'status': 'no_limit',
                    'remaining': None,
                    'limit': None,
                    'reset_in_seconds': 0
                }

            limit_info = self._rate_limits[endpoint]
            return {
                'endpoint': endpoint,
                'status': 'active',
                'remaining': limit_info['remaining'],
                'limit': limit_info['limit'],
                'usage_percent': round((limit_info['limit'] - limit_info['remaining']) / limit_info['limit'] * 100, 1),
                'reset_in_seconds': self.wait_for_rate_limit_reset(endpoint),
                'reset_time': limit_info['reset_time'].isoformat()
            }

        # Return status for all endpoints
        return {
            'endpoints': {
                ep: {
                    'remaining': info['remaining'],
                    'limit': info['limit'],
                    'usage_percent': round((info['limit'] - info['remaining']) / info['limit'] * 100, 1),
                    'reset_in_seconds': self.wait_for_rate_limit_reset(ep)
                }
                for ep, info in self._rate_limits.items()
            },
            'queue_size': len(self._queue)
        }

    def _cleanup_expired_limits(self):
        """Remove expired rate limit entries."""
        now = datetime.utcnow()

        # Only cleanup every 60 seconds to avoid overhead
        if (now - self._last_cleanup).total_seconds() < 60:
            return

        expired = [
            endpoint for endpoint, info in self._rate_limits.items()
            if now >= info['reset_time']
        ]

        for endpoint in expired:
            del self._rate_limits[endpoint]

        self._last_cleanup = now

    def add_to_queue(self, endpoint: str, retry_count: int = 0):
        """
        Add request to queue for later retry.

        Args:
            endpoint: API endpoint
            retry_count: Number of retries so far
        """
        self._queue.append({
            'endpoint': endpoint,
            'timestamp': datetime.utcnow(),
            'retry_count': retry_count
        })

    def get_queued_requests(self) -> list:
        """
        Get all queued requests.

        Returns:
            List of queued request dictionaries
        """
        return list(self._queue)

    def clear_queue(self):
        """Clear all queued requests."""
        self._queue.clear()
