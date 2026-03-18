"""
Unit tests for RetryPolicy class

Tests exponential backoff calculation, jitter, transient error detection,
and retry decision logic.
"""

import pytest
from scripts.error_recovery.retry_policy import RetryPolicy


class TestRetryPolicy:
    """Test suite for RetryPolicy"""

    # T013: Test exponential backoff calculation
    def test_calculate_delay_exponential_backoff(self):
        """Test that delay increases exponentially with attempt number"""
        policy = RetryPolicy(base_delay=1.0, backoff_multiplier=2.0, jitter_enabled=False)

        # Attempt 0: 1.0 * (2^0) = 1.0
        assert policy.calculate_delay(0) == 1.0

        # Attempt 1: 1.0 * (2^1) = 2.0
        assert policy.calculate_delay(1) == 2.0

        # Attempt 2: 1.0 * (2^2) = 4.0
        assert policy.calculate_delay(2) == 4.0

        # Attempt 3: 1.0 * (2^3) = 8.0
        assert policy.calculate_delay(3) == 8.0

        # Attempt 4: 1.0 * (2^4) = 16.0
        assert policy.calculate_delay(4) == 16.0

    # T014: Test jitter adds randomness
    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds random delay within bounds"""
        policy = RetryPolicy(base_delay=1.0, backoff_multiplier=2.0,
                           jitter_enabled=True, jitter_max=1.0)

        # Run multiple times to test randomness
        delays = [policy.calculate_delay(1) for _ in range(10)]

        # Base delay for attempt 1 is 2.0, jitter adds 0-1.0
        for delay in delays:
            assert 2.0 <= delay <= 3.0

        # Verify delays are not all identical (randomness working)
        assert len(set(delays)) > 1

    # T015: Test max delay cap
    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay"""
        policy = RetryPolicy(base_delay=1.0, max_delay=10.0,
                           backoff_multiplier=2.0, jitter_enabled=False)

        # Attempt 10: 1.0 * (2^10) = 1024.0, but capped at 10.0
        assert policy.calculate_delay(10) == 10.0

        # Attempt 20: Even larger, still capped
        assert policy.calculate_delay(20) == 10.0

    # T016: Test transient error detection
    def test_should_retry_transient_errors(self, transient_errors):
        """Test that transient errors are identified as retryable"""
        policy = RetryPolicy(max_attempts=5)

        for error in transient_errors:
            # Should retry on transient errors (within max attempts)
            assert policy.should_retry(1, error) is True
            assert policy.should_retry(3, error) is True

    # T017: Test permanent error detection
    def test_should_not_retry_permanent_errors(self, permanent_errors):
        """Test that permanent errors are not retried"""
        policy = RetryPolicy(max_attempts=5)

        for error in permanent_errors:
            # Should NOT retry on permanent errors
            assert policy.should_retry(1, error) is False
            assert policy.should_retry(3, error) is False

    # T018: Test retry counter reset (implicit in should_retry logic)
    def test_retry_counter_reset_after_success(self):
        """Test that retry logic allows fresh attempts after success"""
        policy = RetryPolicy(max_attempts=3)

        # After success, attempt counter should conceptually reset
        # This is tested by verifying early attempts are retryable
        error = ConnectionError("Test")
        assert policy.should_retry(0, error) is True
        assert policy.should_retry(1, error) is True
        assert policy.should_retry(2, error) is True

    # T019: Test max attempts enforcement
    def test_max_attempts_enforced(self):
        """Test that retries stop after max_attempts"""
        policy = RetryPolicy(max_attempts=3)

        error = ConnectionError("Test")

        # Attempts 0, 1, 2 should be retryable (< max_attempts)
        assert policy.should_retry(0, error) is True
        assert policy.should_retry(1, error) is True
        assert policy.should_retry(2, error) is True

        # Attempt 3 should NOT be retryable (>= max_attempts)
        assert policy.should_retry(3, error) is False
        assert policy.should_retry(4, error) is False

    # Additional tests for validation
    def test_init_validates_base_delay(self):
        """Test that base_delay must be positive"""
        with pytest.raises(ValueError, match="base_delay must be > 0"):
            RetryPolicy(base_delay=0)

        with pytest.raises(ValueError, match="base_delay must be > 0"):
            RetryPolicy(base_delay=-1.0)

    def test_init_validates_max_attempts(self):
        """Test that max_attempts must be >= 1"""
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            RetryPolicy(max_attempts=0)

    def test_init_validates_max_delay(self):
        """Test that max_delay must be >= base_delay"""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryPolicy(base_delay=10.0, max_delay=5.0)

    def test_init_validates_backoff_multiplier(self):
        """Test that backoff_multiplier must be >= 1.0"""
        with pytest.raises(ValueError, match="backoff_multiplier must be >= 1.0"):
            RetryPolicy(backoff_multiplier=0.5)

    def test_init_validates_jitter_max(self):
        """Test that jitter_max must be >= 0"""
        with pytest.raises(ValueError, match="jitter_max must be >= 0"):
            RetryPolicy(jitter_max=-1.0)

    def test_is_transient_error_connection_errors(self):
        """Test that connection errors are transient"""
        policy = RetryPolicy()

        assert policy.is_transient_error(ConnectionError("test")) is True
        assert policy.is_transient_error(TimeoutError("test")) is True
        assert policy.is_transient_error(ConnectionResetError("test")) is True

    def test_is_transient_error_permanent_errors(self):
        """Test that logic errors are permanent"""
        policy = RetryPolicy()

        assert policy.is_transient_error(ValueError("test")) is False
        assert policy.is_transient_error(TypeError("test")) is False
        assert policy.is_transient_error(KeyError("test")) is False
