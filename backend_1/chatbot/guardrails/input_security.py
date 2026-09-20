"""
Input security: two layers, plus a deterministic general-knowledge
off-topic layer.

1. FAST PATH
   A small, deliberately narrow deny-list of unambiguous
   injection/jailbreak/secret-extraction phrases.

2. OUT-OF-SCOPE PATH
   Deterministic patterns that catch requests clearly outside
   the health-assistance AI's purpose, such as general coding,
   recipes, entertainment, and unrelated creative writing.

3. GENERAL-KNOWLEDGE PATH
   Detects clearly unrelated trivia and general-knowledge requests
   while allowing legitimate health and medical questions.

4. CONTEXTUAL PATH
   Anything not caught above is handed to NeMo Guardrails'
   self-check-input rail for contextual security classification.

IMPORTANT:
Normal medical questions must NOT be blocked.

Examples:

    "What is diabetes?"
    "What are the symptoms of flu?"
    "What is paracetamol used for?"
    "What are the side effects of ibuprofen?"
    "What does my blood test mean?"
    "What is hypertension?"
    "How does insulin work?"

These are valid health-assistance questions.
"""

import re
from typing import Optional, Tuple


# ============================================================
# FAST-PATH SECURITY PATTERNS
# ============================================================

_INJECTION_PATTERNS = [
    r"\bignore (all )?(the )?(previous|prior|above)\s+(instructions?|rules?|prompts?)\b",
    r"\bforget (your|all|the)\s+(rules?|instructions?|prompts?)\b",
    r"\bdisregard (your|all|the|previous)\s+(instructions?|rules?)\b",
    r"\bignore\s+everything\s+(above|before)\b",
]


_JAILBREAK_PATTERNS = [
    r"\byou are now (an? )?(unrestricted|uncensored|jailbroken|free)\b",
    r"\bdisable (all )?(safety|content)\s*(restrictions?|filters?|guardrails?)\b",
    r"\bpretend (you have|to have) no (rules|restrictions|limits)\b",
    r"\benter\s+developer\s+mode\b",
    r"\byou are dan\b",
    r"\bact as (an? )?(unrestricted|jailbroken|dan)\b",
    r"\bbypass (your|the) safety\b",
    r"\bdisable (your|the) safety\b",
]


_SYSTEM_EXTRACTION_PATTERNS = [
    r"\breveal (your|the)\s+(hidden|system|internal)\s+(instructions?|prompt|rules?)\b",
    r"\bshow (me )?(your|the)\s+system\s+prompt\b",
    r"\btell me your (developer|system|hidden)\s+instructions?\b",
    r"\bwhat (is|are) your (hidden|internal|system)\s+(instructions?|rules?|prompt)\b\s*(exactly|verbatim)?",
    r"\bprint (your|the)\s+system\s+prompt\b",
    r"\bshow me your hidden instructions\b",
    r"\breveal your developer prompt\b",
]


_HIERARCHY_ATTACK_PATTERNS = [
    r"\bsystem\s*message\s*:\s*ignore\b",
    r"\bdeveloper\s+says?\s+to\s+reveal\b",
    r"\bact as (the )?system\s+administrator\b",
    r"^\s*(system|developer|admin)\s*:\s*",
]


_SECRET_EXTRACTION_PATTERNS = [
    r"\b(give|show|tell) me (your|the)\s+api\s*key\b",
    r"\b(give|show|tell) me (your|the)\s+api\b",
    r"\benvironment\s+variables?\b.{0,20}\b(show|give|reveal|list)\b",
    r"\b(show|give|reveal) (me )?(the|your)\s+environment\s+variables?\b",
    r"\bjwt\s+secret\b",
    r"\b(secret|private)\s+key\b",
    r"\bdatabase\s+credentials?\b",
    r"\b(show|give|reveal) (me )?(the|your)\s+(database\s+)?(password|credentials)\b",
    r"\bshow me your credentials\b",
]


# ============================================================
# OUT-OF-SCOPE FAST PATH
# ============================================================
#
# These are clearly outside a health-assistance assistant.
#
# IMPORTANT:
# Health-related questions are intentionally NOT included here.
# ============================================================

_OUT_OF_SCOPE_PATTERNS = [

    # --------------------------------------------------------
    # Creative writing
    # --------------------------------------------------------

    r"\b(write|create|compose|generate)\s+(me\s+)?(a\s+)?(poem|poetry)\b",

    r"\b(write|create|compose|generate)\s+(me\s+)?(a\s+)?(song|lyrics)\b",

    r"\b(write|create|tell)\s+(me\s+)?(a\s+)?(story|fiction)\b",

    r"\b(write|create|generate)\s+(me\s+)?(a\s+)?joke\b",

    r"\b(write|create|generate)\s+(me\s+)?(a\s+)?rap\b",

    # --------------------------------------------------------
    # General coding / programming
    # --------------------------------------------------------

    r"\b(write|create|generate|debug|fix)\s+(me\s+)?(a\s+)?"
    r"(python|javascript|java|c\+\+|html|css)\s+"
    r"(code|program|script)\b",

    r"\bwrite\s+code\s+for\b",

    r"\bhow\s+do\s+i\s+code\b",

    r"\bhow\s+to\s+program\b",

    # --------------------------------------------------------
    # Homework / academic work
    # --------------------------------------------------------

    r"\bsolve\s+(my\s+)?(math|mathematics)\s+"
    r"(problem|question|equation)\b",

    r"\bdo\s+(my\s+)?homework\b",

    r"\bwrite\s+(my\s+)?essay\b",

    r"\bwrite\s+(my\s+)?assignment\b",

    # --------------------------------------------------------
    # Cooking / recipes
    # --------------------------------------------------------

    r"\bhow\s+do\s+i\s+cook\b",

    r"\bhow\s+to\s+make\s+(a\s+)?"
    r"(cake|pizza|pasta|curry|bread)\b",

    r"\b(recipe|recipes)\s+for\b",

    # --------------------------------------------------------
    # Entertainment
    # --------------------------------------------------------

    r"\bwrite\s+(me\s+)?(a\s+)?movie\s+script\b",

    r"\bmovie\s+recommendations?\b",

    r"\b(tv|television)\s+show\s+recommendations?\b",

    r"\b(song|music)\s+recommendations?\b",

    # --------------------------------------------------------
    # Sports
    # --------------------------------------------------------

    r"\b(football|cricket|basketball|soccer|baseball|tennis)"
    r"\s+(score|scores|news|match)\b",

    # --------------------------------------------------------
    # Travel
    # --------------------------------------------------------

    r"\bflight\s+booking\b",

    r"\bhotel\s+booking\b",

    r"\btravel\s+packages?\b",

    r"\bholiday\s+packages?\b",

    r"\btravel\s+itinerary\b",

    # --------------------------------------------------------
    # Generic unrelated knowledge
    # --------------------------------------------------------

    r"\bcapital of\b",

    r"\bprime minister of\b",

    r"\bpresident of\b",

    r"\bwho won the\b",

    r"\bhistory of\b",
]


# ============================================================
# GENERAL-KNOWLEDGE / TRIVIA
# ============================================================
#
# We only classify these as off-topic when they do NOT contain
# health/medical/application context.
#
# This prevents:
#
#   "What is diabetes?"
#   "Who discovered insulin?"
#   "What is the history of vaccines?"
#
# from being incorrectly rejected.
# ============================================================


_HEALTH_CONTEXT_WORDS = re.compile(
    r"\b("
    r"health|healthcare|medical|medicine|medicines|medication|"
    r"medications|drug|drugs|pharmacy|pharmacist|doctor|doctors|"
    r"nurse|hospital|clinic|patient|symptom|symptoms|disease|"
    r"condition|diagnosis|treatment|therapy|prescription|"
    r"side effect|side effects|dose|dosage|tablet|capsule|"
    r"syrup|injection|antibiotic|antibiotics|painkiller|"
    r"vitamin|vitamins|supplement|supplements|diabetes|"
    r"hypertension|blood pressure|blood sugar|glucose|"
    r"cholesterol|asthma|allergy|allergies|infection|"
    r"fever|cough|flu|cold|headache|migraine|"
    r"pain|nausea|vomiting|diarrhea|dizziness|"
    r"pregnancy|pregnant|vaccine|vaccination|immunization|"
    r"blood test|lab test|laboratory|medical report|"
    r"health report|test result|test results|"
    r"prescription|medicine order|pharmacy order|"
    r"patient account|health record|medical record"
    r")\b",
    re.IGNORECASE,
)


_APPLICATION_CONTEXT_WORDS = re.compile(
    r"\b("
    r"account|profile|login|log ?in|sign ?up|signup|"
    r"register|registration|password|order|orders|"
    r"delivery|report|reports|pharmacy|medicine|"
    r"prescription|patient"
    r")\b",
    re.IGNORECASE,
)


_GENERAL_KNOWLEDGE_PATTERNS = [

    # Who/what questions
    r"\bwho (is|was|are)\b",

    # Geography / politics
    r"\bwhat is the capital of\b",

    r"\b(prime minister|president|chief minister|ceo|founder)\s+of\b",

    # Sports
    r"\b(football|cricket|basketball|soccer|baseball|tennis)\b",

    r"\bwho won\b",

    # History
    r"\bhistory of\b",

    # Dates
    r"\bwhat year (was|did)\b",

    # Population
    r"\bhow many people (live|are) in\b",

    # Weather
    r"\bcurrent (weather|temperature)\b",
]


_COMPILED_GENERAL_KNOWLEDGE = [
    re.compile(
        pattern,
        re.IGNORECASE,
    )
    for pattern in _GENERAL_KNOWLEDGE_PATTERNS
]


def _matches_general_knowledge(
    message: str,
) -> bool:
    """
    Returns True only when the message looks like unrelated
    general knowledge and does not contain health/application
    context.
    """

    # Health-related questions are allowed.
    if _HEALTH_CONTEXT_WORDS.search(message):
        return False

    # Application/account questions are allowed.
    if _APPLICATION_CONTEXT_WORDS.search(message):
        return False

    return any(
        pattern.search(message)
        for pattern in _COMPILED_GENERAL_KNOWLEDGE
    )


# ============================================================
# FAST PATH CATEGORIES
# ============================================================

_FAST_PATH_CATEGORIES = (

    (
        "prompt_injection",
        _INJECTION_PATTERNS,
    ),

    (
        "jailbreak",
        _JAILBREAK_PATTERNS,
    ),

    (
        "system_prompt_extraction",
        _SYSTEM_EXTRACTION_PATTERNS,
    ),

    (
        "prompt_injection",
        _HIERARCHY_ATTACK_PATTERNS,
    ),

    (
        "secret_extraction",
        _SECRET_EXTRACTION_PATTERNS,
    ),

    (
        "off_topic",
        _OUT_OF_SCOPE_PATTERNS,
    ),
)


_COMPILED = [
    (
        category,
        [
            re.compile(
                pattern,
                re.IGNORECASE,
            )
            for pattern in patterns
        ],
    )
    for category, patterns in _FAST_PATH_CATEGORIES
]


# ============================================================
# FAST PATH CHECK
# ============================================================

def fast_path_check(
    message: str,
) -> Optional[Tuple[str, str]]:
    """
    Returns:

        (category, matched_pattern)

    when the message matches a known security attack or a
    clearly unrelated request.

    Returns None when the message should continue to the
    contextual NeMo Guardrails check.
    """

    # --------------------------------------------------------
    # Security / injection patterns
    # --------------------------------------------------------

    for category, patterns in _COMPILED:

        for pattern in patterns:

            if pattern.search(message):

                return (
                    category,
                    pattern.pattern,
                )

    # --------------------------------------------------------
    # General knowledge / unrelated trivia
    # --------------------------------------------------------

    if _matches_general_knowledge(message):

        return (
            "off_topic",
            "general_knowledge_trivia",
        )

    return None


# ============================================================
# WORDS THAT MUST NEVER TRIGGER A BLOCK ON THEIR OWN
# ============================================================
#
# These are documented safe examples.
#
# They must be allowed because they are legitimate health,
# medical, or AI-security educational questions.
# ============================================================

SAFE_EDUCATIONAL_EXAMPLES = [

    # --------------------------------------------------------
    # AI / security education
    # --------------------------------------------------------

    "What is a system prompt?",

    "How does prompt injection work?",

    "What are AI guardrails?",

    "Why do developers use rules for chatbots?",

    "What is an API key?",

    "Why should passwords be protected?",

    # --------------------------------------------------------
    # General health
    # --------------------------------------------------------

    "What is diabetes?",

    "What is hypertension?",

    "What causes a headache?",

    "What are the symptoms of flu?",

    "What is an allergic reaction?",

    "What is high blood pressure?",

    # --------------------------------------------------------
    # Medicine
    # --------------------------------------------------------

    "What is paracetamol used for?",

    "What are the side effects of ibuprofen?",

    "How do antibiotics work?",

    "What is the difference between antibiotics and antivirals?",

    "How should medicine be stored?",

    # --------------------------------------------------------
    # Medical reports
    # --------------------------------------------------------

    "What does a blood test measure?",

    "What is a CBC blood test?",

    "What does blood sugar mean?",

    "What is a medical report?",

    "Can you explain my test results?",

    # --------------------------------------------------------
    # Pharmacy
    # --------------------------------------------------------

    "Is this medicine available at the pharmacy?",

    "How can I order my medicine?",

    "Where can I see my medicine orders?",

    "How can I view my health reports?",
]