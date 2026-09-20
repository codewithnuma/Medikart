import React, { useEffect, useRef, useState, useCallback } from "react";
import { Outlet } from "react-router-dom";
import axios from "axios";
import {
  MessageOutlined,
  SendOutlined,
  RobotOutlined,
  PlusOutlined,
  MenuOutlined,
  CloseOutlined,
  AudioOutlined,
  AudioMutedOutlined,
  SoundOutlined,
} from "@ant-design/icons";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import axiosInstance from "../axiosInstance";
import { useAuth } from "../context/AuthContext";

import "./Chatbot.css";


/* ============================================================
   CHATBOT API
   ============================================================ */

const CHATBOT_API_BASE = "http://127.0.0.1:8001/api/chat";

// ngrok's free tier injects an HTML "you're about to visit an
// ngrok tunnel" interstitial for any plain browser request that
// doesn't carry this header. Without it, every request here
// (axios AND raw fetch) gets back that warning page instead of
// JSON/SSE, which the browser then reports as a CORS failure.
const NGROK_SKIP_HEADER = { "ngrok-skip-browser-warning": "true" };

const chatbotAxios = axios.create({
  baseURL: CHATBOT_API_BASE,
  headers: {
    ...NGROK_SKIP_HEADER,
  },
});


/* ============================================================
   VOICE CONFIG
   ============================================================ */

const WAKE_PHRASES = ["siri", "hi siri", "hey siri", "avengers assemble"];

const STOP_WORDS_LOCAL = [
  "stop",
  "thank you",
  "thanks",
  "that's all",
  "thats all",
  "cancel",
  "goodbye",
  "bye",
];

// How long a fetched JWT is trusted before we quietly refresh it
// in the background. Keep this comfortably under the backend's
// actual token TTL — adjust if you know the real expiry.
//
// NOTE: this is only a client-side heuristic. If the real backend
// expiry is shorter than this (or the token is invalidated some
// other way), a request can still come back 401 even though the
// cache thinks the token is "fresh". That's what the 401-retry
// logic in fetchThreadsFromBackend()/loadThreadMessages() below
// is for — don't rely on this constant alone for correctness.
const JWT_CACHE_TTL_MS = 1000;

// How long after the user stops talking (no new recognition
// results) before we treat their turn as finished and send it.
// This is transcript-based (not volume-based like the old audio
// pipeline), so it's reliable enough to keep short for snappy
// turn-taking.
const TURN_SILENCE_MS = 700;

// Minimum characters of speech heard before we treat it as a real
// barge-in attempt rather than a stray noise or recognition blip.
const INTERRUPT_MIN_CHARS = 3;

// Small breathing gap between spoken sentences — reads much more
// like a person pausing than one flat run-on utterance.
const INTER_SENTENCE_GAP_MS = 60;

// ------------------------------------------------------------
// SELF-ECHO FILTERING
//
// SpeechRecognition has no concept of "ignore my own speaker
// output" — without headphones, the mic hears speechSynthesis
// just like it hears the user, so the old code could interrupt
// or "finalize a turn" based on the bot's OWN voice ("how can I
// help you" got heard back and treated as if the user said it).
//
// Fix: we always know exactly what text is currently queued/
// playing through speechSynthesis (spokenReferenceTextRef below).
// Every new recognition result is compared against that text; if
// most of its words already appear in what the bot is saying,
// it's discarded as an echo instead of being treated as human
// speech. Very short utterances (<=2 words) skip this check
// entirely so real one/two-word commands like "stop" are never
// swallowed just because the bot's reply happens to contain that
// word somewhere.
// ------------------------------------------------------------

const ECHO_OVERLAP_RATIO_THRESHOLD = 0.6;
const ECHO_MIN_WORDS_TO_CHECK = 3;

const SpeechRecognitionCtor =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

const speechSynthesisSupported =
  typeof window !== "undefined" && "speechSynthesis" in window;

// Strip the markdown the bot's text answers usually contain,
// so it doesn't get read aloud as literal asterisks/hashes.
const stripMarkdownForSpeech = (text) =>
  String(text || "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[[^\]]*]\([^)]*\)/g, "")
    .replace(/\[([^\]]+)]\([^)]*\)/g, "$1")
    .replace(/[*_#>~-]/g, "")
    .replace(/\s+/g, " ")
    .trim();

// Lowercase, punctuation-stripped word list — used only for the
// echo-overlap comparison below, never for anything user-facing.
const normalizeForCompare = (text) =>
  String(text || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

// True if `candidateText` looks like it's just the mic picking up
// `referenceText` (whatever the bot is currently speaking) rather
// than something a human said. Deliberately conservative: it only
// fires when most of the candidate's words are already present in
// the bot's own speech, and never for very short candidates (so
// real short commands like "stop"/"cancel" always get through).
const isLikelySelfEcho = (candidateText, referenceText) => {

  const candidateWords = normalizeForCompare(candidateText);

  if (candidateWords.length < ECHO_MIN_WORDS_TO_CHECK) {
    return false;
  }

  const referenceWords = normalizeForCompare(referenceText);

  if (referenceWords.length === 0) {
    return false;
  }

  const referenceSet = new Set(referenceWords);

  const overlapCount = candidateWords.filter((word) =>
    referenceSet.has(word)
  ).length;

  return (
    overlapCount / candidateWords.length >= ECHO_OVERLAP_RATIO_THRESHOLD
  );
};

// Picks the most natural-sounding voice actually installed in this
// browser/OS. True human-quality TTS needs a cloud neural voice
// (ElevenLabs, Azure, Google Cloud TTS) — this just does the best
// with whatever system voices are available.
const VOICE_PREFERENCE_PATTERNS = [
  /Natural/i,
  /Neural/i,
  /Premium/i,
  /Enhanced/i,
  /Google US English/i,
  /Google UK English Female/i,
  /Samantha/i,
  /Aria/i,
  /Jenny/i,
  /Daniel/i,
  /Karen/i,
];

const pickBestVoice = (voices) => {

  if (!voices || voices.length === 0) return null;

  for (const pattern of VOICE_PREFERENCE_PATTERNS) {
    const match = voices.find((v) => pattern.test(v.name));
    if (match) return match;
  }

  return (
    voices.find((v) => v.lang === "en-US") ||
    voices.find((v) => (v.lang || "").startsWith("en")) ||
    voices[0]
  );
};


/* ============================================================
   CREATE UUID / MESSAGE ID
   ============================================================ */

const createThreadId = () => {
  if (crypto?.randomUUID) {
    return crypto.randomUUID();
  }

  return (
    Date.now().toString(36) +
    Math.random().toString(36).substring(2)
  );
};

// Every chat bubble gets its own id so a streaming reply always
// updates ITS OWN bubble. Previously the stream wrote into
// "whatever the last message in the array is", which is fragile —
// anything else that appends a message mid-stream (e.g. the
// wake-word greeting) would get its text overwritten.
const createMessageId = () =>
  Date.now().toString(36) + "-" + Math.random().toString(36).substring(2);


/* ============================================================
   GUARDRAIL / ERROR RESPONSE HELPERS
   ============================================================

   The backend now returns structured JSON (not an SSE stream)
   when a request is:
     - blocked by a guardrail  -> 400 { error: "guardrail_blocked", category, message }
     - rate limited            -> 429 { error: "rate_limited", message }
   Both still arrive on the SAME /chat/stream/ endpoint, so the
   streaming fetch handlers below check response.ok BEFORE trying
   to read the body as a stream, and surface the real message to
   the user instead of a generic "Server error".
   ============================================================ */

const FALLBACK_ERROR_MESSAGE = "Server error. Please try again.";

// Reads a non-OK response as JSON and returns a user-facing
// message. Never throws — always resolves to *some* string.
const extractErrorMessage = async (response) => {

  try {

    const data = await response.json();

    if (response.status === 429) {
      return data?.message || "You're sending messages too fast. Please wait a moment and try again.";
    }

    if (data?.message) return data.message;
    if (data?.error) return String(data.error);

  } catch (parseError) {
    // Body wasn't JSON (e.g. a raw 5xx HTML page) — fall through.
  }

  return FALLBACK_ERROR_MESSAGE;
};


/* ============================================================
   SSE STREAM READER  (THE FIX for duplicated / stale text)
   ============================================================

   The backend emits two kinds of content events on the stream:

     { type: "token", content }  -> the reply, streamed piece by piece
     { type: "node",  content }  -> a whole message emitted by a graph
                                    node (used by routes such as
                                    "direct_tool")

   The old code did this:

       node  -> if (!botText) botText = content
       token -> botText += content        <-- appended onto the node text

   So whenever a node event arrived FIRST, its text became the
   start of the bubble and every following token was appended
   on top of it:

     * node text == the answer      ->  "Your role is pharmacy.Your role is pharmacy."
     * node text == the PREVIOUS    ->  "<old fever answer>Your role is pharmacy."
       assistant message (stale)

   The saved history in the database only ever held the single
   correct answer, which is why a page refresh (which reloads
   history from the server) "fixed" it.

   Rules now:
     1. Tokens are the source of truth. They build tokenText on
        their own and are NEVER appended to node text.
     2. Node text is only a fallback: it is shown while no token
        has arrived yet, and is discarded the moment the first
        token shows up.
     3. Whatever the final text is, it is exactly ONE of the two,
        never a mix of both.
   ============================================================ */

const consumeChatStream = async (response, handlers = {}) => {

  const { onToken, onNode, onDone, onStreamError } = handlers;

  if (!response.body) {
    throw new Error("Stream response had no body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";
  let tokenText = "";
  let nodeText = "";
  let hadError = false;

  const handleRawEvent = (rawEvent) => {

    // An SSE event can span several lines (e.g. "event: x" then
    // "data: {...}"), so collect every data: line instead of
    // requiring the whole event to start with "data:".
    const dataStr = rawEvent
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trim())
      .join("\n");

    if (!dataStr || dataStr === "[DONE]") return;

    let event;
    try {
      event = JSON.parse(dataStr);
    } catch (parseError) {
      console.error("Failed to parse SSE event:", dataStr, parseError);
      return;
    }

    if (event.type === "token") {

      const chunk = event.content || "";
      if (!chunk) return;

      tokenText += chunk;
      if (onToken) onToken(chunk, tokenText);

    } else if (event.type === "node") {

      // Fallback only — ignored as soon as real tokens exist.
      if (!tokenText && event.content) {
        nodeText = event.content;
        if (onNode) onNode(nodeText);
      }

    } else if (event.type === "done") {

      if (onDone) onDone(event);

    } else if (event.type === "error") {

      hadError = true;
      console.error("Stream error event:", event.error);
      if (onStreamError) onStreamError(event.error);
    }
  };

  while (true) {

    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    buffer = buffer.replace(/\r\n/g, "\n");

    const rawEvents = buffer.split("\n\n");
    buffer = rawEvents.pop() || "";

    rawEvents.forEach(handleRawEvent);
  }

  // Flush anything left over (a final event with no trailing
  // blank line would otherwise be silently dropped).
  buffer += decoder.decode();
  if (buffer.trim()) handleRawEvent(buffer.replace(/\r\n/g, "\n"));

  return {
    tokenText,
    nodeText,
    finalText: tokenText || nodeText,
    usedNodeFallback: !tokenText && !!nodeText,
    hadError,
  };
};


/* ============================================================
   CHATBOT
   ============================================================ */

const Chatbot = () => {

  const { user, isAuthenticated, loading } = useAuth();

  const [isOpen, setIsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingThreads, setIsLoadingThreads] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const [threads, setThreads] = useState([]);
  const [activeThreadId, setActiveThreadId] = useState(null);

  /* ---------------- VOICE STATE ---------------- */

  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [wakeWordEnabled, setWakeWordEnabled] = useState(true);

  // Persistent "voice conversation" mode. While true, the mic is
  // continuously listening — through the bot thinking AND speaking
  // — so the user can interrupt at any point, and it self-restarts
  // if the browser ever silently drops it. Ends on a stop phrase or
  // clicking the mic.
  const [voiceModeActive, setVoiceModeActive] = useState(false);
  const voiceModeActiveRef = useRef(false);

  const micSupported =
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices &&
    !!navigator.mediaDevices.getUserMedia;

  // Both the wake-word listener and voice-mode dictation run on the
  // Web Speech API, so both features share this one capability flag.
  const speechRecognitionSupported = !!SpeechRecognitionCtor;

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const wakeRecognitionRef = useRef(null);
  const wakeWordEnabledRef = useRef(wakeWordEnabled);

  const voicesRef = useRef([]);

  // ---- JWT cache: avoids re-hitting the token endpoint on every
  // single voice/text turn.
  const jwtCacheRef = useRef({ token: null, expiresAt: 0 });
  const jwtFetchPromiseRef = useRef(null);

  // ---- Mirrors of state that long-lived listeners (the
  // continuous dictation recognizer, in particular) need to read
  // fresh values from without being recreated every render.
  const activeThreadIdRef = useRef(null);
  const isAuthenticatedRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isProcessingVoiceRef = useRef(false);

  // ---- Continuous voice-mode dictation.
  const dictationRecognitionRef = useRef(null);
  const turnTranscriptRef = useRef("");
  const interruptedThisTurnRef = useRef(false);
  const turnSilenceTimerRef = useRef(null);

  // ---- Spoken-reply queue + the in-flight streamed request.
  const ttsQueueRef = useRef([]);
  const voiceStreamAbortRef = useRef(null);

  // ---- Everything the bot is currently speaking or has queued to
  // speak THIS turn, kept in sync every time text is enqueued for
  // TTS. This is the reference the dictation recognizer compares
  // against to tell "the bot's own echoed voice" apart from real
  // human speech (see isLikelySelfEcho above).
  const spokenReferenceTextRef = useRef("");

  // ---- "Latest function" indirection so the dictation recognizer
  // (created once, long-lived) always calls the current closure
  // instead of a stale one from whichever render created it.
  const sendVoiceTextRef = useRef(() => { });
  const finalizeTurnRef = useRef(() => { });
  const cancelBotOutputRef = useRef(() => { });
  const enqueueSpeechRef = useRef(() => { });
  const processTtsQueueRef = useRef(() => { });

  useEffect(() => { wakeWordEnabledRef.current = wakeWordEnabled; }, [wakeWordEnabled]);
  useEffect(() => { voiceModeActiveRef.current = voiceModeActive; }, [voiceModeActive]);
  useEffect(() => { activeThreadIdRef.current = activeThreadId; }, [activeThreadId]);
  useEffect(() => { isAuthenticatedRef.current = isAuthenticated; }, [isAuthenticated]);
  useEffect(() => { isSpeakingRef.current = isSpeaking; }, [isSpeaking]);
  useEffect(() => { isProcessingVoiceRef.current = isProcessingVoice; }, [isProcessingVoice]);

  const setVoiceMode = (active) => {
    voiceModeActiveRef.current = active;
    setVoiceModeActive(active);
  };

  // Updates the text of ONE specific message by id. If the message
  // is gone (e.g. the user switched threads mid-stream) this is a
  // harmless no-op instead of overwriting some other bubble.
  const updateMessageText = useCallback((id, text) => {
    setMessages((previous) =>
      previous.map((message) =>
        message.id === id ? { ...message, text } : message
      )
    );
  }, []);


  /* ==========================================================
     JWT + THREADS
     ========================================================== */

  const fetchJWTFromBackend = async () => {

    try {
      const response = await axiosInstance.get("/accounts/rasa-token/");
      return response.data?.jwt_token || null;
    } catch (error) {
      // Logging the status here matters: a 401/403 from this call
      // means the MAIN app's session/access token is stale, which
      // is a completely different failure than the chat backend
      // rejecting a Rasa JWT later on. Knowing which one is
      // happening is the difference between "refresh the Rasa
      // token" and "refresh the app's own auth session".
      console.error(
        "Failed to get chatbot JWT:",
        error.response?.status,
        error.response?.data || error.message,
      );
      return null;
    }
  };

  // Cached + de-duplicated JWT getter. Returns instantly if a
  // still-fresh token is cached; if a fetch is already in flight,
  // awaits that same fetch instead of starting a second one.
  const ensureJwtToken = useCallback(({ forceRefresh = false } = {}) => {

    const cache = jwtCacheRef.current;
    const isFresh = cache.token && Date.now() < cache.expiresAt;

    if (isFresh && !forceRefresh) {
      return Promise.resolve(cache.token);
    }

    if (jwtFetchPromiseRef.current) {
      return jwtFetchPromiseRef.current;
    }

    const fetchPromise = fetchJWTFromBackend()
      .then((token) => {

        if (token) {
          jwtCacheRef.current = { token, expiresAt: Date.now() + JWT_CACHE_TTL_MS };
        } else {
          // A failed fetch must not leave a stale cached token
          // sitting around looking "fresh" to the next caller.
          jwtCacheRef.current = { token: null, expiresAt: 0 };
        }

        return token;
      })
      .finally(() => {
        jwtFetchPromiseRef.current = null;
      });

    jwtFetchPromiseRef.current = fetchPromise;
    return fetchPromise;

  }, []);

  // --------------------------------------------------------
  // Thread-list / history disappearing bug (already fixed)
  // --------------------------------------------------------
  //
  // Previously, both fetchThreadsFromBackend() and
  // loadThreadMessages() returned [] on ANY failure, including a
  // 401 from an expired chatbot JWT. Every caller then did
  // `setThreads(backendThreads)` / `setMessages(history)`
  // unconditionally, which meant a single stale-token failure
  // silently wiped the sidebar (or the open conversation) back
  // to empty, even though the user was still logged in and the
  // data still existed on the server. A full page refresh fixed
  // it only because it reset jwtCacheRef and forced a brand-new
  // token fetch from scratch.
  //
  // Now:
  //   1. Both functions return `null` (not []) when the request
  //      genuinely FAILED, so callers can tell "fetched, zero
  //      results" apart from "the fetch itself failed".
  //   2. On a 401 from the CHAT backend specifically, they force
  //      a fresh JWT (ensureJwtToken({ forceRefresh: true })) and
  //      retry ONCE before giving up, since a 401 on a
  //      client-cached "fresh" token almost always means the
  //      server-side expiry is shorter than our client-side guess.
  //   3. That retry only covers a 401 coming back from the chat
  //      backend itself. If ensureJwtToken() can't get a token AT
  //      ALL (step 1, `if (!token) return null`) — e.g. because
  //      the MAIN app's access token used by
  //      `axiosInstance.get("/accounts/rasa-token/")` has itself
  //      gone stale after a few minutes — that 401 never reaches
  //      this function, so the retry branch never fires. This is
  //      what was actually causing "thread visible, but clicking
  //      it shows nothing until I refresh": every click was
  //      silently hitting `if (!token) return null` on the FIRST
  //      attempt, with zero retry.
  //   4. Call sites (selectThread / initial load below) now retry
  //      ONE more time with a forced, clean token fetch whenever
  //      loadThreadMessages comes back null, and only fall back
  //      to an empty/error state if that second attempt also
  //      fails — instead of silently blanking the conversation.
  // --------------------------------------------------------

  const fetchThreadsFromBackend = async ({ forceRefresh = false } = {}) => {

    let token = await ensureJwtToken({ forceRefresh });

    if (!token) return null;

    try {

      const response = await chatbotAxios.get("/threads/", {
        headers: { Authorization: `Bearer ${token}` },
      });

      return response.data?.threads || [];

    } catch (error) {

      const status = error.response?.status;

      // Client-cached token looked "fresh" but the server
      // rejected it anyway — force a real refresh and retry once
      // before treating this as a genuine failure.
      if (status === 401 && !forceRefresh) {

        token = await ensureJwtToken({ forceRefresh: true });

        if (!token) return null;

        try {

          const retryResponse = await chatbotAxios.get("/threads/", {
            headers: { Authorization: `Bearer ${token}` },
          });

          return retryResponse.data?.threads || [];

        } catch (retryError) {

          console.error(
            "Failed to fetch threads (after token refresh):",
            retryError.response?.data || retryError.message,
          );

          return null;
        }
      }

      console.error("Failed to fetch threads:", error.response?.data || error.message);
      return null;
    }
  };

  const loadThreadMessages = async (threadId, { forceRefresh = false } = {}) => {

    let token = await ensureJwtToken({ forceRefresh });

    if (!token) return null;

    const mapMessages = (rawMessages) =>
      (rawMessages || []).map((message) => ({
        id: createMessageId(),
        sender: message.role === "user" ? "user" : "bot",
        text: message.content || "",
      }));

    try {

      const response = await chatbotAxios.get(`/threads/${threadId}/messages/`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Backend sends { role: "user" | "assistant", content: "..." }.
      // The UI renders { sender: "user" | "bot", text: "..." }.
      return mapMessages(response.data?.messages);

    } catch (error) {

      const status = error.response?.status;

      if (status === 401 && !forceRefresh) {

        token = await ensureJwtToken({ forceRefresh: true });

        if (!token) return null;

        try {

          const retryResponse = await chatbotAxios.get(`/threads/${threadId}/messages/`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          return mapMessages(retryResponse.data?.messages);

        } catch (retryError) {

          console.error(
            "Failed to load thread history (after token refresh):",
            retryError.response?.data || retryError.message,
          );

          return null;
        }
      }

      console.error("Failed to load thread history:", error.response?.data || error.message);
      return null;
    }
  };

  // Wraps loadThreadMessages with one more layer of retry that
  // covers the case the function itself can't: ensureJwtToken()
  // failing to produce a token at all (the main app's own access
  // token gone stale), which short-circuits loadThreadMessages
  // via `if (!token) return null` before it ever talks to the
  // chat backend, so the 401-retry inside it never runs. Forcing
  // a clean token cache + a fresh fetch here is the equivalent of
  // what a full page refresh used to do by accident.
  const loadThreadMessagesWithRetry = async (threadId) => {

    let history = await loadThreadMessages(threadId);

    if (history === null) {
      jwtCacheRef.current = { token: null, expiresAt: 0 };
      history = await loadThreadMessages(threadId, { forceRefresh: true });
    }

    return history;
  };

  useEffect(() => {

    if (loading) return;

    let cancelled = false;

    const init = async () => {

      if (isAuthenticated) {

        setIsLoadingThreads(true);
        const backendThreads = await fetchThreadsFromBackend();
        if (cancelled) return;

        // First load has no prior state worth protecting, so a
        // failed fetch (null) just falls back to an empty list
        // rather than leaving isLoadingThreads stuck forever.
        const resolvedThreads = backendThreads || [];

        setThreads(resolvedThreads);
        setIsLoadingThreads(false);

        if (resolvedThreads.length > 0) {

          const first = resolvedThreads[0];
          setActiveThreadId(first.thread_id);
          setIsLoadingHistory(true);

          const history = await loadThreadMessagesWithRetry(first.thread_id);
          if (cancelled) return;

          setMessages(history || []);
          setIsLoadingHistory(false);

        } else {
          setActiveThreadId(createThreadId());
          setMessages([]);
        }

      } else {
        setThreads([]);
        setActiveThreadId(createThreadId());
        setMessages([]);
      }
    };

    init();

    return () => { cancelled = true; };

  }, [isAuthenticated, loading]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const toggleChat = () => setIsOpen((previous) => !previous);

  const startNewChat = () => {

    if (isLoading) return;

    setActiveThreadId(createThreadId());
    setMessages([]);
    setInput("");

    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const selectThread = async (threadId) => {

    if (isLoading || threadId === activeThreadId) return;

    setActiveThreadId(threadId);
    setMessages([]);
    setIsLoadingHistory(true);

    const history = await loadThreadMessagesWithRetry(threadId);

    if (history === null) {
      // Both the normal attempt and the forced-refresh retry
      // failed — genuinely couldn't load this thread. Say so
      // instead of silently showing an empty conversation, which
      // is what made this bug look like data loss.
      setMessages([
        { id: createMessageId(), sender: "bot", text: "Couldn't load this conversation. Please try again." },
      ]);
    } else {
      setMessages(history);
    }

    setIsLoadingHistory(false);
  };


  /* ==========================================================
     SEND TEXT MESSAGE — STREAMING (typed input)
     ========================================================== */

  const sendMessage = async (textToSend) => {

    const messageText = textToSend || input;
    const trimmed = messageText.trim();

    if (!trimmed || isLoading) return;

    let currentThreadId = activeThreadId;

    if (!currentThreadId) {
      currentThreadId = createThreadId();
      setActiveThreadId(currentThreadId);
    }

    const botMessageId = createMessageId();

    setMessages((previous) => [
      ...previous,
      { id: createMessageId(), sender: "user", text: trimmed },
      { id: botMessageId, sender: "bot", text: "" },
    ]);

    setInput("");
    setIsLoading(true);

    const updateBotMessage = (text) => updateMessageText(botMessageId, text);

    // Best text shown so far — used if the request dies half-way.
    let shownText = "";

    try {

      let jwtToken = null;
      if (isAuthenticated) jwtToken = await ensureJwtToken();

      const response = await fetch(`${CHATBOT_API_BASE}/chat/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...NGROK_SKIP_HEADER,
        },
        body: JSON.stringify({
          message: trimmed,
          thread_id: currentThreadId,
          jwt_token: jwtToken || null,
        }),
      });

      // Guardrail block (400) or rate limit (429) come back as a
      // plain JSON body, NOT an SSE stream — handle those before
      // trying to read response.body as a stream.
      if (!response.ok) {
        const message = await extractErrorMessage(response);
        updateBotMessage(message);
        return;
      }

      const result = await consumeChatStream(response, {

        // Tokens REPLACE whatever was shown before (including any
        // node fallback text) — they are never appended to it.
        onToken: (_chunk, fullText) => {
          shownText = fullText;
          updateBotMessage(fullText);
        },

        // Only fires while no tokens have arrived yet.
        onNode: (text) => {
          shownText = text;
          updateBotMessage(text);
        },

        onDone: (event) => {
          if (event.thread_id) {
            currentThreadId = event.thread_id;
            setActiveThreadId(currentThreadId);
          }
        },
      });

      if (!result.finalText) {
        updateBotMessage(
          result.hadError
            ? FALLBACK_ERROR_MESSAGE
            : "Sorry, I couldn't generate a response."
        );
      }

      if (isAuthenticated) {
        const backendThreads = await fetchThreadsFromBackend();
        // Only overwrite the sidebar on a SUCCESSFUL refresh. A
        // null here means the refresh itself failed (e.g. a
        // stale-token 401 that the retry inside
        // fetchThreadsFromBackend also couldn't recover) — in
        // that case we keep showing whatever thread list is
        // already in state instead of blanking it.
        if (backendThreads !== null) {
          setThreads(backendThreads);
        }
      }

    } catch (error) {

      console.error("CHAT STREAM ERROR:", error.message);
      updateBotMessage(shownText || FALLBACK_ERROR_MESSAGE);

    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      if (!isLoading && input.trim()) sendMessage();
    }
  };

  const quickSuggestions = [
    "What could be causing my symptoms?",
    "How can I manage a fever at home?",
    "Help me find a medicine",
    "Show my pending medicine orders",
  ];


  const handleSuggestionClick = (text) => {
    setInput(text);
    setTimeout(() => inputRef.current?.focus(), 0);
  };


  /* ==========================================================
     TEXT-TO-SPEECH — queued, sentence-by-sentence, interruptible
     ========================================================== */

  useEffect(() => {

    if (!speechSynthesisSupported) return;

    const loadVoices = () => { voicesRef.current = window.speechSynthesis.getVoices(); };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

  }, []);

  // Lowest-level: speaks one already-cleaned chunk of text.
  const speakUtterance = useCallback((cleanText, { onEnd } = {}) => {

    if (!speechSynthesisSupported || !cleanText) {
      if (onEnd) onEnd();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);

    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    utterance.lang = "en-US";

    const preferred = pickBestVoice(voicesRef.current);
    if (preferred) utterance.voice = preferred;

    utterance.onend = () => { if (onEnd) onEnd(); };
    utterance.onerror = () => { if (onEnd) onEnd(); };

    window.speechSynthesis.speak(utterance);

  }, []);

  // One-off convenience (e.g. the wake-word greeting) — cleans
  // markdown then speaks immediately, bypassing the queue. Also
  // records the text as the current "spoken reference" so the
  // dictation recognizer knows to ignore hearing this back.
  const speak = useCallback((text, opts = {}) => {
    spokenReferenceTextRef.current = String(text || "");
    speakUtterance(stripMarkdownForSpeech(text), opts);
  }, [speakUtterance]);

  // Drains the sentence queue one at a time. Never calls
  // speechSynthesis.cancel() mid-stream — that was what caused
  // replies to occasionally cut themselves off before finishing.
  const processTtsQueue = () => {

    if (ttsQueueRef.current.length === 0) {
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      // Nothing left playing or queued — clear the echo-reference
      // so a stale value can never suppress the NEXT real turn.
      spokenReferenceTextRef.current = "";
      return;
    }

    const next = ttsQueueRef.current.shift();
    isSpeakingRef.current = true;
    setIsSpeaking(true);

    speakUtterance(next, {
      onEnd: () => setTimeout(() => processTtsQueueRef.current(), INTER_SENTENCE_GAP_MS),
    });
  };
  processTtsQueueRef.current = processTtsQueue;

  // Queues a chunk of raw (possibly markdown) text for speech,
  // kicking off playback immediately if nothing is currently
  // speaking. Also grows spokenReferenceTextRef so the dictation
  // recognizer always knows the full text the bot is in the
  // middle of saying (queued sentences included), not just the
  // one sentence currently playing.
  const enqueueSpeech = (rawText) => {

    const clean = stripMarkdownForSpeech(rawText);
    if (!clean) return;

    spokenReferenceTextRef.current = (
      spokenReferenceTextRef.current + " " + clean
    ).trim();

    ttsQueueRef.current.push(clean);

    if (!isSpeakingRef.current) processTtsQueueRef.current();
  };
  enqueueSpeechRef.current = enqueueSpeech;

  const stopSpeaking = () => {
    if (speechSynthesisSupported) window.speechSynthesis.cancel();
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  };

  // Interruption handler: wipes the speech queue, cancels any
  // audio currently playing, and aborts the in-flight streamed
  // response — used both for a manual "stop" and for barge-in
  // when the user starts talking over the bot.
  const cancelBotOutput = () => {

    ttsQueueRef.current = [];
    if (speechSynthesisSupported) window.speechSynthesis.cancel();
    isSpeakingRef.current = false;
    setIsSpeaking(false);
    spokenReferenceTextRef.current = "";

    if (voiceStreamAbortRef.current) {
      voiceStreamAbortRef.current.abort();
      voiceStreamAbortRef.current = null;
    }

    isProcessingVoiceRef.current = false;
    setIsProcessingVoice(false);
  };
  cancelBotOutputRef.current = cancelBotOutput;


  /* ==========================================================
     VOICE — send a transcribed turn through the streaming chat
     endpoint, speaking each sentence as soon as it's complete.
     ========================================================== */

  const sendVoiceText = async (transcript) => {

    // Fresh turn — any reference text from the previous reply no
    // longer matters.
    spokenReferenceTextRef.current = "";

    let currentThreadId = activeThreadIdRef.current;

    if (!currentThreadId) {
      currentThreadId = createThreadId();
      setActiveThreadId(currentThreadId);
      activeThreadIdRef.current = currentThreadId;
    }

    const botMessageId = createMessageId();

    setMessages((previous) => [
      ...previous,
      { id: createMessageId(), sender: "user", text: transcript },
      { id: botMessageId, sender: "bot", text: "" },
    ]);

    isProcessingVoiceRef.current = true;
    setIsProcessingVoice(true);

    // Cancel any previous still-in-flight voice request so it
    // can't land after this one and clobber the conversation.
    if (voiceStreamAbortRef.current) voiceStreamAbortRef.current.abort();
    const abortController = new AbortController();
    voiceStreamAbortRef.current = abortController;

    let speechBuffer = "";
    let shownText = "";

    const updateBotMessage = (text) => updateMessageText(botMessageId, text);

    // Pulls every complete sentence out of the buffer and queues
    // it for speech right away — this is what lets speech start on
    // the first sentence while the rest is still streaming in,
    // instead of waiting for the whole reply.
    const flushCompleteSentences = (force = false) => {

      const sentenceEnd = /[^.!?\n]*[.!?\n]+/g;
      let match;
      let consumed = 0;

      while ((match = sentenceEnd.exec(speechBuffer)) !== null) {
        const sentence = match[0];
        if (sentence.trim()) enqueueSpeechRef.current(sentence);
        consumed = sentenceEnd.lastIndex;
      }

      speechBuffer = speechBuffer.slice(consumed);

      if (force && speechBuffer.trim()) {
        enqueueSpeechRef.current(speechBuffer);
        speechBuffer = "";
      }
    };

    try {

      let jwtToken = null;
      if (isAuthenticatedRef.current) jwtToken = await ensureJwtToken();

      const response = await fetch(`${CHATBOT_API_BASE}/chat/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...NGROK_SKIP_HEADER,
        },
        body: JSON.stringify({
          message: transcript,
          thread_id: currentThreadId,
          jwt_token: jwtToken || null,
        }),
        signal: abortController.signal,
      });

      // Same as sendMessage: a guardrail block (400) or rate
      // limit (429) is plain JSON, not an SSE stream. Speak the
      // real reason out loud too, since we're in voice mode.
      if (!response.ok) {
        const message = await extractErrorMessage(response);
        updateBotMessage(message);
        enqueueSpeechRef.current(message);
        return;
      }

      const result = await consumeChatStream(response, {

        // Tokens are spoken as they stream in, and REPLACE any
        // node fallback text on screen.
        onToken: (chunk, fullText) => {
          shownText = fullText;
          speechBuffer += chunk;
          updateBotMessage(fullText);
          flushCompleteSentences();
        },

        // Node text is shown but NOT spoken yet — if real tokens
        // follow, they supersede it and it must never be read
        // out loud. It is only spoken below if no tokens arrive.
        onNode: (text) => {
          shownText = text;
          updateBotMessage(text);
        },

        onDone: (event) => {
          if (event.thread_id) {
            currentThreadId = event.thread_id;
            setActiveThreadId(currentThreadId);
            activeThreadIdRef.current = currentThreadId;
          }
        },
      });

      if (result.usedNodeFallback) {
        // No tokens ever arrived — the node text IS the reply.
        speechBuffer = result.nodeText;
      }

      flushCompleteSentences(true);

      if (!result.finalText) {
        updateBotMessage(
          result.hadError
            ? FALLBACK_ERROR_MESSAGE
            : "Sorry, I couldn't generate a response."
        );
      }

      if (isAuthenticatedRef.current) {
        const backendThreads = await fetchThreadsFromBackend();
        // Same guard as sendMessage — don't blank the sidebar on
        // a failed background refresh.
        if (backendThreads !== null) {
          setThreads(backendThreads);
        }
      }

    } catch (error) {

      if (error.name === "AbortError") {
        // Superseded by an interruption or a newer turn — not a
        // real failure, nothing to show the user.
      } else {
        console.error("Voice stream error:", error.message);
        updateBotMessage(shownText || FALLBACK_ERROR_MESSAGE);
      }

    } finally {

      if (voiceStreamAbortRef.current === abortController) {
        voiceStreamAbortRef.current = null;
      }

      isProcessingVoiceRef.current = false;
      setIsProcessingVoice(false);
    }
  };
  sendVoiceTextRef.current = sendVoiceText;


  /* ==========================================================
     VOICE — turn finalization + voice-mode lifecycle
     ========================================================== */

  const stopDictation = () => {

    if (dictationRecognitionRef.current) {

      try {
        dictationRecognitionRef.current.onend = null;
        dictationRecognitionRef.current.onresult = null;
        dictationRecognitionRef.current.onerror = null;
        dictationRecognitionRef.current.abort();
      } catch (e) { /* no-op */ }

      dictationRecognitionRef.current = null;
    }

    if (turnSilenceTimerRef.current) {
      clearTimeout(turnSilenceTimerRef.current);
      turnSilenceTimerRef.current = null;
    }

    turnTranscriptRef.current = "";
  };

  const finalizeTurn = () => {

    turnSilenceTimerRef.current = null;

    const transcript = turnTranscriptRef.current.trim();
    turnTranscriptRef.current = "";
    interruptedThisTurnRef.current = false;

    if (!transcript) return; // nothing said — keep listening, no-op

    const isStopPhrase = STOP_WORDS_LOCAL.includes(transcript.toLowerCase());

    if (isStopPhrase) {
      endVoiceMode("Okay, bye!");
      return;
    }

    sendVoiceTextRef.current(transcript);
  };
  finalizeTurnRef.current = finalizeTurn;

  // Single exit point for ending voice mode, no matter how it
  // happens (manual stop, stop phrase, etc.) — always restarts
  // wake-word listening afterward. Previously that restart only
  // happened along one specific path, so ending voice mode certain
  // ways left the mic silently dead until the page was refreshed.
  const endVoiceMode = (goodbyeText) => {

    setVoiceMode(false);
    cancelBotOutputRef.current();
    stopDictation();

    const restartWakeWord = () => {
      if (wakeWordEnabledRef.current) startWakeWordListening();
    };

    if (goodbyeText) {
      speak(goodbyeText, { onEnd: restartWakeWord });
    } else {
      restartWakeWord();
    }
  };

  // Long-lived continuous recognizer for the duration of a voice
  // session. Created once per session (not per turn), so there's
  // no start/stop overhead between turns — it just keeps listening
  // straight through the bot thinking and speaking, which is what
  // makes barge-in possible.
  const startDictation = useCallback(() => {

    if (!SpeechRecognitionCtor || dictationRecognitionRef.current) return;

    const recognition = new SpeechRecognitionCtor();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {

      let interimText = "";
      let finalTextThisEvent = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {

        const result = event.results[i];
        const transcript = result[0].transcript;

        if (result.isFinal) {
          finalTextThisEvent = (finalTextThisEvent + " " + transcript).trim();
        } else {
          interimText += transcript;
        }
      }

      // --------------------------------------------------------
      // SELF-ECHO CHECK
      //
      // Only meaningful while the bot is actually producing audio
      // (isSpeakingRef). Compare what was JUST heard in this event
      // against everything the bot is currently/about-to say
      // (spokenReferenceTextRef). If it's mostly the same words,
      // this is the mic hearing the speaker, not the user — drop
      // it completely: don't add it to the transcript, don't reset
      // the silence timer, and don't treat it as a barge-in.
      // --------------------------------------------------------

      const newlyHeardText = (finalTextThisEvent + " " + interimText).trim();

      const referenceText = spokenReferenceTextRef.current;

      const isSelfEcho =
        isSpeakingRef.current &&
        !!referenceText &&
        isLikelySelfEcho(newlyHeardText, referenceText);

      if (isSelfEcho) {
        return;
      }

      if (finalTextThisEvent) {
        turnTranscriptRef.current = (
          turnTranscriptRef.current + " " + finalTextThisEvent
        ).trim();
      }

      const heardEnough =
        (turnTranscriptRef.current + " " + interimText).trim().length >= INTERRUPT_MIN_CHARS;

      // Barge-in: the bot is talking or thinking and the user just
      // started speaking (and it passed the self-echo check above)
      // — stop it immediately instead of making them wait.
      if (
        heardEnough &&
        (isSpeakingRef.current || isProcessingVoiceRef.current) &&
        !interruptedThisTurnRef.current
      ) {
        interruptedThisTurnRef.current = true;
        cancelBotOutputRef.current();
      }

      if (turnSilenceTimerRef.current) clearTimeout(turnSilenceTimerRef.current);
      turnSilenceTimerRef.current = setTimeout(() => {
        finalizeTurnRef.current();
      }, TURN_SILENCE_MS);
    };

    recognition.onerror = (event) => {
      if (event.error !== "no-speech" && event.error !== "aborted") {
        console.error("Dictation recognition error:", event.error);
      }
    };

    recognition.onend = () => {

      dictationRecognitionRef.current = null;

      // Browsers sometimes end a continuous session on their own
      // (long silence, tab backgrounding, etc). If we're still
      // meant to be in voice mode, restart right away instead of
      // leaving the mic silently dead — this is what previously
      // required a page refresh to fix.
      if (voiceModeActiveRef.current) {
        setTimeout(() => startDictation(), 150);
      }
    };

    try {
      recognition.start();
      dictationRecognitionRef.current = recognition;
    } catch (error) {
      console.error("Could not start dictation:", error.message);
      dictationRecognitionRef.current = null;
    }

  }, []);

  const startVoiceMode = () => {

    stopWakeWordListening();
    setIsOpen(true);
    setVoiceMode(true);
    interruptedThisTurnRef.current = false;
    turnTranscriptRef.current = "";
    startDictation();
  };

  const handleMicButtonClick = () => {

    if (voiceModeActive) {
      endVoiceMode();
      return;
    }

    startVoiceMode();
  };


  /* ==========================================================
     WAKE WORD — "AVENGERS ASSEMBLE"
     ========================================================== */

  // Greets using the identity already available on the client (no
  // backend round trip needed just to say hello) and starts
  // listening immediately, in parallel with the greeting — not
  // after it — so you can start talking the instant it finishes,
  // or even talk over it.
  const greetAndStartVoiceMode = useCallback(() => {

    setIsOpen(true);
    setVoiceMode(true);
    interruptedThisTurnRef.current = false;
    turnTranscriptRef.current = "";

    const displayName = user?.username || user?.email;

    const greeting = isAuthenticated && displayName
      ? `Hi ${displayName}, how can I help you?`
      : "Hi, how can I help you?";

    setMessages((previous) => [
      ...previous,
      { id: createMessageId(), sender: "bot", text: greeting },
    ]);

    startDictation();
    speak(greeting);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, isAuthenticated, speak, startDictation]);

  const startWakeWordListening = useCallback(() => {

    if (
      !SpeechRecognitionCtor ||
      !wakeWordEnabledRef.current ||
      voiceModeActiveRef.current ||
      wakeRecognitionRef.current
    ) {
      return;
    }

    const recognition = new SpeechRecognitionCtor();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    let triggered = false;

    recognition.onresult = (event) => {

      if (triggered) return;

      for (let i = event.resultIndex; i < event.results.length; i++) {

        const transcript = event.results[i][0].transcript.toLowerCase().trim();

        const heardWakeWord = WAKE_PHRASES.some((phrase) => transcript.includes(phrase));

        if (heardWakeWord) {

          // Disarm this instance completely BEFORE tearing it
          // down, so its own onend can't race with the dictation
          // that's about to start and steal the mic back.
          triggered = true;
          recognition.onend = null;
          recognition.onresult = null;
          recognition.onerror = null;

          try { recognition.abort(); } catch (e) { /* no-op */ }

          wakeRecognitionRef.current = null;

          greetAndStartVoiceMode();

          return;
        }
      }
    };

    recognition.onerror = (event) => {
      if (event.error !== "no-speech" && event.error !== "aborted") {
        console.error("Wake-word recognition error:", event.error);
      }
    };

    recognition.onend = () => {

      wakeRecognitionRef.current = null;

      if (wakeWordEnabledRef.current && !voiceModeActiveRef.current) {
        setTimeout(() => startWakeWordListening(), 300);
      }
    };

    try {
      recognition.start();
      wakeRecognitionRef.current = recognition;
    } catch (error) {
      console.error("Could not start wake-word listener:", error.message);
      wakeRecognitionRef.current = null;
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [greetAndStartVoiceMode]);

  const stopWakeWordListening = useCallback(() => {

    if (wakeRecognitionRef.current) {

      try {
        wakeRecognitionRef.current.onend = null;
        wakeRecognitionRef.current.onresult = null;
        wakeRecognitionRef.current.abort();
      } catch (e) { /* no-op */ }

      wakeRecognitionRef.current = null;
    }

  }, []);

  const toggleWakeWord = () => {

    setWakeWordEnabled((previous) => {

      const next = !previous;
      wakeWordEnabledRef.current = next;

      if (next) startWakeWordListening();
      else stopWakeWordListening();

      return next;
    });
  };

  // On mount: ask for mic permission once up front (so the browser
  // doesn't silently block the wake-word listener the first time
  // it tries to start — SpeechRecognition shares the same
  // microphone permission as getUserMedia), then begin listening.
  useEffect(() => {

    let cancelled = false;

    const init = async () => {

      if (micSupported) {

        try {
          const primingStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          primingStream.getTracks().forEach((track) => track.stop());
        } catch (error) {
          console.warn("Microphone permission not granted:", error.message);
        }
      }

      if (cancelled) return;

      if (wakeWordEnabledRef.current) startWakeWordListening();
    };

    init();

    return () => {
      cancelled = true;
      if (voiceStreamAbortRef.current) voiceStreamAbortRef.current.abort();
      stopWakeWordListening();
      stopDictation();
      if (speechSynthesisSupported) window.speechSynthesis.cancel();
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  const activeThread = threads.find((thread) => thread.thread_id === activeThreadId);

  // Derived, not stored state — exactly one of these three is true
  // whenever voice mode is on: listening for the user, waiting on
  // the stream, or speaking the reply.
  const isListening = voiceModeActive && !isProcessingVoice && !isSpeaking;


  /* ==========================================================
     UI
     ========================================================== */

  return (

    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>

      <div style={{ flex: 1, overflow: "auto" }}>
        <Outlet />
      </div>

      {!isOpen && (

        <button
          type="button"
          onClick={toggleChat}
          className={"chatbot-big-launcher " + (isListening ? "chatbot-launcher-recording" : "")}
          aria-label="Open AI Assistance"
        >
          <RobotOutlined />
          <span>
            {voiceModeActive
              ? (isSpeaking ? "Speaking..." : isProcessingVoice ? "Thinking..." : "Listening...")
              : wakeWordEnabled && speechRecognitionSupported
                ? "AI agent for you • say “Avengers Assemble”"
                : "AI agent for you"}
          </span>
        </button>

      )}

      {isOpen && (

        <div className="chatbot-shell">

          {isAuthenticated && isSidebarOpen && (

            <div className="chatbot-sidebar">

              <div className="chatbot-sidebar-header">
                <div className="chatbot-sidebar-brand">
                  <RobotOutlined />
                  <span>AI Assistance</span>
                </div>
                <button type="button" onClick={() => setIsSidebarOpen(false)} className="chatbot-icon-button">
                  <CloseOutlined />
                </button>
              </div>

              <button type="button" onClick={startNewChat} className="chatbot-new-chat-button">
                <PlusOutlined />
                <span>New chat</span>
              </button>

              <div className="chatbot-thread-list">

                {isLoadingThreads && (
                  <div className="chatbot-empty-threads">Loading conversations...</div>
                )}

                {!isLoadingThreads && threads.length === 0 && (
                  <div className="chatbot-empty-threads">No conversations yet.</div>
                )}

                {!isLoadingThreads && threads.map((thread) => (
                  <div
                    key={thread.thread_id}
                    className={"chatbot-thread-item " + (thread.thread_id === activeThreadId ? "active" : "")}
                    onClick={() => selectThread(thread.thread_id)}
                  >
                    <MessageOutlined />
                    <span className="chatbot-thread-title">{thread.title}</span>
                  </div>
                ))}

              </div>

              <div className="chatbot-sidebar-footer">
                <div className="chatbot-user-avatar">
                  {(user?.username || user?.email || "U").charAt(0).toUpperCase()}
                </div>
                <div>
                  <div>{user?.username || user?.email || "User"}</div>
                  <small>Logged in</small>
                </div>
              </div>

            </div>

          )}

          <div className="chatbot-main">

            <div className="chatbot-main-header">

              {isAuthenticated && !isSidebarOpen && (
                <button type="button" onClick={() => setIsSidebarOpen(true)} className="chatbot-icon-button">
                  <MenuOutlined />
                </button>
              )}

              <div className="chatbot-header-info">
                <div className="chatbot-header-avatar">
                  <RobotOutlined />
                </div>
                <div>
                  <div className="chatbot-header-title">AI Assistance</div>
                  <div className="chatbot-header-status">
                    <span className="chatbot-status-dot" />
                    {isSpeaking
                      ? "Speaking... • start talking to interrupt"
                      : isProcessingVoice
                        ? "Thinking... • start talking to interrupt"
                        : voiceModeActive
                          ? "Listening... • say “stop” or tap mic to end"
                          : loading
                            ? "Connecting..."
                            : isAuthenticated
                              ? `Online • ${user?.username || user?.email || "Logged in"}`
                              : "Online • Guest"}
                  </div>
                </div>
              </div>

              {voiceModeActive && (

                <div
                  className={
                    "chatbot-voice-orb " +
                    (isSpeaking
                      ? "is-speaking"
                      : isProcessingVoice
                        ? "is-thinking"
                        : "is-listening")
                  }
                  aria-hidden="true"
                >

                  {isProcessingVoice ? (
                    <div className="chatbot-orb-dots">
                      <span /><span /><span />
                    </div>
                  ) : (
                    <div className="chatbot-orb-bars">
                      <span /><span /><span /><span /><span />
                    </div>
                  )}

                </div>

              )}

              {isSpeaking && (
                <button
                  type="button"
                  onClick={stopSpeaking}
                  className="chatbot-icon-button"
                  title="Stop speaking"
                >
                  <SoundOutlined />
                </button>
              )}

              {speechRecognitionSupported && (
                <button
                  type="button"
                  onClick={toggleWakeWord}
                  className="chatbot-icon-button"
                  title={
                    wakeWordEnabled
                      ? "Wake word listening is ON — click to disable"
                      : "Wake word listening is OFF — click to enable"
                  }
                >
                  {wakeWordEnabled ? <AudioOutlined /> : <AudioMutedOutlined />}
                </button>
              )}

              <button type="button" onClick={toggleChat} className="chatbot-icon-button">
                <CloseOutlined />
              </button>

            </div>

            {isAuthenticated && activeThread && (
              <div className="chatbot-current-thread">{activeThread.title}</div>
            )}

            <div className="chatbot-messages-area">

              {isLoadingHistory && (
                <div className="chatbot-welcome"><p>Loading conversation...</p></div>
              )}

              {!isLoadingHistory && messages.length === 0 && (

                <div className="chatbot-welcome">
                  <div className="chatbot-welcome-icon"><RobotOutlined /></div>
                  <h2>Namaste! 👋</h2>
                  <p>How can I help you with AI Assistance today?</p>

                  <div className="chatbot-suggestions">
                    {quickSuggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        type="button"
                        className="chatbot-suggestion"
                        onClick={() => handleSuggestionClick(suggestion)}
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>

              )}

              {!isLoadingHistory && messages.map((message, index) => {

                const isLastMessage = index === messages.length - 1;

                const isStreamingPlaceholder =
                  message.sender === "bot" &&
                  message.text === "" &&
                  (isLoading || isProcessingVoice) &&
                  isLastMessage;

                return (

                  <div
                    key={message.id || index}
                    className={message.sender === "user" ? "chatbot-message-row user" : "chatbot-message-row bot"}
                  >

                    {message.sender === "bot" && (
                      <div className="chatbot-message-avatar"><RobotOutlined /></div>
                    )}

                    <div className={message.sender === "user" ? "chatbot-user-message" : "chatbot-bot-message"}>

                      {isStreamingPlaceholder ? (
                        <span className="chatbot-typing"><span /><span /><span /></span>
                      ) : message.sender === "bot" ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                      ) : (
                        message.text
                      )}

                    </div>

                  </div>

                );

              })}

              <div ref={chatEndRef} />

            </div>

            <div className="chatbot-input-wrapper">

              <div className="chatbot-input-box">

                {speechRecognitionSupported && (
                  <button
                    type="button"
                    onClick={handleMicButtonClick}
                    disabled={isLoading}
                    className={"chatbot-mic-button " + (isListening ? "recording" : "") + (voiceModeActive ? " active" : "")}
                    title={voiceModeActive ? "Tap to end voice mode" : "Speak your message"}
                  >
                    <AudioOutlined />
                  </button>
                )}

                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  placeholder={
                    isListening
                      ? "Listening..."
                      : isProcessingVoice
                        ? "Thinking..."
                        : isSpeaking
                          ? "Speaking..."
                          : "Message with AI Assistance..."
                  }
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading || voiceModeActive}
                  autoComplete="off"
                />

                <button
                  type="button"
                  onClick={() => sendMessage()}
                  disabled={isLoading || !input.trim()}
                  className="chatbot-send-button"
                >
                  {isLoading ? <span className="chatbot-spinner" /> : <SendOutlined />}
                </button>

              </div>

              <div className="chatbot-disclaimer">
                AI can make mistakes. Please verify important information.
              </div>

            </div>

          </div>

        </div>

      )}

    </div>
  );
};

export default Chatbot;