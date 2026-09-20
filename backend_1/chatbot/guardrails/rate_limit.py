"""
Server-side rate limiting, backed by Django's cache framework
(works with whatever CACHES backend is already configured -
locmem by default, Redis/Memcached in production).

Fixed-window counters per minute and per hour. Simple, and good
enough for a chatbot endpoint; swap for a sliding-window/token-
bucket implementation later if needed without changing callers.
"""

import time

from django.core.cache import cache

from . import config
from .exceptions import RateLimitExceeded


def _window_key(identifier: str, window: str, window_start: int) -> str:
    return f"guardrails:ratelimit:{window}:{identifier}:{window_start}"


def check_rate_limit(identifier: str, authenticated: bool) -> None:
    """
    Raises RateLimitExceeded if `identifier` (Clerk user_id, or
    client IP for guests) has exceeded the configured limits.
    Otherwise increments the counters and returns None.
    """

    if authenticated:
        per_minute_limit = config.RATE_LIMIT_PER_MINUTE
        per_hour_limit = config.RATE_LIMIT_PER_HOUR
    else:
        per_minute_limit = config.GUEST_RATE_LIMIT_PER_MINUTE
        per_hour_limit = config.GUEST_RATE_LIMIT_PER_HOUR

    now = int(time.time())

    minute_start = now - (now % 60)
    hour_start = now - (now % 3600)

    minute_key = _window_key(identifier, "minute", minute_start)
    hour_key = _window_key(identifier, "hour", hour_start)

    minute_count = cache.get(minute_key, 0)
    hour_count = cache.get(hour_key, 0)

    if minute_count >= per_minute_limit:
        raise RateLimitExceeded(retry_after_seconds=60 - (now % 60))

    if hour_count >= per_hour_limit:
        raise RateLimitExceeded(retry_after_seconds=3600 - (now % 3600))

    # Increment (best-effort; cache.add + incr avoids races well
    # enough for this use case without needing atomic Lua scripts).
    if cache.add(minute_key, 0, timeout=65):
        pass
    cache.incr(minute_key, 1)

    if cache.add(hour_key, 0, timeout=3665):
        pass
    cache.incr(hour_key, 1)