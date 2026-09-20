# ============================================================
# cache_utils.py
#
# Reusable, DB-backed answer caching for the `general`, `rag`
# (handbook), and `web_search` routes only.
#
#   general     -> shared cache key = normalized question (no user_id)
#   rag         -> shared cache key = normalized question + current
#                   knowledge-base version (no user_id)
#   web_search  -> shared cache key = normalized question (no user_id)
#                   (short TTL, since web results go stale faster
#                   than the handbook or general health knowledge)
#   ai_agent -> NEVER cached here (may perform actions / depend on
#                current state) — nothing in this module is wired
#                into health_agent.py.
#   direct_tool / user_information -> NEVER put into this shared
#                cache. If a caller ever needs to cache user-specific
#                data, use get_user_info_cache_key() below, which
#                forces the user's id into the key so it can never
#                be served to a different user.
#
# Uses Django's configured `default` cache (DatabaseCache — see
# settings.py). No Redis, no new infrastructure.
# ============================================================

import hashlib
import time

from django.conf import settings
from django.core.cache import cache


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_question(question) -> str:
    """
    Collapse whitespace and case so trivial differences
    ("What's my Name?  " vs "what's my name?") don't create
    separate cache entries for what is really the same question.
    """

    if not question:
        return ""

    return " ".join(str(question).strip().lower().split())


def _hash(text: str) -> str:
    """
    Short, fixed-length, non-reversible fingerprint of normalized
    question text. Keeps cache keys short and avoids ever putting
    raw user text directly into a cache key/log line.
    """

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


# ============================================================
# CACHE KEYS
# ============================================================

def get_general_cache_key(question) -> str:
    """
    general:<hash of normalized question>

    Deliberately contains NO user_id — a general answer ("how do I
    login", "who won the world cup") is safe to share between every
    user who asks the same normalized question.
    """

    normalized = normalize_question(question)

    return f"general:{_hash(normalized)}"


def get_rag_cache_key(question, knowledge_version: str) -> str:
    """
    rag:<knowledge_version>:<hash of normalized question>

    Contains NO user_id (RAG answers are drawn from the shared
    company handbook, not from anything user-specific) but DOES
    contain the current knowledge-base version, so a stale answer
    from an old document version can never be served once the
    handbook changes. See get_knowledge_version() below.
    """

    normalized = normalize_question(question)

    return f"rag:{knowledge_version}:{_hash(normalized)}"


def get_websearch_cache_key(question) -> str:
    """
    websearch:<hash of normalized question>

    Contains NO user_id — a web-search answer is drawn from public
    sources (Tavily + the allow-listed health domains), not from
    anything user-specific, so it's safe to share between every
    user who asks the same normalized question.

    Unlike RAG, there's no local "knowledge version" to key off of
    (the source is the live web), so freshness is handled purely
    through a short TTL — see get_websearch_cache_ttl() below —
    rather than a version fingerprint.
    """

    normalized = normalize_question(question)

    return f"websearch:{_hash(normalized)}"


def get_user_info_cache_key(user_id, information_key: str) -> str:
    """
    user:<user_id>:<information_key>

    For USER_INFORMATION data only. The user_id is mandatory and is
    always the leading path segment, so one user's cached data can
    never collide with — or be served to — another user, even if
    they asked the exact same question.

    Not currently called by direct_tool.py (there is nothing there
    worth caching yet), but provided so any future user-specific
    caching in that route starts from a key shape that can't leak
    across users.
    """

    if user_id is None or str(user_id).strip() == "":
        raise ValueError(
            "get_user_info_cache_key() requires a non-empty user_id "
            "— refusing to build a user-information cache key "
            "without one, since that could let one user's cached "
            "answer be served to another."
        )

    return f"user:{user_id}:{information_key}"


# ============================================================
# GET / SET
# ============================================================

def get_cached_answer(key: str):
    """
    Returns the cached answer string, or None on a cache miss
    (including an expired entry — Django's cache backends already
    treat expiry as a miss, so nothing extra is needed here).
    """

    try:

        return cache.get(key)

    except Exception as exc:

        # A cache backend hiccup should degrade to "treat as a
        # miss", never break the request.
        print("CACHE ERROR (get):", type(exc).__name__, exc)

        return None


def set_cached_answer(key: str, answer, timeout: int) -> bool:
    """
    Stores `answer` under `key` for `timeout` seconds. Refuses to
    cache an empty/falsy answer, so a failed LLM/RAG/web-search call
    never poisons the cache with an invalid response that would then
    be served to everyone else asking the same question.

    Returns True if something was actually written, False if the
    write was skipped or failed.
    """

    if answer is None:
        return False

    if isinstance(answer, str) and not answer.strip():
        return False

    try:

        cache.set(key, answer, timeout=timeout)
        return True

    except Exception as exc:

        print("CACHE ERROR (set):", type(exc).__name__, exc)
        return False


# ============================================================
# KNOWLEDGE-BASE VERSION (for the RAG cache key)
# ============================================================
#
# There is no existing document/version metadata system in this
# project (C_rag.py has no version field) — but it DOES already
# have a single, canonical "is the knowledge base up to date"
# signal: the FAISS index directory (FAISS_DIR). C_rag.py's own
# get_vectorstore() already treats "does FAISS_DIR exist" as the
# switch between "reuse what's there" and "rebuild from the PDF".
#
# So instead of inventing a separate versioning system, this
# derives a cache-friendly fingerprint FROM that same directory:
# file count + newest modification time, hashed down to something
# short. Rebuilding the index (delete faiss_index_fast/ and let it
# rebuild, or swap in a new one) changes the directory's contents/
# mtimes, which changes this fingerprint, which automatically
# invalidates every RAG cache entry tied to the old version — no
# manual "bump the version" step required anywhere.
# ============================================================

_KNOWLEDGE_VERSION_CACHE = {
    "version": None,
    "checked_at": 0.0,


}

# How often we're willing to re-stat the FAISS directory. This can
# be called on every single RAG request, so re-walking the
# directory tree every time would add needless disk I/O; a short
# recheck window keeps it cheap while still picking up a rebuilt
# index within a bounded amount of time.
KNOWLEDGE_VERSION_RECHECK_SECONDS = 60


def _compute_knowledge_version() -> str:

    # Local import: keeps this module importable even in contexts
    # that don't need the (heavy) C_rag import path, and avoids any
    # import-order issues with chatbot.py, which imports both.
    from .C_rag import FAISS_DIR

    if not FAISS_DIR.exists():
        return "no-index"

    newest_mtime = 0.0
    file_count = 0

    for path in FAISS_DIR.rglob("*"):

        if not path.is_file():
            continue

        file_count += 1

        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue

        if mtime > newest_mtime:
            newest_mtime = mtime

    raw = f"{file_count}:{newest_mtime:.3f}"

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def get_knowledge_version() -> str:
    """
    Returns the current RAG knowledge-base version fingerprint,
    recomputing it at most once every
    KNOWLEDGE_VERSION_RECHECK_SECONDS.
    """

    now = time.time()

    cached_version = _KNOWLEDGE_VERSION_CACHE["version"]
    checked_at = _KNOWLEDGE_VERSION_CACHE["checked_at"]

    if (
        cached_version is not None
        and (now - checked_at) < KNOWLEDGE_VERSION_RECHECK_SECONDS
    ):
        return cached_version

    version = _compute_knowledge_version()

    _KNOWLEDGE_VERSION_CACHE["version"] = version
    _KNOWLEDGE_VERSION_CACHE["checked_at"] = now

    return version


def invalidate_knowledge_version_cache() -> None:
    """
    Forces the next get_knowledge_version() call to recompute
    immediately instead of waiting out the recheck window. Mainly
    useful for tests, or right after a manual reindex.
    """

    _KNOWLEDGE_VERSION_CACHE["version"] = None
    _KNOWLEDGE_VERSION_CACHE["checked_at"] = 0.0


# ============================================================
# TTL HELPERS
# ============================================================
#
# TTLs are configurable through Django settings (see settings.py)
# rather than hardcoded at every call site. These small wrappers
# are the ONE place that reads the setting, with a sane default if
# it's ever missing.
# ============================================================

def get_general_cache_ttl() -> int:

    return getattr(
        settings,
        "GENERAL_ANSWER_CACHE_TTL",
        60 * 60 * 24,  # 24 hours
    )


def get_rag_cache_ttl() -> int:

    return getattr(
        settings,
        "RAG_ANSWER_CACHE_TTL",
        60 * 60 * 3,  # 3 hours
    )


def get_websearch_cache_ttl() -> int:
    """
    Kept deliberately shorter than general/RAG — web-search answers
    are drawn from live public sources (news, guidance pages, etc.)
    that can change well before a handbook PDF or static health
    fact would, so a stale cached answer should expire sooner.
    """

    return getattr(
        settings,
        "WEBSEARCH_ANSWER_CACHE_TTL",
        60 * 30,  # 30 minutes
    )


# ============================================================
# LOGGING
# ============================================================
#
# Simple, development-friendly logging: which route, and whether
# it was a HIT / MISS / SET / SKIP. Never logs the question text,
# the answer text, user identity, tokens, or any other private
# data — only the route label and the opaque (hashed) cache key,
# which is not reversible to the original question.
# ============================================================

VALID_ROUTES = (
    "GENERAL",
    "RAG",
    "WEBSEARCH",
    "AI_AGENT",
    "USER_INFORMATION",
)

VALID_EVENTS = (
    "HIT",
    "MISS",
    "SET",
    "SKIP",
)


def log_cache_event(event: str, route: str, key: str = None) -> None:

    event = event.upper()
    route = route.upper()

    if event not in VALID_EVENTS:
        event = "UNKNOWN"

    if route not in VALID_ROUTES:
        route = "UNKNOWN"

    if key:
        print(f"[{route}] CACHE {event} (key={key})")
    else:
        print(f"[{route}] CACHE {event}")