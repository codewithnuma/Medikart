"""
Shared helpers: safe logging and secret-pattern definitions used
by both input and output security checks.
"""

import logging
import time
import uuid
from typing import Optional

logger = logging.getLogger("guardrails.security")


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def log_security_event(
    event: str,
    category: Optional[str] = None,
    risk: str = "LOW",
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    request_id: Optional[str] = None,
):
    """
    Structured security logging. Deliberately takes only
    non-sensitive fields - never pass tokens, keys, or raw
    message content into this function.
    """

    logger.info(
        "guardrail_event",
        extra={
            "event": event,
            "category": category,
            "risk": risk,
            "user_id": user_id,
            "endpoint": endpoint,
            "request_id": request_id,
            "timestamp": time.time(),
        },
    )