# ============================================================
# C_rag.py
# ============================================================
# Horizon Trails Company Handbook RAG SUBGRAPH
#
# CHUNKING (in priority order):
#       1. Section-based chunking (deterministic, regex on
#          numbered headers like "12.1 Travel Insurance").
#          Keeps a whole section -- including numbers, money
#          amounts, thresholds -- together in one chunk instead
#          of letting an LLM slice it into separate "purpose"
#          groups.
#       2. If a section is too long, split it into overlapping
#          sentence windows (so a figure sitting near a chunk
#          boundary still shows up in both chunks).
#       3. If NO numbered sections are detected at all (doc
#          doesn't use that formatting), fall back to the
#          original LLM semantic-grouping pipeline:
#              Groq ChatGroq -> Gemini -> sentence-window fallback
#
# RETRIEVAL:
#       Hybrid dense (FAISS) + lexical (BM25) search, fused with
#       reciprocal rank fusion, then expanded with neighboring
#       chunks from the same section so a split detail (e.g. the
#       coverage amount sitting in the next window) is included.
#
# Embeddings:
#       sentence-transformers/all-MiniLM-L6-v2
#
# Vector store:
#       FAISS
#
# Orchestration:
#       LangGraph
#
# IMPORTANT:
#   - chatbot.py is NOT changed
#   - This file exports rag_graph_builder
#   - Chunking happens ONLY when FAISS does not exist
#   - Existing FAISS is loaded directly
#   - If you already have a FAISS index built with the OLD
#     chunking logic, DELETE the faiss_index_fast folder so it
#     gets rebuilt with the new section-aware chunker. Loading an
#     old index will just keep using the old chunks.
#
# LAZY INITIALIZATION:
#   - Everything heavy (Groq/Gemini/HF model clients, the
#     sentence-transformers embedding model, and — most
#     importantly — the FAISS vectorstore + BM25 index) used to
#     be built as soon as this module was imported. Since
#     chatbot.py imports `rag_graph_builder` from this file at
#     Django startup, that meant the PDF got chunked and FAISS
#     got built (or loaded) the moment the server booted, even
#     if nobody had asked a handbook question yet.
#   - All of that now lives behind get_rag_resources(), a
#     thread-safe singleton (same pattern as get_embedding_model()
#     in chatbot.py) that only runs on the FIRST real call into
#     retrieve_node(). Importing this module is now cheap: it
#     only defines functions/classes and builds the (equally
#     cheap) LangGraph wiring. The moment a handbook question
#     actually comes in, resources are built once and reused for
#     every request after that.
# ============================================================


# ============================================================
# STANDARD LIBRARY
# ============================================================

import os
import re
import math
import json
import time
import threading

from pathlib import Path
from collections import defaultdict, Counter
from typing import (
    TypedDict,
    List,
    Optional,
    Annotated,
)


# ============================================================
# ENVIRONMENT
# ============================================================

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# PYDANTIC
# ============================================================

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# LANGCHAIN CORE
# ============================================================

from langchain_core.documents import Document

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    BaseMessage,
)


# ============================================================
# PDF
# ============================================================

from langchain_community.document_loaders import (
    PyPDFLoader,
)


# ============================================================
# FAISS
# ============================================================

from langchain_community.vectorstores import FAISS


# ============================================================
# HUGGING FACE
# ============================================================

from langchain_huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceEndpoint,
    ChatHuggingFace,
)


# ============================================================
# GROQ
# ============================================================

from langchain_groq import ChatGroq


# ============================================================
# GEMINI
# ============================================================

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
)


# ============================================================
# LANGGRAPH
# ============================================================

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.graph.message import add_messages


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


PDF_PATH = (
    BASE_DIR
    / "documents"
    / "Medikart_Knowledge_Base.pdf"
)


FAISS_DIR = (
    BASE_DIR
    / "faiss_index_fast"
)


# ============================================================
# CONFIGURATION
# ============================================================

TOP_K = 5

FETCH_K_MULTIPLIER = 3

RRF_K = 60

MAX_RETURNED_DOCUMENTS = 8

SEMANTIC_BATCH_SIZE = 15

MAX_SENTENCES_PER_CHUNK = 8

OVERLAP_SENTENCES = 2

MIN_SECTIONS_FOR_SECTION_MODE = 3

SEMANTIC_MAX_RETRIES = 2

SEMANTIC_RETRY_DELAY = 1.5


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# GROQ SEMANTIC CHUNKING (fallback path only)
# ------------------------------------------------------------

GROQ_MODEL = (
    "openai/gpt-oss-120b"
)


# ------------------------------------------------------------
# GEMINI SEMANTIC CHUNKING (fallback path only)
# ------------------------------------------------------------

GEMINI_MODEL = (
    "gemini-3.8-flash"
)


# ------------------------------------------------------------
# FINAL RAG MODEL
# ------------------------------------------------------------

RAG_MODEL = (
    "Qwen/Qwen2.5-1.5B-Instruct"
)


# ============================================================
# API KEYS
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)


HF_TOKEN = os.getenv(
    "HUGGINGFACEHUB_API_TOKEN"
)


# ============================================================
# SEMANTIC GROUP SCHEMA (fallback path only)
# ============================================================

class SemanticGroup(BaseModel):

    sentence_indexes: List[int]

    purpose: str


class SemanticGroupingResult(BaseModel):

    groups: List[SemanticGroup] = Field(
        default_factory=list
    )


SEMANTIC_SYSTEM_PROMPT = """
You are a semantic document chunking engine.

Your job is to group consecutive sentences from a company
handbook into semantically coherent groups.

The input contains numbered sentences.

Return ONLY valid JSON.

Do NOT return:
- Markdown
- code fences
- explanations
- comments
- reasoning
- extra text

The JSON must have exactly this top-level structure:

{
  "groups": [
    {
      "sentence_indexes": [0, 1, 2],
      "purpose": "Short description of what these sentences explain"
    }
  ]
}

Rules:

1. sentence_indexes are ZERO-BASED indexes.
2. Every sentence index must appear exactly once.
3. Do not invent indexes.
4. Do not omit indexes.
5. Groups must preserve the original sentence order.
6. A group must contain semantically related sentences.
7. A group may contain at most 8 sentences.
8. Keep any sentence containing a number, amount, currency,
   percentage, date, or threshold IN THE SAME GROUP as the
   sentence(s) that explain what that number refers to. Never
   isolate a number from the rule/requirement it belongs to.
9. If a sentence does not strongly belong to another group,
   create a separate group.
10. The purpose must be short and descriptive.
11. Return ONLY the JSON object.
12. Do not include a ```json code fence.
13. Do not include reasoning or analysis before the JSON.
"""


# ============================================================
# STREAMING CONCURRENCY LOCK
# ============================================================
#
# The (lazily-built) rag_model is a single ChatHuggingFace
# instance shared by EVERY request once it's built. Django can
# (and does) serve requests on multiple threads concurrently. If
# two requests call rag_model.stream(...) at the same moment,
# their two response streams can get their chunks crossed by the
# underlying HTTP client, producing ONE answer that is actually
# two different answers glued together mid-word (this is what
# caused unrelated content from a different concurrent request to
# appear mixed into an otherwise correct answer).
#
# This lock ensures only one .stream() call on rag_model is ever
# in flight at a time, across all requests, which eliminates the
# cross-contamination entirely. Requests queue briefly under real
# concurrent load instead of racing on the same client.
#
# This is cheap (just a Lock object), so it stays at module level
# — no need to lazy-load it.
# ============================================================

_RAG_STREAM_LOCK = threading.Lock()


# ============================================================
# MESSAGE CONTENT EXTRACTION
# ============================================================
#
# Used for non-streaming / one-shot model responses (semantic
# chunking calls to Groq/Gemini). NOT used for streaming deltas —
# see extract_stream_delta below for that.
# ============================================================

def extract_message_content(response) -> str:

    if response is None:
        return ""

    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):

                text = item.get("text")

                if text:
                    parts.append(str(text))

        return "\n".join(parts).strip()

    return str(content).strip()


# ============================================================
# STREAMING DELTA EXTRACTION
# ============================================================
#
# Like extract_message_content, but for a SINGLE streaming chunk
# that will be concatenated with other chunks. Must NOT strip() -
# a leading/trailing space in a streamed delta is the word
# boundary itself (e.g. " the", " charge"). Stripping each delta
# individually, then joining them, glues words together with no
# space in between ("thecancellationcharge...").
#
# Strip only the FULLY ASSEMBLED answer once, after the loop.
# ============================================================

def extract_stream_delta(chunk) -> str:

    if chunk is None:
        return ""

    content = getattr(chunk, "content", chunk)

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):

                text = item.get("text")

                if text:
                    parts.append(str(text))

        return "".join(parts)

    return str(content)


# ============================================================
# CLEAN / PARSE JSON RESPONSE (fallback path only)
# ============================================================

def clean_json_response(raw_content: str) -> str:

    if not raw_content:
        raise ValueError("Model returned empty content.")

    text = raw_content.strip()

    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    if end <= start:
        raise ValueError("Invalid JSON boundaries.")

    return text[start:end + 1]


def parse_semantic_json(raw_content: str) -> SemanticGroupingResult:

    cleaned = clean_json_response(raw_content)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON returned by model: {error}")

    if not isinstance(data, dict):
        raise ValueError("Semantic response must be a JSON object.")

    if "groups" not in data:
        raise ValueError("Semantic response does not contain 'groups'.")

    return SemanticGroupingResult.model_validate(data)


# ============================================================
# PROVIDER ERROR CLASSIFICATION (fallback path only)
# ============================================================

def is_non_retryable_provider_error(error: Exception) -> bool:

    message = str(error).lower()

    non_retryable_patterns = [
        "400", "401", "402", "403", "404", "429",
        "unauthorized", "authentication", "invalid api key",
        "api key invalid", "permission denied", "forbidden",
        "does not have access", "model_not_found", "model not found",
        "does not exist", "deprecated", "shutdown", "payment required",
        "billing", "payment", "insufficient quota", "quota exceeded",
        "quota", "rate limit", "too many requests", "resource exhausted",
    ]

    return any(pattern in message for pattern in non_retryable_patterns)


# ============================================================
# GROQ / GEMINI SEMANTIC CALLS (fallback path only)
#
# These read the lazily-built resources via get_rag_resources()
# instead of module-level globals, so they can't accidentally
# trigger initialization on their own before it's actually wanted.
# ============================================================

def call_groq_semantic(sentences: List[str]) -> SemanticGroupingResult:

    resources = get_rag_resources()

    if resources.groq_model is None:
        raise RuntimeError("ChatGroq is not initialized.")

    numbered_sentences = "\n".join(
        f"{index}. {sentence}" for index, sentence in enumerate(sentences)
    )

    user_prompt = (
        "Group the following numbered sentences.\n\n"
        "Return ONLY valid JSON according to the required format.\n\n"
        f"Sentences:\n\n{numbered_sentences}"
    )

    response = resources.groq_model.invoke([
        SystemMessage(content=SEMANTIC_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    raw_content = extract_message_content(response)

    return parse_semantic_json(raw_content)


def call_gemini_semantic(sentences: List[str]) -> SemanticGroupingResult:

    resources = get_rag_resources()

    if resources.gemini_model is None:
        raise RuntimeError("Gemini is not initialized.")

    numbered_sentences = "\n".join(
        f"{index}. {sentence}" for index, sentence in enumerate(sentences)
    )

    user_prompt = (
        "Group the following numbered sentences.\n\n"
        "Return ONLY valid JSON according to the required format.\n\n"
        f"Sentences:\n\n{numbered_sentences}"
    )

    response = resources.gemini_model.invoke([
        SystemMessage(content=SEMANTIC_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    raw_content = extract_message_content(response)

    return parse_semantic_json(raw_content)


def run_provider_with_retry(provider_name, provider_function, sentences):

    for attempt in range(1, SEMANTIC_MAX_RETRIES + 1):

        try:

            print(f"      {provider_name} attempt {attempt}/{SEMANTIC_MAX_RETRIES}")

            result = provider_function(sentences)

            print(f"      {provider_name} semantic grouping successful.")

            return result

        except Exception as error:

            print(f"      {provider_name} semantic grouping failed.")
            print(f"      Error: {error}")

            if is_non_retryable_provider_error(error):
                print(f"      {provider_name} error is non-retryable.")
                print("      Switching provider...")
                raise

            if attempt < SEMANTIC_MAX_RETRIES:
                print(f"      Retrying {provider_name}...")
                time.sleep(SEMANTIC_RETRY_DELAY)
            else:
                print(f"      {provider_name} failed after {SEMANTIC_MAX_RETRIES} attempts.")
                raise


def get_semantic_groups(sentences: List[str]) -> SemanticGroupingResult:

    resources = get_rag_resources()

    groq_error = None
    gemini_error = None

    if resources.groq_available:

        try:
            return run_provider_with_retry("ChatGroq", call_groq_semantic, sentences)
        except Exception as error:
            groq_error = error
            print("      ChatGroq unavailable. Moving to Gemini...")

    else:
        print("      ChatGroq is unavailable. Skipping directly to Gemini.")

    if resources.gemini_available:

        try:
            return run_provider_with_retry("Gemini", call_gemini_semantic, sentences)
        except Exception as error:
            gemini_error = error
            print("      Gemini unavailable.")

    else:
        print("      Gemini is unavailable.")

    error_messages = []

    if groq_error:
        error_messages.append(f"Groq: {groq_error}")

    if gemini_error:
        error_messages.append(f"Gemini: {gemini_error}")

    combined_error = (
        " | ".join(error_messages)
        if error_messages
        else "No semantic provider is available."
    )

    raise RuntimeError("Both semantic providers failed. " + combined_error)


# ============================================================
# SENTENCE SPLITTER
# ============================================================

def split_into_sentences(text: str) -> List[str]:

    text = text.strip()

    if not text:
        return []

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)

    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


# ============================================================
# SECTION-BASED CHUNKING (PRIMARY PATH)
# ============================================================
#
# Handbooks are almost always organized under numbered headers
# like "12.1 Travel Insurance Requirements". Chunking around
# those headers -- instead of letting an LLM regroup sentences by
# "purpose" -- guarantees a requirement and the number attached to
# it (e.g. "mandatory above 3,000m" + "USD 100,000 coverage")
# land in the SAME chunk, because they physically are the same
# section.
# ============================================================

SECTION_HEADER_PATTERN = re.compile(
    r"(?m)^(?P<number>\d{1,2}(?:\.\d{1,2}){0,3})[\.\)]?\s+"
    r"(?P<title>[A-Z][A-Za-z0-9,&/\-\(\) ]{2,90})\s*$"
)

PAGE_MARKER_TEMPLATE = "\n\n<<<PAGE_{page}>>>\n\n"

PAGE_MARKER_STRIP_PATTERN = re.compile(r"<<<PAGE_\d+>>>")


def build_full_text_with_page_map(documents: List[Document]):
    """Concatenate all pages into one text blob, remembering which
    character offset corresponds to which PDF page, so sections
    that span a page break (or headers that live near a break)
    still resolve to a correct page number."""

    parts = []
    page_offsets = []
    cursor = 0

    for page_number, document in enumerate(documents, start=1):

        marker = PAGE_MARKER_TEMPLATE.format(page=page_number)
        parts.append(marker)
        cursor += len(marker)

        page_offsets.append((cursor, page_number))

        text = (document.page_content or "").strip()
        parts.append(text)
        cursor += len(text)

    full_text = "".join(parts)

    return full_text, page_offsets


def page_for_offset(offset: int, page_offsets) -> int:

    page = page_offsets[0][1] if page_offsets else 1

    for start, page_number in page_offsets:

        if start <= offset:
            page = page_number
        else:
            break

    return page


def detect_sections(full_text: str):

    matches = list(SECTION_HEADER_PATTERN.finditer(full_text))

    sections = []

    for idx, match in enumerate(matches):

        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(full_text)

        sections.append({
            "number": match.group("number").strip(),
            "title": match.group("title").strip(),
            "start": start,
            "end": end,
        })

    return sections


def build_chunk_document(section, sentences, chunk_index, total_chunks, page_number) -> Document:

    header = f"Section {section['number']} — {section['title']}"
    body = " ".join(sentences).strip()
    content = f"{header}\n\n{body}"

    metadata = {
        "page": page_number,
        "section_number": section["number"],
        "section_title": section["title"],
        "chunk_index": chunk_index,
        "section_total_chunks": total_chunks,
        "chunk_type": "section",
        "purpose": section["title"],
        "sentence_count": len(sentences),
    }

    return Document(page_content=content, metadata=metadata)


def build_section_chunks(full_text: str, sections, page_offsets) -> List[Document]:

    chunks = []

    for section in sections:

        section_text = full_text[section["start"]:section["end"]]
        section_text = PAGE_MARKER_STRIP_PATTERN.sub(" ", section_text).strip()

        sentences = split_into_sentences(section_text)

        if not sentences:
            continue

        page_number = page_for_offset(section["start"], page_offsets)

        # ----------------------------------------------------
        # Short section -> one chunk, nothing gets separated
        # ----------------------------------------------------

        if len(sentences) <= MAX_SENTENCES_PER_CHUNK:

            chunks.append(
                build_chunk_document(section, sentences, 0, 1, page_number)
            )

            continue

        # ----------------------------------------------------
        # Long section -> overlapping sentence windows, so any
        # figure sitting near a boundary appears in two chunks
        # instead of being stranded in just one.
        # ----------------------------------------------------

        windows = []
        start = 0

        while start < len(sentences):

            end = min(start + MAX_SENTENCES_PER_CHUNK, len(sentences))
            windows.append(sentences[start:end])

            if end == len(sentences):
                break

            start = end - OVERLAP_SENTENCES

        for chunk_index, window_sentences in enumerate(windows):

            chunks.append(
                build_chunk_document(
                    section, window_sentences, chunk_index, len(windows), page_number
                )
            )

    return chunks


# ============================================================
# FALLBACK CHUNKING (LLM semantic grouping, per page)
# ============================================================
# Only used when no numbered sections are detected at all, i.e.
# the handbook doesn't follow "12.1 Title" style headers. Kept
# close to the original implementation, with one important fix:
# the sentence-level fallback no longer produces one-sentence
# chunks (which threw away all surrounding context) -- it now
# uses the same overlapping-window approach as the primary path.
# ============================================================

def sentence_level_fallback(sentences: List[str]) -> List[SemanticGroup]:

    groups = []
    start = 0

    while start < len(sentences):

        end = min(start + MAX_SENTENCES_PER_CHUNK, len(sentences))

        groups.append(
            SemanticGroup(
                sentence_indexes=list(range(start, end)),
                purpose="Grouped sentences (window fallback)",
            )
        )

        if end == len(sentences):
            break

        start = end - OVERLAP_SENTENCES

    return groups


def validate_semantic_groups(result: SemanticGroupingResult, sentence_count: int) -> List[SemanticGroup]:

    if sentence_count == 0:
        return []

    valid_groups = []
    used_indexes = set()

    for group in result.groups:

        valid_indexes = []

        for index in group.sentence_indexes:

            if not isinstance(index, int):
                continue
            if index < 0 or index >= sentence_count:
                continue
            if index in used_indexes:
                continue

            valid_indexes.append(index)
            used_indexes.add(index)

        if not valid_indexes:
            continue

        valid_groups.append(
            SemanticGroup(
                sentence_indexes=valid_indexes,
                purpose=group.purpose.strip() if group.purpose else "Related information",
            )
        )

    missing_indexes = [i for i in range(sentence_count) if i not in used_indexes]

    for index in missing_indexes:

        valid_groups.append(
            SemanticGroup(sentence_indexes=[index], purpose="Individual information")
        )

    valid_groups.sort(key=lambda group: min(group.sentence_indexes))

    return valid_groups


def split_large_group(group: SemanticGroup) -> List[SemanticGroup]:

    indexes = group.sentence_indexes

    if len(indexes) <= MAX_SENTENCES_PER_CHUNK:
        return [group]

    result = []

    for start in range(0, len(indexes), MAX_SENTENCES_PER_CHUNK):

        chunk_indexes = indexes[start:start + MAX_SENTENCES_PER_CHUNK]

        result.append(SemanticGroup(sentence_indexes=chunk_indexes, purpose=group.purpose))

    return result


def semantic_group_batch(sentences: List[str]) -> List[SemanticGroup]:

    if not sentences:
        return []

    try:

        result = get_semantic_groups(sentences)

        validated = validate_semantic_groups(result, len(sentences))

        final_groups = []

        for group in validated:
            final_groups.extend(split_large_group(group))

        return final_groups

    except Exception as error:

        print()
        print("    WARNING: Both semantic providers failed.")
        print(f"    Error: {error}")
        print("    Using overlapping-window fallback.")

        return sentence_level_fallback(sentences)


def purpose_based_chunk_page(page_document: Document, page_number: int) -> List[Document]:

    page_text = (page_document.page_content or "").strip()

    if not page_text:
        return []

    sentences = split_into_sentences(page_text)

    if not sentences:
        return []

    all_groups = []

    for batch_start in range(0, len(sentences), SEMANTIC_BATCH_SIZE):

        batch_end = min(batch_start + SEMANTIC_BATCH_SIZE, len(sentences))
        batch_sentences = sentences[batch_start:batch_end]

        print()
        print(f"    Semantic grouping: sentences {batch_start}-{batch_end - 1}")

        local_groups = semantic_group_batch(batch_sentences)

        for group in local_groups:

            global_indexes = [batch_start + index for index in group.sentence_indexes]

            all_groups.append(
                SemanticGroup(sentence_indexes=global_indexes, purpose=group.purpose)
            )

    chunks = []

    for group_index, group in enumerate(all_groups):

        group_sentences = [
            sentences[index] for index in group.sentence_indexes if 0 <= index < len(sentences)
        ]

        if not group_sentences:
            continue

        content = " ".join(group_sentences).strip()

        if not content:
            continue

        metadata = dict(page_document.metadata)

        metadata.update({
            "page": page_number,
            "chunk_index": group_index,
            "chunk_type": "semantic",
            "purpose": group.purpose,
            "sentence_count": len(group_sentences),
        })

        chunks.append(Document(page_content=content, metadata=metadata))

    return chunks


def chunk_documents_legacy(documents: List[Document]) -> List[Document]:

    print()
    print("========== LLM SEMANTIC CHUNKING (fallback) ==========")

    all_chunks = []

    for page_number, document in enumerate(documents, start=1):

        print()
        print(f"Processing page {page_number}...")

        page_chunks = purpose_based_chunk_page(document, page_number)
        all_chunks.extend(page_chunks)

        print("Semantic chunks found:", len(page_chunks))

    print()
    print("Total semantic chunks:", len(all_chunks))
    print("=" * 60)

    return all_chunks


# ============================================================
# CHUNKING ENTRY POINT
# ============================================================

def chunk_documents(documents: List[Document]) -> List[Document]:

    print()
    print("========== CHUNKING ==========")

    full_text, page_offsets = build_full_text_with_page_map(documents)

    sections = detect_sections(full_text)

    print(f"Detected {len(sections)} numbered section header(s).")

    if len(sections) >= MIN_SECTIONS_FOR_SECTION_MODE:

        print("Using SECTION-BASED chunking (deterministic).")

        chunks = build_section_chunks(full_text, sections, page_offsets)

        if chunks:

            print(f"Total section-based chunks: {len(chunks)}")
            print("=" * 60)

            return chunks

        print("Section-based chunking produced no chunks. Falling back.")

    print("Falling back to LLM semantic chunking (per-page).")

    return chunk_documents_legacy(documents)


# ============================================================
# PRINT SAMPLE CHUNKS
# ============================================================

def print_sample_chunks(chunks: List[Document], number: int = 5):

    print()
    print("========== SAMPLE CHUNKS ==========")

    for index, chunk in enumerate(chunks[:number]):

        print()
        print(f"CHUNK {index + 1}")
        print("Page:", chunk.metadata.get("page"))
        print("Section:", chunk.metadata.get("section_number"))
        print("Purpose:", chunk.metadata.get("purpose"))
        print("Content:")
        print(chunk.page_content[:1000])
        print("-" * 50)


# ============================================================
# LOAD PDF
# ============================================================

def load_pdf() -> List[Document]:

    print()
    print("========== LOADING PDF ==========")

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF file not found:\n{PDF_PATH}")

    start_time = time.time()

    loader = PyPDFLoader(str(PDF_PATH))
    documents = loader.load()

    elapsed = time.time() - start_time

    print(f"Pages loaded: {len(documents)}")
    print(f"PDF loading time: {elapsed:.3f}s")
    print("=================================")

    return documents


# ============================================================
# BUILD / LOAD FAISS
#
# Both take the embedding model explicitly now (instead of
# reaching for a module-level global) so they can be called
# safely from inside the lazy resource builder below, in whatever
# order that builder assembles things.
# ============================================================

def build_faiss(chunks: List[Document], embedding_model):

    print()
    print("========== BUILDING FAISS ==========")

    if not chunks:
        raise RuntimeError("No chunks were generated.")

    start_time = time.time()

    vectorstore = FAISS.from_documents(documents=chunks, embedding=embedding_model)

    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(FAISS_DIR))

    elapsed = time.time() - start_time

    print("FAISS index saved to:", FAISS_DIR)
    print(f"FAISS build time: {elapsed:.3f}s")
    print("====================================")

    return vectorstore


def load_faiss(embedding_model):

    print()
    print("========== LOADING EXISTING FAISS ==========")

    if not FAISS_DIR.exists():
        raise FileNotFoundError(f"FAISS directory does not exist: {FAISS_DIR}")

    vectorstore = FAISS.load_local(
        str(FAISS_DIR),
        embedding_model,
        allow_dangerous_deserialization=True,
    )

    print("FAISS index loaded successfully.")
    print("FAISS path:", FAISS_DIR)
    print("============================================")

    return vectorstore


def get_vectorstore(embedding_model):

    if FAISS_DIR.exists():

        print()
        print("=" * 60)
        print("EXISTING FAISS INDEX FOUND")
        print("Loading existing FAISS. Chunking will NOT run.")
        print(
            "(If you changed the chunking logic, delete "
            "faiss_index_fast/ to rebuild.)"
        )
        print("=" * 60)

        return load_faiss(embedding_model)

    print()
    print("=" * 60)
    print("FAISS INDEX NOT FOUND")
    print("Building FAISS from handbook PDF.")
    print("=" * 60)

    documents = load_pdf()
    chunks = chunk_documents(documents)

    print_sample_chunks(chunks, number=5)

    return build_faiss(chunks, embedding_model)


# ============================================================
# LEXICAL (BM25) INDEX
# ============================================================
#
# Dense embeddings are good at "what is this about" but weak at
# exact tokens like "USD 100,000" or "3,000m" -- those don't carry
# much semantic weight, so a purely vector search can rank a
# generic passage above the one with the actual figure. A small,
# dependency-free BM25 index fixes that by rewarding literal term
# overlap, and gets fused with the dense results below.
# ============================================================

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[.,][a-z0-9]+)*")


class SimpleBM25:

    def __init__(self, documents: List[Document], k1: float = 1.5, b: float = 0.75):

        self.k1 = k1
        self.b = b
        self.documents = documents

        self.doc_tokens = [self._tokenize(doc.page_content) for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]

        self.avg_doc_length = (
            sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0
        )

        self.doc_term_counts = [Counter(tokens) for tokens in self.doc_tokens]

        self.idf = {}
        self._build_idf()

    @staticmethod
    def _tokenize(text: str) -> List[str]:

        return TOKEN_PATTERN.findall(text.lower())

    def _build_idf(self):

        document_frequency = defaultdict(int)

        for counts in self.doc_term_counts:
            for term in counts:
                document_frequency[term] += 1

        n_docs = len(self.doc_tokens)

        for term, freq in document_frequency.items():

            self.idf[term] = math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: str) -> List[float]:

        query_tokens = self._tokenize(query)
        scores = [0.0] * len(self.documents)

        for doc_index, counts in enumerate(self.doc_term_counts):

            doc_len = self.doc_lengths[doc_index] or 1
            score = 0.0

            for term in query_tokens:

                if term not in counts:
                    continue

                freq = counts[term]
                idf = self.idf.get(term, 0.0)

                denom = freq + self.k1 * (
                    1 - self.b + self.b * doc_len / (self.avg_doc_length or 1)
                )

                score += idf * (freq * (self.k1 + 1)) / (denom or 1)

            scores[doc_index] = score

        return scores

    def get_top_n(self, query: str, n: int = 10) -> List[Document]:

        scores = self.get_scores(query)

        ranked_indexes = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        return [self.documents[i] for i in ranked_indexes[:n] if scores[i] > 0]


def get_all_documents_from_vectorstore(vs) -> List[Document]:
    """Pull every chunk back out of FAISS's docstore so we can
    build the BM25 index and the section-neighbor lookup, without
    needing to persist the chunk list separately -- FAISS already
    saves/loads its docstore alongside the index."""

    try:
        return list(vs.docstore._dict.values())
    except Exception as error:
        print("Warning: could not read FAISS docstore for BM25/neighbor index:", error)
        return []


def build_section_lookup(documents: List[Document]):

    lookup = defaultdict(dict)

    for doc in documents:

        section_number = doc.metadata.get("section_number")
        chunk_index = doc.metadata.get("chunk_index")

        if section_number is None or chunk_index is None:
            continue

        lookup[section_number][chunk_index] = doc

    return lookup


# ============================================================
# LAZY RAG RESOURCES (models, embeddings, FAISS, BM25)
#
# Everything that used to run at module-import time (API key
# checks, ChatGroq/Gemini/HF client construction, embedding model
# load, and — the expensive one — get_vectorstore(), which chunks
# the PDF and builds FAISS from scratch when faiss_index_fast/
# doesn't exist yet) now lives here instead.
#
# get_rag_resources() is called from retrieve_node(), i.e. only
# once an actual handbook question reaches the graph. The first
# call does all the setup (and prints the same diagnostics the
# old module-level code used to print); every call after that
# just returns the already-built resources. Thread-safe via the
# same double-checked-locking pattern chatbot.py already uses for
# its embedding model.
# ============================================================

class _RAGResources:

    def __init__(self):

        self.embedding_model = None

        self.groq_model = None
        self.groq_available = False

        self.gemini_model = None
        self.gemini_available = False

        self.rag_model = None

        self.vectorstore = None
        self.all_documents = None
        self.bm25_index = None
        self.section_lookup = None


_rag_resources: Optional[_RAGResources] = None

_rag_resources_lock = threading.Lock()


def _build_rag_resources() -> _RAGResources:

    print()
    print("=" * 60)
    print("HORIZON TRAILS RAG SUBGRAPH — INITIALIZING")
    print("(first handbook question triggered setup)")
    print("=" * 60)

    print(
        "Groq API key:",
        "FOUND" if GROQ_API_KEY else "NOT FOUND"
    )

    print(
        "Gemini API key:",
        "FOUND" if GEMINI_API_KEY else "NOT FOUND"
    )

    print(
        "Hugging Face token:",
        "FOUND" if HF_TOKEN else "NOT FOUND"
    )

    print("=" * 60)

    if not HF_TOKEN:

        raise RuntimeError(
            "HUGGINGFACEHUB_API_TOKEN is missing "
            "from .env"
        )

    # Hugging Face token compatibility.
    os.environ["HF_TOKEN"] = HF_TOKEN

    resources = _RAGResources()

    # --------------------------------------------------------
    # GROQ (semantic chunking fallback only)
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("INITIALIZING CHATGROQ")
    print("=" * 60)

    print("Groq model:", GROQ_MODEL)

    if GROQ_API_KEY:

        try:

            resources.groq_model = ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=0,
                max_tokens=1200,
            )

            resources.groq_available = True

            print("ChatGroq initialized successfully.")

        except Exception as error:

            resources.groq_available = False

            print("ChatGroq initialization failed.")
            print("Error:", error)

    else:

        print("GROQ_API_KEY not found.")

    # --------------------------------------------------------
    # GEMINI (semantic chunking fallback only)
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("INITIALIZING GEMINI")
    print("=" * 60)

    print("Gemini model:", GEMINI_MODEL)

    if GEMINI_API_KEY:

        try:

            resources.gemini_model = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GEMINI_API_KEY,
                max_output_tokens=1200,
            )

            resources.gemini_available = True

            print("Gemini initialized successfully.")

        except Exception as error:

            resources.gemini_available = False

            print("Gemini initialization failed.")
            print("Error:", error)

    else:

        print("GEMINI_API_KEY not found.")

    # --------------------------------------------------------
    # HUGGING FACE RAG MODEL (final answer generation)
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("INITIALIZING HUGGING FACE RAG MODEL")
    print("=" * 60)

    print("RAG model:", RAG_MODEL)

    try:

        rag_endpoint = HuggingFaceEndpoint(
            repo_id=RAG_MODEL,
            task="text-generation",
            provider="featherless-ai",
            huggingfacehub_api_token=HF_TOKEN,
            max_new_tokens=500,
            temperature=0.1,
            top_p=0.9,
        )

        resources.rag_model = ChatHuggingFace(
            llm=rag_endpoint
        )

        print("Hugging Face RAG model initialized.")

    except Exception as error:

        raise RuntimeError(
            "Failed to initialize Hugging Face "
            "RAG model.\n"
            f"Error: {error}"
        )

    print("=" * 60)

    # --------------------------------------------------------
    # EMBEDDING MODEL
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("LOADING EMBEDDING MODEL")
    print("=" * 60)

    embedding_start = time.time()

    resources.embedding_model = HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    embedding_time = time.time() - embedding_start

    print("Embedding model loaded.")
    print(f"Embedding load time: {embedding_time:.3f}s")
    print("=" * 60)

    # --------------------------------------------------------
    # FAISS VECTORSTORE (this is the step that used to run at
    # import time and chunk the PDF on every server start if
    # faiss_index_fast/ didn't exist yet).
    # --------------------------------------------------------

    resources.vectorstore = get_vectorstore(resources.embedding_model)

    # --------------------------------------------------------
    # BM25 + SECTION NEIGHBOR LOOKUP
    # --------------------------------------------------------

    resources.all_documents = get_all_documents_from_vectorstore(
        resources.vectorstore
    )

    resources.bm25_index = (
        SimpleBM25(resources.all_documents)
        if resources.all_documents
        else None
    )

    resources.section_lookup = build_section_lookup(
        resources.all_documents
    )

    print()
    print("=" * 60)
    print("HORIZON TRAILS RAG SUBGRAPH — READY")
    print("=" * 60)

    return resources


def get_rag_resources() -> _RAGResources:
    """
    Thread-safe lazy singleton. First call (from the first real
    handbook question) builds everything; every call after that
    returns the same already-built resources instantly.
    """

    global _rag_resources

    if _rag_resources is None:

        with _rag_resources_lock:

            if _rag_resources is None:

                _rag_resources = _build_rag_resources()

    return _rag_resources


def preload_rag_resources() -> None:
    """
    Optional: call this (e.g. from a management command, a
    background thread, or AppConfig.ready() the same way
    preload_semantic_cache_model() is already called for the
    embedding cache model) if you want the handbook index warmed
    up ahead of the first real question instead of on it. Not
    called automatically — importing this module stays cheap by
    default.
    """

    try:
        get_rag_resources()
    except Exception as exc:
        print(
            "RAG resource preload failed:",
            type(exc).__name__,
            str(exc),
        )


# ============================================================
# HYBRID RETRIEVAL
#
# These now pull the embedding model / vectorstore / BM25 index /
# section lookup from get_rag_resources() rather than module-level
# globals, so calling them is what actually triggers lazy setup
# (via retrieve_node() below) rather than import time.
# ============================================================

def _doc_key(doc: Document):

    return (
        doc.metadata.get("page"),
        doc.metadata.get("section_number"),
        doc.metadata.get("chunk_index"),
        doc.page_content[:80],
    )


def _reciprocal_rank_fuse(*ranked_lists: List[Document]) -> List[Document]:

    fused_scores = defaultdict(float)
    doc_lookup = {}

    for ranked_list in ranked_lists:

        for rank, doc in enumerate(ranked_list):

            key = _doc_key(doc)
            doc_lookup[key] = doc
            fused_scores[key] += 1.0 / (RRF_K + rank + 1)

    ranked_keys = sorted(fused_scores.keys(), key=lambda key: fused_scores[key], reverse=True)

    return [doc_lookup[key] for key in ranked_keys]


def _expand_with_neighbors(top_docs: List[Document], max_total: int, section_lookup) -> List[Document]:

    seen_keys = {_doc_key(doc) for doc in top_docs}
    result = list(top_docs)

    for doc in top_docs:

        if len(result) >= max_total:
            break

        section_number = doc.metadata.get("section_number")
        chunk_index = doc.metadata.get("chunk_index")
        total_chunks = doc.metadata.get("section_total_chunks", 1)

        if section_number is None or chunk_index is None or total_chunks <= 1:
            continue

        for neighbor_index in (chunk_index - 1, chunk_index + 1):

            if len(result) >= max_total:
                break

            neighbor_doc = section_lookup.get(section_number, {}).get(neighbor_index)

            if neighbor_doc is None:
                continue

            neighbor_key = _doc_key(neighbor_doc)

            if neighbor_key in seen_keys:
                continue

            seen_keys.add(neighbor_key)
            result.append(neighbor_doc)

    return result


def hybrid_retrieve(query: str, k: int = TOP_K) -> List[Document]:

    if not query:
        return []

    resources = get_rag_resources()

    fetch_k = max(k * FETCH_K_MULTIPLIER, 10)

    query_vector = resources.embedding_model.embed_query(query)

    dense_hits = resources.vectorstore.similarity_search_by_vector(query_vector, k=fetch_k)

    bm25_hits = (
        resources.bm25_index.get_top_n(query, n=fetch_k)
        if resources.bm25_index
        else []
    )

    fused = _reciprocal_rank_fuse(dense_hits, bm25_hits)

    top_docs = fused[:k]

    expanded = _expand_with_neighbors(
        top_docs,
        max_total=min(MAX_RETURNED_DOCUMENTS, k + 3),
        section_lookup=resources.section_lookup,
    )

    return expanded


def retrieve_documents(query: str) -> List[Document]:

    return hybrid_retrieve(query, k=TOP_K)


# ============================================================
# FORMAT RETRIEVED CONTEXT
# ============================================================

def format_context(documents: List[Document]) -> str:

    if not documents:
        return "No relevant information was retrieved from the handbook."

    context_parts = []

    for index, document in enumerate(documents, start=1):

        page = document.metadata.get("page", "Unknown")
        section_number = document.metadata.get("section_number")

        section_title = document.metadata.get("section_title") or document.metadata.get(
            "purpose", "Related information"
        )

        if section_number:
            location = f"Section {section_number} ({section_title})"
        else:
            location = section_title

        context_parts.append(
            f"SOURCE {index}\nPage: {page}\nLocation: {location}\n\n{document.page_content}".strip()
        )

    return "\n\n".join(context_parts)


# ============================================================
# RAG SYSTEM PROMPT
# ============================================================

RAG_SYSTEM_PROMPT = """
You are the Horizon Trails Company Handbook assistant.

Answer the user's question using ONLY the supplied handbook
context.

Rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not supported by the context, say:
   "I could not find that information in the Horizon Trails
   Company Handbook."
4. Give a concise but useful answer.
5. ALWAYS include exact figures from the context verbatim --
   amounts, currencies, percentages, altitudes, dates, and
   deadlines -- do not round, paraphrase, or drop them.
6. When possible, mention the relevant handbook section and page.
7. Do not mention internal models, vector databases,
   embeddings, chunking, LangGraph, or retrieval systems.
8. Do not claim something is in the handbook unless it is
   supported by the supplied context.
"""


# ============================================================
# LANGGRAPH STATE
# ============================================================

class RAGState(TypedDict, total=False):

    messages: Annotated[List[BaseMessage], add_messages]

    retrieved_documents: List[Document]

    context: str

    answer: str


# ============================================================
# RETRIEVE NODE
#
# This is the first node the compiled graph runs, and therefore
# the single entry point that actually needs the RAG resources.
# retrieve_documents() -> hybrid_retrieve() -> get_rag_resources()
# handles lazy setup on the first real call; every call after
# that is effectively free.
# ============================================================

def retrieve_node(state: RAGState):

    messages = state.get("messages", [])

    if not messages:
        return {"retrieved_documents": [], "context": ""}

    last_message = messages[-1]

    query = getattr(last_message, "content", "")

    if not isinstance(query, str):
        query = extract_message_content(last_message)

    documents = retrieve_documents(query)
    context = format_context(documents)

    return {"retrieved_documents": documents, "context": context}


# ============================================================
# GENERATE NODE
# ============================================================

def generate_node(state: RAGState):

    messages = state.get("messages", [])

    if not messages:

        answer = "Please provide a question."

        return {"messages": [AIMessage(content=answer)], "answer": answer}

    last_message = messages[-1]

    query = getattr(last_message, "content", "")

    if not isinstance(query, str):
        query = extract_message_content(last_message)

    context = state.get("context", "")

    user_prompt = f"""
HANDBOOK CONTEXT
================

{context}


USER QUESTION
=============

{query}


INSTRUCTIONS
============

Answer the user question using only the handbook context above.

If the answer cannot be found in the context, say that the
information could not be found in the Horizon Trails Company
Handbook.

Preserve every number, amount, currency, and threshold from the
context exactly as written. Include the relevant section/page
when possible.
"""

    # retrieve_node (which always runs first) already triggered
    # lazy setup, but this call is defensive in case generate_node
    # is ever invoked on its own.
    resources = get_rag_resources()

    answer = ""

    # --------------------------------------------------------
    # LOCK: only one .stream() call on the shared rag_model
    # client at a time, across every concurrent request. This
    # prevents two simultaneous requests' streamed tokens from
    # being interleaved into the same answer (see
    # _RAG_STREAM_LOCK above for why this is necessary).
    # --------------------------------------------------------

    with _RAG_STREAM_LOCK:

        for chunk in resources.rag_model.stream([
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]):

            # Use extract_stream_delta (NOT extract_message_content)
            # here - the latter calls .strip() on every individual
            # chunk, which deletes the leading space that separates
            # streamed words and glues the whole answer together
            # ("Thecancellationcharge...").

            text = extract_stream_delta(chunk)

            if text:
                answer += text

    # Strip ONLY the fully-assembled answer, once, at the end.
    answer = answer.strip()

    if not answer:
        answer = "I could not generate an answer."

    return {"messages": [AIMessage(content=answer)], "answer": answer}


# ============================================================
# BUILD RAG LANGGRAPH
#
# Wiring nodes/edges together is cheap (no model/FAISS work
# happens here), so this stays at module level exactly like
# before — it's only the resources the nodes *use* that are now
# lazy.
# ============================================================

def build_rag_graph():

    graph = StateGraph(RAGState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


rag_graph = build_rag_graph()

rag_graph_builder = rag_graph


# ============================================================
# PUBLIC CHATBOT FUNCTION
# ============================================================

def chatbot(query: str) -> str:

    if not query or not query.strip():
        return "Please enter a question."

    result = rag_graph_builder.invoke({
        "messages": [HumanMessage(content=query.strip())],
        "retrieved_documents": [],
        "context": "",
        "answer": "",
    })

    return result.get("answer", "I could not generate an answer.")


# ============================================================
# OPTIONAL CLI MODE
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("HORIZON TRAILS COMPANY HANDBOOK RAG")
    print("=" * 60)
    print()
    print("Chunking priority:")
    print("  1. Section-based (regex on numbered headers)")
    print("  2. LLM semantic fallback -> ChatGroq ->", GROQ_MODEL)
    print("                            -> Gemini ->", GEMINI_MODEL)
    print("                            -> overlapping-window fallback")
    print()
    print("Retrieval: hybrid dense (FAISS) + BM25, RRF-fused, neighbor-expanded")
    print()
    print("Final RAG model:", RAG_MODEL)
    print("Embeddings: sentence-transformers/all-MiniLM-L6-v2")
    print("Vector store: FAISS")
    print("FAISS location:", FAISS_DIR)
    print("=" * 60)

    # CLI mode explicitly triggers setup up front so the first
    # question doesn't eat the (one-time) build/load cost silently.
    preload_rag_resources()