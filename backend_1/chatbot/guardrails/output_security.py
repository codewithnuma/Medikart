"""
Output security: deterministic secret detection/redaction.
"""

import re
from typing import Tuple


_SECRET_PATTERNS = [
    (re.compile(r'(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token)\b\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?'), "api_key"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "api_key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_key"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "jwt"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "private_key"),
    (re.compile(r'(?i)\b(password|pwd|passwd)\b\s*[:=]\s*["\']?\S{4,}["\']?'), "password"),
    (re.compile(r"\b\w+://[^:\s]+:[^@\s]+@[^\s/]+"), "connection_string"),
    (re.compile(r'(?i)\b(DATABASE_URL|DB_PASSWORD|SECRET_KEY|CLERK_SECRET_KEY|JWT_SECRET)\b\s*[:=]\s*\S+'), "env_secret"),
]

_REDACTION_TEXT = "[REDACTED]"


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern, _label in _SECRET_PATTERNS)


def redact_secrets(text: str) -> Tuple[str, bool]:
    redacted_any = False
    result = text

    for pattern, _label in _SECRET_PATTERNS:
        new_result, count = pattern.subn(_REDACTION_TEXT, result)
        if count:
            redacted_any = True
            result = new_result

    return result, redacted_any


class StreamingRedactor:

    _CARRY_OVER_CHARS = 120

    def __init__(self):
        self._buffer = ""
        self._in_possible_pem = False

    def feed(self, chunk: str) -> str:
        self._buffer += chunk

        if "-----BEGIN" in self._buffer and "-----END" not in self._buffer:
            self._in_possible_pem = True
            return ""

        if self._in_possible_pem and "-----END" not in self._buffer:
            return ""

        self._in_possible_pem = False

        if len(self._buffer) <= self._CARRY_OVER_CHARS:
            return ""

        safe_len = len(self._buffer) - self._CARRY_OVER_CHARS
        emit, self._buffer = self._buffer[:safe_len], self._buffer[safe_len:]

        redacted, _ = redact_secrets(emit)
        return redacted

    def flush(self) -> str:
        if not self._buffer:
            return ""

        redacted, _ = redact_secrets(self._buffer)
        self._buffer = ""
        return redacted