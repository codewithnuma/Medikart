# Guardrails module

## Architecture

```
USER MESSAGE
    │
    ▼
Rate limit check (rate_limit.py)              → 429 if exceeded
    │
    ▼
Input length check (service.py / config.py)   → 400 if too long
    │
    ▼
Simple-message handler (simple_responses.py)  → instant predefined reply,
    │  (no match)                                NO LLM call at all
    ▼
Fast-path deterministic checks (input_security.py)
    │  (no unambiguous match)                  → instant block on textbook
    │                                             injection/jailbreak/secret
    │                                             extraction phrases, NO LLM
    ▼
NeMo Guardrails self-check-input rail (nemo/)  → contextual LLM classification
    │  (allowed)                                  of anything the fast path
    ▼                                              didn't already catch
AI MODEL (your existing chatbot.py graph — unchanged)
    │
    ▼
Deterministic secret redaction (output_security.py)
    │
    ▼
NeMo self-check-output policy check (service.py)
    │
    ▼
SAFE RESPONSE → USER
```

## Files

| File | Purpose |
|---|---|
| `config.py` | All tunables: rate limits, input length, topic policy, refusal text |
| `simple_responses.py` | Deterministic greeting/thanks/goodbye handler, zero LLM cost |
| `input_security.py` | Fast regex deny-list for unambiguous attacks |
| `output_security.py` | Secret detection/redaction, incl. streaming-safe redactor |
| `rate_limit.py` | Django-cache-backed per-user/IP rate limiting |
| `service.py` | Orchestrates everything; the only thing views.py imports |
| `exceptions.py` | `GuardrailBlocked`, `RateLimitExceeded`, `InputTooLarge` |
| `utils.py` | Structured security logging (never logs secrets/tokens) |
| `nemo/` | NeMo Guardrails config, prompts, Colang rails |

## Adding a new simple response

Edit `simple_responses.py`:

```python
SIMPLE_RESPONSES = {
    ...
    "good night": "Good night! Sleep well.",
}
```

The normalizer already lowercases, strips punctuation, and collapses
repeated letters, so `"Good Night!!"` and `"goodnight"` variants are
handled — add close variants as separate keys if needed.

## Adding/removing allowed topics

Edit `ALLOWED_TOPICS` / `BLOCKED_TOPICS` in `config.py`. Topic
enforcement is **off by default** (`ENFORCE_TOPIC_POLICY = False`)
until you confirm this chatbot's exact domain — turn it on via the
`GUARDRAILS_ENFORCE_TOPIC_POLICY=true` env var once confirmed.

## Changing rate limits

Set env vars (see `.env.example`):
`GUARDRAILS_RATE_LIMIT_PER_MINUTE`, `GUARDRAILS_RATE_LIMIT_PER_HOUR`,
`GUARDRAILS_GUEST_RATE_LIMIT_PER_MINUTE`, `GUARDRAILS_GUEST_RATE_LIMIT_PER_HOUR`.

## Running tests

```bash
python manage.py test chatbot.tests.test_guardrails
# or
pytest chatbot/tests/test_guardrails.py -v
```

## Troubleshooting

- **"Failed to initialize NeMo Guardrails" on startup** — check
  `GROQ_API_KEY` is set and `nemoguardrails` is installed
  (`pip show nemoguardrails`). The app still starts; `guardrail_service.is_available`
  will be `False` and input checks fall back to the fail-safe refusal
  for anything that isn't a simple message or an obvious fast-path
  block (see `FAIL_SAFE_MESSAGE` in `config.py`).
- **Legitimate question getting blocked** — check `input_security.py`'s
  fast-path patterns first (they're regex, so a false match there is
  a config bug); if it's not matching those, it's the NeMo self-check
  LLM being overly cautious — tune the prompt in `nemo/prompts.yml`.
- **"Hi, can you explain X" only gets the greeting** — this means
  `simple_responses.classify_simple_message` is misclassifying it;
  check `_DISQUALIFYING_TOKENS` / `_MAX_SIMPLE_WORD_COUNT` in that file.
- **Streaming feels delayed** — `StreamingRedactor` intentionally holds
  back the last ~120 characters as a rolling buffer so a secret split
  across two chunks can't slip through; this is a small, constant lag,
  not per-chunk buffering of the whole reply.

## Honesty note on security claims

This system provides **defense-in-depth**, not a guarantee. Regex
fast-paths and LLM self-checks both reduce risk but can still miss
novel phrasing or be fooled by adversarial input. Treat this as one
layer among several (also: least-privilege backend access, secret
management, monitoring/logging) — not a substitute for them.