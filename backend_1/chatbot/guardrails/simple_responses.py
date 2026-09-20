"""
Deterministic, zero-cost handler for simple standalone messages.

This module handles:
- Greetings
- Thanks
- Goodbyes
- Basic conversation
- Basic assistant identity questions

It intentionally does NOT answer substantive medical questions.
Those questions continue through the health guardrail pipeline.
"""

import re
from typing import Optional


_PUNCT_RE = re.compile(r"[!?.,:;\"'()\[\]{}~*_-]+")
_WHITESPACE_RE = re.compile(r"\s+")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")


def normalize(text: str) -> str:
    """
    Normalize a short standalone message for exact matching.
    """

    if not text:
        return ""

    normalized = text.strip().lower()

    normalized = _PUNCT_RE.sub(" ", normalized)

    normalized = _REPEATED_CHAR_RE.sub(
        r"\1",
        normalized,
    )

    normalized = _WHITESPACE_RE.sub(
        " ",
        normalized,
    ).strip()

    return normalized


# ----------------------------------------------------------------------
# Simple standalone responses
# ----------------------------------------------------------------------

SIMPLE_RESPONSES = {

    # --------------------------------------------------------------
    # Greetings
    # --------------------------------------------------------------

    "hi": "Hello! How can I help you with your health question today?",

    "hello": "Hello! How can I help you with your health question today?",

    "hey": "Hey! How can I help you with your health question today?",

    "hey there": (
        "Hey there! How can I help you with your health question today?"
    ),

    "good morning": (
        "Good morning! How can I help you with your health question today?"
    ),

    "good afternoon": (
        "Good afternoon! How can I help you with your health question today?"
    ),

    "good evening": (
        "Good evening! How can I help you with your health question today?"
    ),

    # --------------------------------------------------------------
    # Thanks
    # --------------------------------------------------------------

    "thanks": "You're welcome!",

    "thank you": "You're welcome!",

    "thx": "You're welcome!",

    "thanks a lot": "You're very welcome!",

    "thank you so much": "You're very welcome!",

    # --------------------------------------------------------------
    # Goodbye
    # --------------------------------------------------------------

    "bye": "Goodbye! Take care!",

    "goodbye": "Goodbye! Take care!",

    "see you": "See you soon! Take care!",

    "see you later": "See you later! Take care!",

    "talk to you later": "Talk to you later!",

    # --------------------------------------------------------------
    # Basic conversation
    # --------------------------------------------------------------

    "how are you": (
        "I'm doing well! How can I help you with your health question?"
    ),

    "how are you doing": (
        "I'm doing well! How can I help you with your health question?"
    ),

    "whats up": (
        "Not much! How can I help you with your health question today?"
    ),

    "what s up": (
        "Not much! How can I help you with your health question today?"
    ),

    "are you there": (
        "Yes, I'm here! How can I help you with your health question?"
    ),

    "okay": "Great!",

    "ok": "Great!",

    "cool": "Glad to hear it!",

    "nice": "Glad to hear it!",

    "thanks again": "You're welcome!",

    # --------------------------------------------------------------
    # What the assistant can do
    # --------------------------------------------------------------

    "what can you do": (
        "I can provide general health, medicine, symptom, "
        "medical report, pharmacy, and healthcare information."
    ),

    # --------------------------------------------------------------
    # Assistant identity
    #
    # Do not reveal the underlying model/vendor.
    # --------------------------------------------------------------

    "who are you": (
        "I'm your health-assistance AI, here to provide "
        "general health and healthcare information."
    ),

    "what are you": (
        "I'm your health-assistance AI, here to provide "
        "general health and healthcare information."
    ),

    "who made you": (
        "I'm a health-assistance AI designed to provide "
        "general health and healthcare information."
    ),

    "who created you": (
        "I'm a health-assistance AI designed to provide "
        "general health and healthcare information."
    ),

    "who built you": (
        "I'm a health-assistance AI designed to provide "
        "general health and healthcare information."
    ),

    "who developed you": (
        "I'm a health-assistance AI designed to provide "
        "general health and healthcare information."
    ),
}


# ----------------------------------------------------------------------
# Simple-message limits
# ----------------------------------------------------------------------

_MAX_SIMPLE_WORD_COUNT = 5


# These tokens indicate that a short message is probably a real
# question/request rather than a standalone conversational message.
#
# IMPORTANT:
# Medical questions such as:
#
#   "what is diabetes?"
#   "what is fever?"
#   "how does insulin work?"
#
# must NOT be answered here. They should continue through the
# health-assistance guardrail and main AI pipeline.
#
_DISQUALIFYING_TOKENS = {
    "?",
    "explain",
    "can",
    "could",
    "would",
    "please",
    "help",
    "what",
    "why",
    "how",
    "when",
    "where",
    "which",
    "who",
    "who's",
    "show",
    "tell",
    "give",
    "describe",
    "mean",
    "means",
    "cause",
    "causes",
    "symptom",
    "symptoms",
    "medicine",
    "medication",
    "drug",
    "dose",
    "dosage",
    "treatment",
    "disease",
    "condition",
    "diagnosis",
    "doctor",
    "pharmacy",
    "pharmacist",
    "report",
    "reports",
    "test",
    "tests",
    "result",
    "results",
    "prescription",
    "order",
    "orders",
    "book",
    "cancel",
    "reschedule",
    "price",
    "cost",
    "delivery",
    "account",
    "profile",
    "password",
    "and",
    "but",
}


def classify_simple_message(
    raw_text: str,
) -> Optional[str]:
    """
    Classify a message as a simple standalone conversational message.

    Returns:
        str:
            A deterministic response when the message is simple.

        None:
            The message should continue through the normal
            health-assistance guardrail pipeline.
    """

    normalized = normalize(raw_text)

    if not normalized:
        return None

    # --------------------------------------------------------------
    # Exact standalone match
    # --------------------------------------------------------------

    if normalized in SIMPLE_RESPONSES:
        return SIMPLE_RESPONSES[normalized]

    words = normalized.split()

    # --------------------------------------------------------------
    # Do not classify longer messages as simple conversation.
    # --------------------------------------------------------------

    if len(words) > _MAX_SIMPLE_WORD_COUNT:
        return None

    # --------------------------------------------------------------
    # Do not classify questions or substantive requests as simple.
    # --------------------------------------------------------------

    if any(
        token in _DISQUALIFYING_TOKENS
        for token in words
    ):
        return None

    # --------------------------------------------------------------
    # Preserve question protection.
    #
    # Anything ending in a question mark that wasn't explicitly
    # defined in SIMPLE_RESPONSES should continue to the main
    # health/security pipeline.
    # --------------------------------------------------------------

    if "?" in raw_text and normalized not in SIMPLE_RESPONSES:
        return None

    # --------------------------------------------------------------
    # Handle harmless filler after greetings.
    #
    # Examples:
    #
    #   "hello there"
    #   "hi guys"
    #   "hey everyone"
    #
    # These can still receive the deterministic greeting.
    # --------------------------------------------------------------

    trimmed = normalized

    for filler in (
        " there",
        " everyone",
        " guys",
        " friend",
    ):
        if trimmed.endswith(filler):
            trimmed = trimmed[
                :-len(filler)
            ].strip()

    if trimmed in SIMPLE_RESPONSES:
        return SIMPLE_RESPONSES[trimmed]

    return None