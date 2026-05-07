"""
API Utilities for caching, rate limiting, and quota management.
Reduces API calls and prevents quota exhaustion.
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Callable
import random


class ResponseCache:
    """Simple file-based cache for API responses to avoid duplicate calls."""

    def __init__(self, cache_dir: str = ".api_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, api_name: str, input_text: str) -> str:
        """Generate a cache key from API name and input."""
        hash_obj = hashlib.md5(input_text.encode())
        return f"{api_name}_{hash_obj.hexdigest()}.json"

    def get(self, api_name: str, input_text: str) -> Optional[str]:
        """Retrieve cached response if it exists."""
        cache_file = self.cache_dir / self._get_cache_key(api_name, input_text)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Check if cache is still valid (24 hour TTL)
                    if time.time() - data['timestamp'] < 86400:
                        print(f"[CACHE HIT] Using cached response for {api_name}")
                        return data['response']
                    else:
                        cache_file.unlink()  # Delete expired cache
            except Exception as e:
                print(f"[CACHE ERROR] Could not read cache: {e}")
        return None

    def set(self, api_name: str, input_text: str, response: str) -> None:
        """Store response in cache."""
        try:
            cache_file = self.cache_dir / self._get_cache_key(api_name, input_text)
            data = {
                'timestamp': time.time(),
                'response': response,
                'api': api_name
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[CACHE SAVED] Cached response for {api_name}")
        except Exception as e:
            print(f"[CACHE ERROR] Could not write cache: {e}")

    def clear(self) -> None:
        """Clear all cached responses."""
        for file in self.cache_dir.glob("*.json"):
            file.unlink()
        print("[CACHE] Cleared all cached responses")


class RateLimiter:
    """Rate limiter with exponential backoff to prevent quota exhaustion."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 30.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_call_time = {}
        self.failure_count = {}

    def wait(self, api_name: str) -> None:
        """Wait appropriate time before making API call."""
        if api_name in self.last_call_time:
            elapsed = time.time() - self.last_call_time[api_name]
            wait_time = self.min_delay - elapsed
            if wait_time > 0:
                print(f"[RATE LIMIT] Waiting {wait_time:.2f}s before next {api_name} call...")
                time.sleep(wait_time)

        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.5)
        time.sleep(jitter)
        self.last_call_time[api_name] = time.time()

    def handle_quota_error(self, api_name: str) -> float:
        """Handle quota error with exponential backoff."""
        failure_count = self.failure_count.get(api_name, 0) + 1
        self.failure_count[api_name] = failure_count

        # Exponential backoff: 1s, 2s, 4s, 8s, ... capped at max_delay
        backoff_delay = min(2 ** (failure_count - 1), self.max_delay)
        print(f"[QUOTA ERROR] {api_name} quota exceeded. Backoff attempt {failure_count}, waiting {backoff_delay}s...")
        return backoff_delay

    def reset_failure_count(self, api_name: str) -> None:
        """Reset failure count after successful call."""
        self.failure_count[api_name] = 0


def call_with_cache_and_limits(
    cache: ResponseCache,
    rate_limiter: RateLimiter,
    api_name: str,
    input_text: str,
    api_call_func: Callable,
    max_retries: int = 3
) -> Optional[str]:
    """
    Call an API with caching and rate limiting.

    Args:
        cache: ResponseCache instance
        rate_limiter: RateLimiter instance
        api_name: Name of the API (for logging)
        input_text: Input to the API (used for cache key)
        api_call_func: Function that calls the API and returns response
        max_retries: Maximum number of retries on failure

    Returns:
        API response or None if failed
    """

    # Check cache first
    cached_response = cache.get(api_name, input_text)
    if cached_response:
        return cached_response

    # Rate limit before call
    rate_limiter.wait(api_name)

    # Try API call with retries
    for attempt in range(max_retries):
        try:
            print(f"[API CALL] {api_name} (attempt {attempt + 1}/{max_retries})")
            response = api_call_func()

            if response:
                # Cache successful response
                cache.set(api_name, input_text, response)
                rate_limiter.reset_failure_count(api_name)
                print(f"[API SUCCESS] {api_name} call successful")
                return response
            else:
                # Response is empty/None from API
                print(f"[WARNING] {api_name} returned empty response on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        except Exception as e:
            error_str = str(e).lower()
            print(f"[API EXCEPTION] {api_name} error: {type(e).__name__}: {e}")

            # Check if it's a quota error (429)
            if '429' in error_str or 'quota' in error_str or 'resource_exhausted' in error_str:
                if attempt < max_retries - 1:
                    backoff_delay = rate_limiter.handle_quota_error(api_name)
                    time.sleep(backoff_delay)
                    continue
                else:
                    print(f"[ERROR] {api_name} quota exhausted after {max_retries} attempts")
                    return None

            # Check if it's a server overload error (503 UNAVAILABLE)
            elif '503' in error_str or 'unavailable' in error_str or 'high demand' in error_str:
                if attempt < max_retries - 1:
                    backoff_delay = min(5 * (2 ** attempt), 60)  # 5s, 10s, 20s, 40s, 60s
                    print(f"[SERVER OVERLOAD] {api_name} server overloaded. Waiting {backoff_delay}s before retry...")
                    time.sleep(backoff_delay)
                    continue
                else:
                    print(f"[ERROR] {api_name} server unavailable after {max_retries} attempts")
                    return None

            # Other errors (network, auth, etc)
            else:
                print(f"[RETRY] {api_name} failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Simple backoff for other errors
                    continue
                else:
                    return None

    print(f"[ERROR] {api_name} exhausted all retries")
    return None


# Global instances (singleton pattern)
_cache = None
_rate_limiter = None


def get_cache() -> ResponseCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = ResponseCache()
    return _cache


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(min_delay=2.0, max_delay=30.0)  # 2-30s delays
    return _rate_limiter
