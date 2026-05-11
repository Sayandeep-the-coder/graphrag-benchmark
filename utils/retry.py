"""
Exponential backoff retry wrapper for flaky API calls.
"""

import time


def with_retry(fn: callable, max_retries: int = 3, base_delay: float = 2.0):
    """
    Execute fn() with exponential backoff retries.

    Args:
        fn: Zero-argument callable to execute.
        max_retries: Maximum number of attempts before re-raising.
        base_delay: Base delay in seconds (doubles each retry).

    Returns:
        The return value of fn() on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"[retry {attempt + 1}/{max_retries}] {e} — waiting {delay}s")
            time.sleep(delay)
