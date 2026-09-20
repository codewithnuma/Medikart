"""
Guardrail-specific exceptions.

Views catch these and translate them into the standard JSON error
shape (see docs). None of these should ever leak internal details -
that's the job of the view layer, not these classes.
"""


class GuardrailBlocked(Exception):
    """Raised when input or output is blocked by a guardrail check."""

    def __init__(self, category: str, message: str, risk: str = "MEDIUM"):
        self.category = category      # e.g. "prompt_injection", "jailbreak",
                                       # "secret_extraction", "off_topic",
                                       # "output_secret", "service_failure"
        self.message = message        # safe, user-facing refusal text
        self.risk = risk              # "LOW" | "MEDIUM" | "HIGH"
        super().__init__(message)


class RateLimitExceeded(Exception):
    """Raised when a caller exceeds the configured rate limit."""

    def __init__(self, retry_after_seconds: int = 60):
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Rate limit exceeded")


class InputTooLarge(Exception):
    """Raised when the user message exceeds MAX_INPUT_LENGTH."""

    def __init__(self, max_length: int):
        self.max_length = max_length
        super().__init__(f"Input exceeds maximum length of {max_length} characters")