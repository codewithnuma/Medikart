# semantic_cache.py

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
from django.conf import settings
from django.core.cache import cache
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

EMBEDDING_MODEL_NAME = getattr(
    settings,
    "SEMANTIC_CACHE_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

SIMILARITY_THRESHOLD = float(
    getattr(
        settings,
        "SEMANTIC_CACHE_SIMILARITY_THRESHOLD",
        0.88,
    )
)

SEMANTIC_CACHE_TTL = int(
    getattr(
        settings,
        "SEMANTIC_CACHE_TTL",
        60 * 60 * 24,
    )
)

MAX_CACHE_ENTRIES = int(
    getattr(
        settings,
        "SEMANTIC_CACHE_MAX_ENTRIES",
        5000,
    )
)


# ---------------------------------------------------------
# Model singleton
# ---------------------------------------------------------

_model: Optional[SentenceTransformer] = None
_model_lock = threading.Lock()


def get_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once per Python process.

    Do NOT create SentenceTransformer() for every request.
    """

    global _model

    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info(
                    "Loading semantic cache model: %s",
                    EMBEDDING_MODEL_NAME,
                )

                _model = SentenceTransformer(
                    EMBEDDING_MODEL_NAME,
                    device="cpu",
                )

                logger.info(
                    "Semantic cache embedding model loaded"
                )

    return _model


# ---------------------------------------------------------
# Text normalization
# ---------------------------------------------------------

def normalize_question(question: str) -> str:
    if not question:
        return ""

    return " ".join(
        question.lower().strip().split()
    )


# ---------------------------------------------------------
# Embedding
# ---------------------------------------------------------

def create_embedding(question: str) -> np.ndarray:
    """
    Create a normalized embedding.

    normalize_embeddings=True means cosine similarity
    becomes a simple dot product.
    """

    normalized = normalize_question(question)

    if not normalized:
        raise ValueError("Question cannot be empty")

    model = get_embedding_model()

    embedding = model.encode(
        normalized,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embedding.astype(np.float32)


# ---------------------------------------------------------
# Cache key
# ---------------------------------------------------------

def _hash_question(question: str) -> str:
    normalized = normalize_question(question)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:32]


def _embedding_cache_key(question: str) -> str:
    question_hash = _hash_question(question)

    return (
        f"semantic-cache:embedding:{question_hash}"
    )


def _answer_cache_key(cache_id: str) -> str:
    return f"semantic-cache:answer:{cache_id}"


# ---------------------------------------------------------
# Cached item
# ---------------------------------------------------------

@dataclass
class SemanticCacheEntry:
    cache_id: str
    question: str
    embedding: np.ndarray
    answer: str
    created_at: float
    expires_at: float


# ---------------------------------------------------------
# Entry storage
# ---------------------------------------------------------

def save_entry(
    question: str,
    answer: str,
    embedding: np.ndarray,
    ttl: Optional[int] = None,
) -> Optional[str]:

    if not question or not answer:
        return None

    ttl = ttl or SEMANTIC_CACHE_TTL

    cache_id = _hash_question(
        question
    )

    now = time.time()

    entry = {
        "cache_id": cache_id,
        "question": question,
        "embedding": embedding.tolist(),
        "answer": answer,
        "created_at": now,
        "expires_at": now + ttl,
    }

    cache.set(
        _answer_cache_key(cache_id),
        entry,
        timeout=ttl,
    )

    # Maintain a registry of semantic cache IDs.
    registry = cache.get(
        "semantic-cache:registry",
        [],
    )

    if cache_id not in registry:
        registry.append(cache_id)

    # Prevent unlimited growth.
    if len(registry) > MAX_CACHE_ENTRIES:
        registry = registry[-MAX_CACHE_ENTRIES:]

    cache.set(
        "semantic-cache:registry",
        registry,
        timeout=SEMANTIC_CACHE_TTL,
    )

    return cache_id


# ---------------------------------------------------------
# Load entries
# ---------------------------------------------------------

def get_all_entries() -> list[SemanticCacheEntry]:

    registry = cache.get(
        "semantic-cache:registry",
        [],
    )

    entries = []

    now = time.time()

    for cache_id in registry:

        data = cache.get(
            _answer_cache_key(cache_id)
        )

        if not data:
            continue

        if data["expires_at"] <= now:
            continue

        try:
            embedding = np.asarray(
                data["embedding"],
                dtype=np.float32,
            )

            entries.append(
                SemanticCacheEntry(
                    cache_id=data["cache_id"],
                    question=data["question"],
                    embedding=embedding,
                    answer=data["answer"],
                    created_at=data["created_at"],
                    expires_at=data["expires_at"],
                )
            )

        except Exception:
            logger.exception(
                "Failed to load semantic cache entry"
            )

    return entries


# ---------------------------------------------------------
# Semantic search
# ---------------------------------------------------------

def find_similar_answer(
    question: str,
    threshold: Optional[float] = None,
) -> Optional[dict]:

    threshold = (
        threshold
        if threshold is not None
        else SIMILARITY_THRESHOLD
    )

    query_embedding = create_embedding(
        question
    )

    entries = get_all_entries()

    if not entries:
        return None

    best_entry = None
    best_score = -1.0

    for entry in entries:

        # Both vectors are normalized.
        # Therefore dot product = cosine similarity.
        score = float(
            np.dot(
                query_embedding,
                entry.embedding,
            )
        )

        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry is None:
        return None

    if best_score < threshold:
        return None

    logger.info(
        "Semantic cache HIT | score=%.4f | question=%s | matched=%s",
        best_score,
        question,
        best_entry.question,
    )

    return {
        "answer": best_entry.answer,
        "score": best_score,
        "matched_question": best_entry.question,
        "cache_id": best_entry.cache_id,
    }


# ---------------------------------------------------------
# Save answer
# ---------------------------------------------------------

def set_semantic_answer(
    question: str,
    answer: str,
    ttl: Optional[int] = None,
) -> bool:

    try:

        if not question or not answer:
            return False

        embedding = create_embedding(
            question
        )

        cache_id = save_entry(
            question=question,
            answer=answer,
            embedding=embedding,
            ttl=ttl,
        )

        if cache_id:
            logger.info(
                "Semantic cache SET | question=%s",
                question,
            )

            return True

        return False

    except Exception:
        logger.exception(
            "Semantic cache SET failed"
        )

        return False


# ---------------------------------------------------------
# Get answer
# ---------------------------------------------------------

def get_semantic_answer(
    question: str,
    threshold: Optional[float] = None,
) -> Optional[dict]:

    try:

        return find_similar_answer(
            question,
            threshold=threshold,
        )

    except Exception:
        logger.exception(
            "Semantic cache GET failed"
        )

        return None


# ---------------------------------------------------------
# Clear cache
# ---------------------------------------------------------

def clear_semantic_cache() -> None:

    registry = cache.get(
        "semantic-cache:registry",
        [],
    )

    for cache_id in registry:

        cache.delete(
            _answer_cache_key(cache_id)
        )

    cache.delete(
        "semantic-cache:registry"
    )

    logger.info(
        "Semantic cache cleared"
    )