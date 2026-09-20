"""
Deterministic, zero-LLM handler for login / signup / forgot-password
questions. Checked BEFORE the attack-pattern fast path and BEFORE
NeMo, so these never reach the LLM or get misclassified.
"""

import re
from typing import Optional, Tuple

LOGIN_RESPONSE = (
    "To log in: go to the Login page, enter your email and password, "
    "then click Sign In."
)

SIGNUP_RESPONSE = (
    "To sign up: go to the Register page, enter your details, "
    "then click Register."
)

FORGOT_PASSWORD_RESPONSE = (
    "To reset your password: click Forgot Password, enter your email, "
    "use the OTP you receive, then set your new password."
)

_FORGOT_PASSWORD_PASS_RE = re.compile(r"\bpass\w{2,12}\b", re.IGNORECASE)
_FORGOT_PASSWORD_INTENT_RE = re.compile(
    r"\b(forgot|forget|forgotten|reset|change|recover|don'?t remember)\b",
    re.IGNORECASE,
)

_LOGIN_RE = re.compile(r"\blog ?in\b|\bsign ?in\b", re.IGNORECASE)
_SIGNUP_RE = re.compile(
    r"\bsign ?up\b|\bregister\b|\bcreate\s+(an\s+)?account\b",
    re.IGNORECASE,
)


def classify_account_help(message: str) -> Optional[Tuple[str, str]]:
    if not message:
        return None

    if _FORGOT_PASSWORD_PASS_RE.search(message) and _FORGOT_PASSWORD_INTENT_RE.search(message):
        return "forgot_password", FORGOT_PASSWORD_RESPONSE

    if _LOGIN_RE.search(message):
        return "login_help", LOGIN_RESPONSE

    if _SIGNUP_RE.search(message):
        return "signup_help", SIGNUP_RESPONSE

    return None