"""Tests for RateLimiter.

Tests rate limiting functionality for:
- Rate limit header parsing
- Proactive throttling at threshold
- Queue management
- Exponential backoff
- Per-endpoint tracking
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

# Import the rate limiter module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.rate_limiter import RateLimiter


# Fixtures

@pytest.fixture
def rate_limiter():
    """Create RateLimiter instance with default settings."""
    return RateLimiter(threshold=0.8, cooldown_seconds=3600)


@pytest.fixture
def rate_limiter_low_threshold():
    """Create RateLimiter with low threshold for testing."""
    return RateLimiter(threshold=0.5, cooldown_seconds=60)


# Tests for User Story 5: Rate Limiting

@pytest.mark.unit
def test_rate_limit_header_parsing(rate_limiter):
    """
    T082: Test rate limit header parsing.

    Given: Response headers with X-App-Usage
    When: parse_rate_limit_headers is called
    Then: Returns parsed rate limit info with call_count, limit, remaining
    """
    # Arrange
    headers = {
        "X-App-Usage": '{"call_count":50,"total_cputime":25,"total_time":30}'
    }

    # Act
    rate_info = rate_limiter.parse_rate_limit_headers(headers)

    # Assert
    assert rate_info['call_count'] == 50
    assert rate_info['total_cputime'] == 25
    assert rate_info['total_time'] == 30
    assert rate_info['limit'] == 200  # Default estimate
    assert rate_info['remaining'] == 150  # 200 - 50


@pytest.mark.unit
def test_rate_limit_header_parsing_business_usage(rate_limiter):
    """
    Test rate limit header parsing with X-Business-Use-Case-Usage.

    Given: Response headers with X-Business-Use-Case-Usage
    When: parse_rate_limit_headers is called
    Then: Returns parsed rate limit info from business usage data
    """
    # Arrange
    headers = {
        "X-Business-Use-Case-Usage": '{"123456":{"call_count":75,"total_cputime":40}}'
    }

    # Act
    rate_info = rate_limiter.parse_rate_limit_headers(headers)

    # Assert
    assert rate_info['call_count'] == 75
    assert rate_info['total_cputime'] == 40
    assert rate_info['limit'] == 200
    assert rate_info['remaining'] == 125  # 200 - 75


@pytest.mark.unit
def test_proactive_throttling_at_80_percent(rate_limiter):
    """
    T083: Test proactive throttling at 80% capacity.

    Given: Rate limit at 80% usage (160/200 calls)
    When: check_rate_limit is called
    Then: Returns (False, reason) indicating throttling
    """
    # Arrange
    headers = {
        "X-App-Usage": '{"call_count":160,"total_cputime":80,"total_time":90}'
    }
    rate_limiter.update_rate_limit("test_endpoint", headers)

    # Act
    is_allowed, reason = rate_limiter.check_rate_limit("test_endpoint")

    # Assert
    assert is_allowed is False
    assert "threshold" in reason.lower() or "throttl" in reason.lower()
    assert "80" in reason or "160" in reason


@pytest.mark.unit
def test_rate_limit_below_threshold_allowed(rate_limiter):
    """
    Test that requests below threshold are allowed.

    Given: Rate limit at 50% usage (100/200 calls)
    When: check_rate_limit is called
    Then: Returns (True, None) allowing request
    """
    # Arrange
    headers = {
        "X-App-Usage": '{"call_count":100,"total_cputime":50,"total_time":60}'
    }
    rate_limiter.update_rate_limit("test_endpoint", headers)

    # Act
    is_allowed, reason = rate_limiter.check_rate_limit("test_endpoint")

    # Assert
    assert is_allowed is True
    assert reason is None


@pytest.mark.unit
def test_rate_limit_queue_management(rate_limiter):
    """
    T084: Test rate limit queue management.

    Given: Rate limiter instance
    When: Requests are added to queue
    Then: Queue tracks requests with endpoint and retry count
    """
    # Act
    rate_limiter.add_to_queue("facebook_post", retry_count=0)
    rate_limiter.add_to_queue("instagram_post", retry_count=1)
    rate_limiter.add_to_queue("facebook_post", retry_count=2)

    queued = rate_limiter.get_queued_requests()

    # Assert
    assert len(queued) == 3
    assert queued[0]['endpoint'] == "facebook_post"
    assert queued[0]['retry_count'] == 0
    assert queued[1]['endpoint'] == "instagram_post"
    assert queued[1]['retry_count'] == 1
    assert queued[2]['retry_count'] == 2


@pytest.mark.unit
def test_rate_limit_exponential_backoff(rate_limiter):
    """
    T085: Test exponential backoff calculation.

    Given: Rate limit exceeded
    When: wait_for_rate_limit_reset is called
    Then: Returns appropriate wait time based on reset time
    """
    # Arrange
    headers = {
        "X-App-Usage": '{"call_count":200,"total_cputime":100,"total_time":120}'
    }
    rate_limiter.update_rate_limit("test_endpoint", headers)

    # Act
    wait_time = rate_limiter.wait_for_rate_limit_reset("test_endpoint")

    # Assert
    assert wait_time > 0
    assert wait_time <= 3600  # Should be within cooldown period


@pytest.mark.unit
def test_rate_limit_per_endpoint_tracking(rate_limiter):
    """
    T086: Test per-endpoint rate limit tracking.

    Given: Multiple endpoints with different rate limits
    When: check_rate_limit is called for each endpoint
    Then: Each endpoint is tracked independently
    """
    # Arrange
    headers_fb = {
        "X-App-Usage": '{"call_count":160,"total_cputime":80,"total_time":90}'
    }
    headers_ig = {
        "X-App-Usage": '{"call_count":50,"total_cputime":25,"total_time":30}'
    }

    rate_limiter.update_rate_limit("facebook_post", headers_fb)
    rate_limiter.update_rate_limit("instagram_post", headers_ig)

    # Act
    fb_allowed, fb_reason = rate_limiter.check_rate_limit("facebook_post")
    ig_allowed, ig_reason = rate_limiter.check_rate_limit("instagram_post")

    # Assert
    assert fb_allowed is False  # 160/200 = 80% (at threshold)
    assert ig_allowed is True   # 50/200 = 25% (below threshold)


@pytest.mark.unit
def test_rate_limit_status_reporting(rate_limiter):
    """
    Test rate limit status reporting.

    Given: Rate limits for multiple endpoints
    When: get_rate_limit_status is called
    Then: Returns status for all endpoints
    """
    # Arrange
    headers = {
        "X-App-Usage": '{"call_count":100,"total_cputime":50,"total_time":60}'
    }
    rate_limiter.update_rate_limit("test_endpoint", headers)

    # Act
    status = rate_limiter.get_rate_limit_status()

    # Assert
    assert "endpoints" in status
    assert "test_endpoint" in status["endpoints"]
    assert status["endpoints"]["test_endpoint"]["remaining"] == 100
    assert status["endpoints"]["test_endpoint"]["limit"] == 200
    assert status["endpoints"]["test_endpoint"]["usage_percent"] == 50.0


@pytest.mark.unit
def test_rate_limit_reset_clears_limit(rate_limiter):
    """
    Test that expired rate limits are cleared.

    Given: Rate limit with past reset time
    When: check_rate_limit is called
    Then: Rate limit is cleared and request is allowed
    """
    # Arrange
    headers = {
        "X-App-Usage": '{"call_count":200,"total_cputime":100,"total_time":120}'
    }
    rate_limiter.update_rate_limit("test_endpoint", headers)

    # Manually set reset time to past
    rate_limiter._rate_limits["test_endpoint"]["reset_time"] = datetime.utcnow() - timedelta(seconds=10)

    # Act
    is_allowed, reason = rate_limiter.check_rate_limit("test_endpoint")

    # Assert
    assert is_allowed is True
    assert reason is None
    assert "test_endpoint" not in rate_limiter._rate_limits


@pytest.mark.unit
def test_rate_limit_queue_clear(rate_limiter):
    """
    Test clearing the request queue.

    Given: Queue with multiple requests
    When: clear_queue is called
    Then: Queue is empty
    """
    # Arrange
    rate_limiter.add_to_queue("endpoint1", 0)
    rate_limiter.add_to_queue("endpoint2", 1)
    assert len(rate_limiter.get_queued_requests()) == 2

    # Act
    rate_limiter.clear_queue()

    # Assert
    assert len(rate_limiter.get_queued_requests()) == 0


@pytest.mark.unit
def test_rate_limit_no_headers(rate_limiter):
    """
    Test rate limit parsing with no headers.

    Given: Empty headers
    When: parse_rate_limit_headers is called
    Then: Returns default values
    """
    # Act
    rate_info = rate_limiter.parse_rate_limit_headers({})

    # Assert
    assert rate_info['call_count'] == 0
    assert rate_info['limit'] == 100  # Default when no headers
    assert rate_info['remaining'] == 100
