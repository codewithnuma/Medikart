# ============================================================
# views.py
# ============================================================

import json
import os
import tempfile
import threading
import uuid

from django.http import StreamingHttpResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from langchain_core.messages import HumanMessage, AIMessage

from .chatbot import graph, chat_stream
from .validation import Chatbot
from .models import ChatThread

# ============================================================
# GUARDRAILS
# ============================================================

from .guardrails import guardrail_service, output_security
from .guardrails.rate_limit import check_rate_limit
from .guardrails.exceptions import RateLimitExceeded


# ============================================================
# WHISPER MODEL — LOADED ONCE, NOT PER REQUEST
# ============================================================
#
# Switched "small" -> "base" and beam_size 5 -> 1, and turned
# on vad_filter. On CPU/int8 this is the single biggest lever
# on latency: "small" + beam_size=5 on a long clip is genuinely
# slow, and vad_filter skips the silent stretches instead of
# transcribing dead air.
#
# If you need better accuracy than "base" and have GPU/CPU
# headroom, "small" + vad_filter=True + beam_size=1 is a good
# middle ground — but "base" should already feel fast.
# ============================================================

_WHISPER_MODEL = None
_WHISPER_LOCK = threading.Lock()


def _get_whisper_model():

    global _WHISPER_MODEL

    if _WHISPER_MODEL is None:

        with _WHISPER_LOCK:

            if _WHISPER_MODEL is None:

                from faster_whisper import WhisperModel

                _WHISPER_MODEL = WhisperModel(
                    "base",
                    device="cpu",
                    compute_type="int8",
                )

    return _WHISPER_MODEL


def _transcribe_uploaded_audio(audio_file):
    """
    Transcribe a Django UploadedFile using the cached
    faster-whisper model. Returns plain text (may be "").
    """

    model = _get_whisper_model()

    suffix = os.path.splitext(audio_file.name)[1] or ".webm"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:

        for chunk in audio_file.chunks():
            temp_file.write(chunk)

        temp_audio_path = temp_file.name

    try:

        segments, info = model.transcribe(
            temp_audio_path,
            beam_size=1,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )

        text = "".join(
            segment.text for segment in segments
        ).strip()

    finally:

        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

    return text


# ============================================================
# STOP PHRASES — end voice mode without touching the LLM
# ============================================================
#
# The frontend loops mic -> agent -> speak -> mic again once
# you're in a voice turn. Ending that loop needs to be instant,
# not "wait for the LLM to answer a question that was actually
# just you saying goodbye". So this is checked right after
# transcription and, if it matches, we skip _run_agent
# entirely and hand back a fixed, fast reply plus a
# stop_voice_mode flag the frontend uses to break its loop.
#
# NOTE: this runs BEFORE guardrails deliberately — "stop" /
# "thanks" / "bye" are unambiguous, zero-risk, and treating them
# as a UX shortcut (not a security decision) keeps voice-mode
# exits instant even under guardrail load.
# ============================================================

STOP_PHRASES = (
    "stop",
    "please stop",
    "stop it",
    "that's all",
    "thats all",
    "that is all",
    "that's it",
    "thats it",
    "thank you",
    "thanks",
    "thank you, that's all",
    "cancel",
    "goodbye",
    "bye",
    "no more questions",
    "i'm done",
    "im done",
    "i am done",
    "nothing else",
    "no thanks",
    "no thank you",
)


def _is_stop_phrase(text):

    normalized = " ".join(str(text or "").strip().lower().split())
    normalized = normalized.rstrip(".!?")

    if not normalized:
        return False

    if normalized in STOP_PHRASES:
        return True

    # Catch short trailing variants like "ok stop" / "alright, thank you"
    return any(
        normalized.endswith(" " + phrase) for phrase in STOP_PHRASES
    )


# ============================================================
# HELPERS
# ============================================================

def _jwt_from_request(request):

    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None


def _extract_text(content):

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

    return str(content or "")


def _make_title(message, max_length=50):

    title = " ".join(str(message).strip().split())

    if not title:
        return "New Conversation"

    if len(title) > max_length:
        title = title[:max_length].rstrip() + "..."

    return title


# ============================================================
# GUARDRAIL HELPERS
# ============================================================

def _client_identifier(request, jwt_token):
    """
    Best-effort identifier for rate limiting / security logging,
    usable BEFORE identity resolution (which needs a DB hit).
    Falls back to client IP for guests.
    """

    if jwt_token:
        return "jwt:" + jwt_token[-24:]

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

    ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else request.META.get("REMOTE_ADDR", "unknown")
    )

    return "ip:" + ip


def _rate_limit_response(exc: RateLimitExceeded):

    response = Response(
        {
            "error": "rate_limited",
            "message": "Too many requests. Please slow down and try again shortly.",
        },
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )

    response["Retry-After"] = str(exc.retry_after_seconds)

    return response


def _guardrail_blocked_response(guard_result, thread_id=None):

    return Response(
        {
            "error": "guardrail_blocked",
            "category": guard_result.get("category", "blocked"),
            "message": guard_result.get("message", "I can't help with that request."),
            "thread_id": thread_id or "",
        },
        status=status.HTTP_400_BAD_REQUEST,
    )




def _resolve_identity_and_thread(question, jwt_token, thread_id):

    chatbot = Chatbot(jwt_token=jwt_token, thread_id=thread_id)
    identity = chatbot.get_identity()

    thread_id = identity["thread_id"]

    if identity["authenticated"]:

        user_id = identity["user_id"]

        thread, created = ChatThread.objects.get_or_create(
            thread_id=thread_id,
            defaults={
                "user_id": user_id,          # <- adjust field name here if needed
                "title": _make_title(question),
            },
        )

        if not created:

            if thread.user_id != user_id:
                # Extremely unlikely uuid4 collision across users —
                # don't let it silently attach to someone else's thread.
                thread_id = str(uuid.uuid4())
                identity["thread_id"] = thread_id

                ChatThread.objects.create(
                    thread_id=thread_id,
                    user_id=user_id,          # <- adjust field name here if needed
                    title=_make_title(question),
                )

            else:
                thread.save(update_fields=["updated_at"])

    return identity, thread_id


def _run_agent(question, jwt_token, thread_id, identity):
    """
    Shared by ChatView and VoiceChatView: invoke the graph and
    pull the final assistant text out of it.
    """

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = graph.invoke(
        {
            "messages": [
                HumanMessage(content=question)
            ],
            "jwt_token": jwt_token,
            "identity": identity,
        },
        config=config,
    )

    messages = response.get("messages", [])

    answer = ""

    for message in reversed(messages):

        if isinstance(message, AIMessage):

            answer = _extract_text(message.content)

            if answer:
                break

    return answer


# ============================================================
# NORMAL CHAT (TEXT)
# ============================================================

class ChatView(APIView):

    def post(self, request):

        question = request.data.get("message", "").strip()

        if not question:
            return Response(
                {"error": "Message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jwt_token = (
            request.data.get("jwt_token")
            or _jwt_from_request(request)
        )

        thread_id = request.data.get("thread_id")

        identifier = _client_identifier(request, jwt_token)

        # --------------------------------------------------
        # GUARDRAILS: rate limit
        # --------------------------------------------------

        try:
            check_rate_limit(identifier, authenticated=bool(jwt_token))
        except RateLimitExceeded as exc:
            return _rate_limit_response(exc)



        guard_result = guardrail_service.check_input(
            question,
            user_id=identifier,
            authenticated=bool(jwt_token),
            endpoint="/api/chat/chat/",
        )

        if guard_result["action"] == "simple":
            return Response(
                {
                    "answer": guard_result["response"],
                    "thread_id": thread_id or "",
                    "identity": None,
                },
                status=status.HTTP_200_OK,
            )

        if guard_result["action"] == "block":
            return _guardrail_blocked_response(guard_result, thread_id)

        # --------------------------------------------------
        # Existing logic — unchanged
        # --------------------------------------------------

        try:

            identity, thread_id = _resolve_identity_and_thread(
                question, jwt_token, thread_id,
            )

            answer = _run_agent(
                question, jwt_token, thread_id, identity
            )

            # ------------------------------------------------
            # GUARDRAILS: output pipeline (secret redaction +
            # NeMo policy check)
            # ------------------------------------------------

            safe_answer, _was_modified = guardrail_service.check_output(
                answer,
                user_id=identifier,
                endpoint="/api/chat/chat/",
            )

            return Response(
                {
                    "answer": safe_answer,
                    "thread_id": thread_id,
                    "identity": identity,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e),
                    "thread_id": thread_id,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# STREAMING CHAT (TEXT)  (FIXED)
#
# WHAT WAS WRONG
# --------------
# event_stream() fed BOTH `token` and `node` events into the SAME
# StreamingRedactor. The redactor holds back the last ~120 chars,
# so a short reply ("You are identified as a pharmacy user.") was
# held back completely while the tokens arrived; the `node` event
# with the same sentence was then fed in behind it, and
# redactor.flush() sent everything as ONE token:
#
#     "You are identified as a pharmacy user.You are identified
#      as a pharmacy user."
#
# WHAT THIS VERSION DOES
# ----------------------
# * Only `token` events go through the redactor; any `node` event
#   that still arrives is dropped (chat_stream no longer sends
#   duplicates, and sends the no-LLM fallback as a normal token).
# * The redactor tail is flushed BEFORE the `done` / `error` event,
#   so the browser has the full text when it sees `done`.
# * The tail is flushed at most once, whatever path ends the stream.
# ============================================================

class ChatStreamView(APIView):

    def post(self, request):

        question = request.data.get("message", "").strip()

        if not question:
            return Response(
                {"error": "Message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jwt_token = (
            request.data.get("jwt_token")
            or _jwt_from_request(request)
        )

        thread_id = request.data.get("thread_id")

        identifier = _client_identifier(request, jwt_token)

        # --------------------------------------------------
        # GUARDRAILS: rate limit — BEFORE opening any stream
        # --------------------------------------------------

        try:
            check_rate_limit(identifier, authenticated=bool(jwt_token))
        except RateLimitExceeded as exc:
            return _rate_limit_response(exc)

        # --------------------------------------------------
        # GUARDRAILS: input pipeline — BEFORE opening any
        # stream. A blocked/simple request never reaches
        # graph.stream(), satisfying "blocked requests must
        # not start LLM streaming".
        # --------------------------------------------------

        guard_result = guardrail_service.check_input(
            question,
            user_id=identifier,
            authenticated=bool(jwt_token),
            endpoint="/api/chat/chat/stream/",
        )

        if guard_result["action"] == "simple":

            def simple_stream():

                yield "data: " + json.dumps(
                    {"type": "token", "content": guard_result["response"], "thread_id": thread_id or ""}
                ) + "\n\n"

                yield "data: " + json.dumps(
                    {"type": "done", "thread_id": thread_id or ""}
                ) + "\n\n"

                yield "data: [DONE]\n\n"

            response = StreamingHttpResponse(
                simple_stream(), content_type="text/event-stream",
            )
            response["Cache-Control"] = "no-cache"
            response["X-Accel-Buffering"] = "no"
            return response

        if guard_result["action"] == "block":
            return _guardrail_blocked_response(guard_result, thread_id)

        # --------------------------------------------------
        # Existing logic — unchanged
        # --------------------------------------------------

        try:

            identity, thread_id = _resolve_identity_and_thread(
                question, jwt_token, thread_id,
            )

        except Exception as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        def event_stream():

            # GUARDRAILS: streaming-safe secret redactor. Holds a
            # small rolling buffer (~120 chars) so a secret split
            # across two token chunks can't slip through, while
            # still emitting tokens incrementally (real streaming
            # is preserved).
            redactor = output_security.StreamingRedactor()

            tail_flushed = False

            def flush_tail_event():
                """
                Returns the SSE line for whatever the redactor is
                still holding back, or None. Runs at most once.
                """

                nonlocal tail_flushed

                if tail_flushed:
                    return None

                tail_flushed = True

                tail = redactor.flush()

                if not tail:
                    return None

                return "data: " + json.dumps(
                    {"type": "token", "content": tail, "thread_id": thread_id}
                ) + "\n\n"

            try:

                for event in chat_stream(
                    question,
                    jwt_token=jwt_token,
                    thread_id=thread_id,
                ):

                    event_type = event.get("type")

                    # ------------------------------------------
                    # `node` events repeat text that is already
                    # streamed as tokens. They must NEVER reach
                    # the redactor or the browser.
                    # ------------------------------------------

                    if event_type == "node":
                        continue

                    # ------------------------------------------
                    # Tokens: the only events that are redacted.
                    # ------------------------------------------

                    if event_type == "token":

                        if event.get("content"):

                            safe_chunk = redactor.feed(event["content"])

                            if safe_chunk:
                                yield "data: " + json.dumps(
                                    dict(event, content=safe_chunk)
                                ) + "\n\n"

                        continue

                    # ------------------------------------------
                    # done / error: release the held-back tail
                    # FIRST, so the browser has the complete
                    # text by the time it sees the terminal event.
                    # ------------------------------------------

                    if event_type in ("done", "error"):

                        tail_line = flush_tail_event()

                        if tail_line:
                            yield tail_line

                    yield "data: " + json.dumps(event) + "\n\n"

                # Stream ended without a done/error event.
                tail_line = flush_tail_event()

                if tail_line:
                    yield tail_line

            except Exception as e:

                tail_line = flush_tail_event()

                if tail_line:
                    yield tail_line

                error_event = {
                    "type": "error",
                    "error": str(e),
                    "thread_id": thread_id,
                }

                yield "data: " + json.dumps(error_event) + "\n\n"

            finally:

                yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )

        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"

        return response


# ============================================================
# VOICE → TEXT ONLY (kept for compatibility / other uses)
# ============================================================

class VoiceToTextView(APIView):

    def post(self, request):

        audio = request.FILES.get("audio")

        if not audio:
            return Response(
                {"error": "Audio file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size = 25 * 1024 * 1024  # 25 MB

        if audio.size > max_size:
            return Response(
                {"error": "Audio file is too large. Maximum size is 25 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            text = _transcribe_uploaded_audio(audio)

        except Exception as e:

            return Response(
                {"error": "Speech recognition failed: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not text:
            return Response(
                {"error": "Could not understand the audio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"text": text}, status=status.HTTP_200_OK)


# ============================================================
# VOICE → AGENT, ONE SHOT
# ============================================================
#
#   POST /api/chat/voice-chat/
#   multipart/form-data:
#       audio      = recorded clip
#       thread_id  = optional, resumes a conversation
#       jwt_token  = optional, for logged-in users
#
# Transcribes the clip AND runs it through the agent in a
# single request. If the transcript is just you saying
# "stop" / "thank you" / etc, the agent is skipped entirely —
# stop_voice_mode: true tells the frontend to break its
# listen-loop instead of looping again.
#
# Voice transcription is untrusted input — it goes through the
# exact same guardrail pipeline as typed text, AFTER the
# stop-phrase shortcut (which is a UX check, not a security
# check) and AFTER rate limiting.
# ============================================================

class VoiceChatView(APIView):

    def post(self, request):

        audio = request.FILES.get("audio")

        if not audio:
            return Response(
                {"error": "Audio file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size = 25 * 1024 * 1024  # 25 MB

        if audio.size > max_size:
            return Response(
                {"error": "Audio file is too large. Maximum size is 25 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        jwt_token = (
            request.data.get("jwt_token")
            or _jwt_from_request(request)
        )

        thread_id = request.data.get("thread_id")

        identifier = _client_identifier(request, jwt_token)

        # --------------------------------------------------
        # GUARDRAILS: rate limit — before spending time on
        # Whisper transcription.
        # --------------------------------------------------

        try:
            check_rate_limit(identifier, authenticated=bool(jwt_token))
        except RateLimitExceeded as exc:
            return _rate_limit_response(exc)

        try:
            question = _transcribe_uploaded_audio(audio)

        except Exception as e:

            return Response(
                {"error": "Speech recognition failed: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not question:

            return Response(
                {"error": "Could not understand the audio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Stop phrase -> skip guardrails + LLM, end voice mode fast
        # ----------------------------------------------------

        if _is_stop_phrase(question):

            return Response(
                {
                    "question": question,
                    "answer": "Okay, ending voice mode. Let me know whenever you need anything else!",
                    "thread_id": thread_id or "",
                    "identity": None,
                    "stop_voice_mode": True,
                },
                status=status.HTTP_200_OK,
            )

        # --------------------------------------------------
        # GUARDRAILS: input pipeline — transcribed speech is
        # untrusted, same as typed text.
        # --------------------------------------------------

        guard_result = guardrail_service.check_input(
            question,
            user_id=identifier,
            authenticated=bool(jwt_token),
            endpoint="/api/chat/voice-chat/",
        )

        if guard_result["action"] == "simple":
            return Response(
                {
                    "question": question,
                    "answer": guard_result["response"],
                    "thread_id": thread_id or "",
                    "identity": None,
                    "stop_voice_mode": False,
                },
                status=status.HTTP_200_OK,
            )

        if guard_result["action"] == "block":
            blocked = _guardrail_blocked_response(guard_result, thread_id)
            blocked.data["stop_voice_mode"] = False
            return blocked

        try:

            identity, thread_id = _resolve_identity_and_thread(
                question, jwt_token, thread_id,
            )

            answer = _run_agent(
                question, jwt_token, thread_id, identity
            )

            # ------------------------------------------------
            # GUARDRAILS: output pipeline
            # ------------------------------------------------

            safe_answer, _was_modified = guardrail_service.check_output(
                answer,
                user_id=identifier,
                endpoint="/api/chat/voice-chat/",
            )

            return Response(
                {
                    "question": question,
                    "answer": safe_answer,
                    "thread_id": thread_id,
                    "identity": identity,
                    "stop_voice_mode": False,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e),
                    "thread_id": thread_id,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# THREAD LIST
# ============================================================

class ThreadListView(APIView):

    def get(self, request):

        # ----------------------------------------------------
        # Get JWT from Authorization header
        # ----------------------------------------------------

        jwt_token = _jwt_from_request(request)

        try:

            # ------------------------------------------------
            # Identify logged-in user
            # ------------------------------------------------

            chatbot = Chatbot(jwt_token=jwt_token)
            identity = chatbot.get_identity()

            print()
            print("=" * 70)
            print("THREAD LIST REQUEST")
            print("=" * 70)

            print("Authenticated:", identity.get("authenticated"))
            print("User ID:", identity.get("user_id"))
            print("Username:", identity.get("username"))
            print("Email:", identity.get("email"))

            # ------------------------------------------------
            # Authentication check
            # ------------------------------------------------

            if not identity["authenticated"]:

                print("USER NOT AUTHENTICATED")
                print("=" * 70)

                return Response(
                    {
                        "error": "Authentication required.",
                        "threads": [],
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user_id = str(identity["user_id"])

            print("Looking for threads owned by:", user_id)

            # ------------------------------------------------
            # DEBUG: Show ALL threads in PostgreSQL
            # ------------------------------------------------

            all_threads = ChatThread.objects.all()

            print()
            print("TOTAL THREADS IN DATABASE:", all_threads.count())

            for thread in all_threads:

                print(
                    "THREAD:",
                    thread.thread_id,
                    "| USER_ID:",
                    thread.user_id,
                    "| TITLE:",
                    thread.title,
                )

            # ------------------------------------------------
            # Get threads belonging to this user
            # ------------------------------------------------

            threads = (
                ChatThread.objects
                .filter(user_id=user_id)
                .order_by("-updated_at")
            )

            print()
            print(
                "THREADS FOR USER",
                user_id,
                ":",
                threads.count()
            )

            # ------------------------------------------------
            # Build response
            # ------------------------------------------------

            data = []

            for thread in threads:

                data.append(
                    {
                        "thread_id": thread.thread_id,
                        "title": thread.title,
                        "created_at": thread.created_at,
                        "updated_at": thread.updated_at,
                    }
                )

            print()
            print("RETURNING THREADS:", len(data))
            print("=" * 70)
            print()

            return Response(
                {
                    "threads": data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            print()
            print("=" * 70)
            print("THREAD LIST ERROR")
            print("=" * 70)
            print(str(e))
            print("=" * 70)
            print()

            return Response(
                {
                    "error": str(e),
                    "threads": [],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# THREAD HISTORY
# ============================================================

class ThreadHistoryView(APIView):

    def get(self, request, thread_id):

        jwt_token = _jwt_from_request(request)

        try:

            chatbot = Chatbot(jwt_token=jwt_token)
            identity = chatbot.get_identity()

            if not identity["authenticated"]:

                return Response(
                    {"error": "Authentication required."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            thread = ChatThread.objects.filter(
                thread_id=thread_id,
                user_id=identity["user_id"],   # <- adjust field name here if needed
            ).first()

            if not thread:

                return Response(
                    {"error": "Thread not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }

            state = graph.get_state(config)

            values = state.values or {}

            messages = values.get("messages", [])

            history = []

            for message in messages:

                if isinstance(message, HumanMessage):

                    history.append(
                        {
                            "role": "user",
                            "content": _extract_text(message.content),
                        }
                    )

                elif isinstance(message, AIMessage):

                    history.append(
                        {
                            "role": "assistant",
                            "content": _extract_text(message.content),
                        }
                    )

            return Response(
                {
                    "thread_id": thread_id,
                    "title": thread.title,
                    "messages": history,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
# ============================================================
# ADD TO the chatbot server's views.py
# (add the imports at the top, the class at the bottom)
# ============================================================

import hmac
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .pharmacy_license_graph import run_pharmacy_verification


def _internal_key_ok(request) -> bool:
    """Server-to-server only: the main backend sends X-Internal-Key."""

    expected = os.getenv("INTERNAL_API_KEY", "")
    provided = request.headers.get("X-Internal-Key", "")

    if not expected:
        return False

    return hmac.compare_digest(expected.encode(), provided.encode())

# ============================================================
# ADD TO the chatbot server's views.py
# (add the imports at the top, the class at the bottom)
# ============================================================

import hmac
import logging
import os

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .pharmacy_license_graph import run_pharmacy_verification

logger = logging.getLogger(__name__)


def _expected_internal_key() -> str:

    return (
        getattr(settings, "INTERNAL_API_KEY", "")
        or os.getenv("INTERNAL_API_KEY", "")
        or ""
    ).strip()


def _internal_key_ok(request) -> bool:
    """Server-to-server only: the main backend sends X-Internal-Key."""

    expected = _expected_internal_key()
    provided = (request.headers.get("X-Internal-Key", "") or "").strip()

    if not expected:
        logger.error("INTERNAL_API_KEY is NOT set on the chatbot server.")
        return False

    if not provided:
        logger.error("Request had no X-Internal-Key header (main backend key is empty).")
        return False

    if not hmac.compare_digest(expected.encode(), provided.encode()):
        logger.error(
            "X-Internal-Key mismatch (chatbot key length=%s, received length=%s).",
            len(expected),
            len(provided),
        )
        return False

    return True


# ============================================================
# PHARMACY REGISTRATION VERIFICATION
#
#   POST /api/chat/pharmacy-verify/
#   Header: X-Internal-Key: <INTERNAL_API_KEY>
#   JSON:   {
#             "registration_id": 12,
#             "username": "City Pharmacy",
#             "email": "city@example.com",
#             "phone_number": "98XXXXXXXX",
#             "license_no": "G6432"
#           }
#
#   Runs the LangGraph agent:
#   verify -> create user -> LLM email -> send email
# ============================================================

class PharmacyVerifyView(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        if not _internal_key_ok(request):
            return Response(
                {"error": "Unauthorized."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        registration_id = request.data.get("registration_id")
        email = str(request.data.get("email") or "").strip()

        if not registration_id or not email:
            return Response(
                {"error": "registration_id and email are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            result = run_pharmacy_verification(
                registration_id=registration_id,
                username=str(request.data.get("username") or ""),
                email=email,
                license_no=str(request.data.get("license_no") or ""),
                phone_number=str(request.data.get("phone_number") or ""),
            )

        except Exception as exc:

            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_200_OK)


# ============================================================
# ADD TO the chatbot server's urls.py
#
#   from .views import PharmacyVerifyView
#
#   urlpatterns = [
#       ...
#       path("pharmacy-verify/", PharmacyVerifyView.as_view()),
#   ]
# ============================================================