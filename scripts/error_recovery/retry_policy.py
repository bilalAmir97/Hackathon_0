"""
RetryPolicy - Exponential backoff retry configuration

Provides retry logic with exponential backoff, jitter, and transient error detection.
"""

import random


class RetryPolicy:
    """
    Configuration and logic for retry behavior with exponential backoff.

    Implements exponential backoff with optional jitter to prevent thundering herd.
    Distinguishes between transient errors (retryable) and permanent errors (not retryable).
    """

    def __init__(self, base_delay=1.0, max_attempts=5, max_delay=60.0,
                 backoff_multiplier=2.0, jitter_enabled=True, jitter_max=1.0):
        """
        Initialize RetryPolicy with configuration.

        Args:
            base_delay: Base delay in seconds for first retry (default: 1.0)
            max_attempts: Maximum number of retry attempts (default: 5)
            max_delay: Maximum delay cap in seconds (default: 60.0)
            backoff_multiplier: Exponential backoff multiplier (default: 2.0)
            jitter_enabled: Whether to add random jitter (default: True)
            jitter_max: Maximum jitter in seconds (default: 1.0)

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if base_delay <= 0:
            raise ValueError("base_delay must be > 0")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if backoff_multiplier < 1.0:
            raise ValueError("backoff_multiplier must be >= 1.0")
        if jitter_max < 0:
            raise ValueError("jitter_max must be >= 0")

        self.base_delay = base_delay
        self.max_attempts = max_attempts
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter_enabled = jitter_enabled
        self.jitter_max = jitter_max

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number using exponential backoff.

        Formula: delay = min(base_delay * (backoff_multiplier ^ attempt), max_delay)
        If jitter enabled: delay += random(0, jitter_max)

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = self.base_delay * (self.backoff_multiplier ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter_enabled:
            delay += random.uniform(0, self.jitter_max)

        return delay

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """
        Determine if retry should be attempted.

        Args:
            attempt: Current attempt number (0-indexed)
            error: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        # Check if we've exceeded max attempts
        if attempt >= self.max_attempts:
            return False

        # Check if error is transient (retryable)
        return self.is_transient_error(error)

    def is_transient_error(self, error: Exception) -> bool:
        """
        Check if error is transient (retryable).

        Transient errors include:
        - ConnectionError, TimeoutError, ConnectionResetError
        - OSError with network-related errno
        - BrokenPipeError

        Permanent errors include:
        - ValueError, TypeError, KeyError (logic errors)
        - Authentication failures

        Args:
            error: Exception to check

        Returns:
            True if error is transient, False if permanent
        """
        # Transient network errors
        transient_types = (
            ConnectionError,
            TimeoutError,
            ConnectionResetError,
            BrokenPipeError,
            OSError,  # Network-related OS errors
        )

        # Permanent logic errors
        permanent_types = (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            NotImplementedError,
        )

        # Check if error is permanent
        if isinstance(error, permanent_types):
            return False

        # Check if error is transient
        if isinstance(error, transient_types):
            return True

        # Default: treat unknown errors as non-retryable (safe default)
        return False
