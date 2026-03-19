"""
Twitter Rate Limiter

Implements proactive rate limiting for Twitter API v2 with:
- 80% capacity threshold (configurable)
- Rate limit tracking from response headers
- Per-endpoint rate limit management
- Cooldown period handling
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class RateLimitInfo:
    """Rate limit information for an endpoint."""
    limit: int  # Total requests allowed in window
    remaining: int  # Requests remaining in current window
    reset_timestamp: int  # Unix timestamp when limit resets
    last_updated: datetime  # When this info was last updated


class TwitterRateLimiter:
    """
    Proactive rate limiter for Twitter API v2.

    Tracks rate limits per endpoint and enforces proactive throttling
    at a configurable threshold (default 80% capacity).
    """

    def __init__(self, threshold: float = 0.8):
        """
        Initialize rate limiter.

        Args:
            threshold: Proactive throttling threshold (0.0-1.0)
                      Default 0.8 = throttle at 80% capacity
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")

        self.threshold = threshold
        self.limits: Dict[str, RateLimitInfo] = {}

        # Load threshold from environment if available
        env_threshold = os.getenv('TWITTER_RATE_LIMIT_THRESHOLD')
        if env_threshold:
            self.threshold = float(env_threshold)

    def check_limit(self, endpoint: str) -> None:
        """
        Check if endpoint is approaching rate limit.

        Args:
            endpoint: API endpoint name (e.g., 'tweets', 'mentions')

        Raises:
            RateLimitException: If endpoint is at or above threshold
        """
        if endpoint not in self.limits:
            # No rate limit info yet, allow request
            return

        limit_info = self.limits[endpoint]

        # Check if limit has reset
        if time.time() >= limit_info.reset_timestamp:
            # Limit has reset, remove old info
            del self.limits[endpoint]
            return

        # Calculate usage percentage
        usage = (limit_info.limit - limit_info.remaining) / limit_info.limit

        if usage >= self.threshold:
            # At or above threshold
            reset_time = datetime.fromtimestamp(limit_info.reset_timestamp)
            wait_seconds = (reset_time - datetime.now()).total_seconds()

            raise RateLimitException(
                f"Rate limit threshold ({self.threshold*100}%) reached for {endpoint}. "
                f"{limit_info.remaining}/{limit_info.limit} requests remaining. "
                f"Resets in {int(wait_seconds)} seconds at {reset_time.isoformat()}"
            )

    def update_from_headers(self, endpoint: str, headers: Dict[str, str]) -> None:
        """
        Update rate limit info from Twitter API response headers.

        Twitter API v2 returns rate limit info in headers:
        - x-rate-limit-limit: Total requests allowed
        - x-rate-limit-remaining: Requests remaining
        - x-rate-limit-reset: Unix timestamp when limit resets

        Args:
            endpoint: API endpoint name
            headers: Response headers from Twitter API
        """
        # Defensive check for headers type
        if not isinstance(headers, dict):
            # Headers might be a list or other type in some error cases
            return

        try:
            limit = int(headers.get('x-rate-limit-limit', 0))
            remaining = int(headers.get('x-rate-limit-remaining', 0))
            reset = int(headers.get('x-rate-limit-reset', 0))

            if limit > 0:  # Valid rate limit info
                self.limits[endpoint] = RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset_timestamp=reset,
                    last_updated=datetime.now()
                )
        except (ValueError, TypeError):
            # Invalid header values, skip update
            pass

    def get_status(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Get current rate limit status for an endpoint.

        Args:
            endpoint: API endpoint name

        Returns:
            Dict with limit info or None if no info available
        """
        if endpoint not in self.limits:
            return None

        limit_info = self.limits[endpoint]

        # Check if expired
        if time.time() >= limit_info.reset_timestamp:
            del self.limits[endpoint]
            return None

        reset_time = datetime.fromtimestamp(limit_info.reset_timestamp)
        usage = (limit_info.limit - limit_info.remaining) / limit_info.limit

        return {
            'endpoint': endpoint,
            'limit': limit_info.limit,
            'remaining': limit_info.remaining,
            'usage_percent': round(usage * 100, 1),
            'reset_at': reset_time.isoformat(),
            'seconds_until_reset': int((reset_time - datetime.now()).total_seconds())
        }

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get rate limit status for all tracked endpoints.

        Returns:
            Dict mapping endpoint names to their status info
        """
        status = {}
        for endpoint in list(self.limits.keys()):
            endpoint_status = self.get_status(endpoint)
            if endpoint_status:
                status[endpoint] = endpoint_status

        return status

    def reset_endpoint(self, endpoint: str) -> None:
        """
        Manually reset rate limit info for an endpoint.

        Useful for testing or when you know the limit has reset.

        Args:
            endpoint: API endpoint name
        """
        if endpoint in self.limits:
            del self.limits[endpoint]

    def reset_all(self) -> None:
        """Reset all rate limit info."""
        self.limits.clear()


class RateLimitException(Exception):
    """Raised when rate limit threshold is reached."""
    pass
