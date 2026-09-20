# ============================================================
# validation.py
# ============================================================
#
# Identity resolution for the chatbot server.
#
# The chatbot server does not share a database with the main
# Django backend, so it asks Django who the caller is over
# HTTP, using the JWT the frontend passed through.
#
# Two ids come out of this:
#
#   user_id   -> scopes LONG-TERM memory (the store) and owns
#                ChatThread rows. Must be STABLE across every
#                thread and every request for one person.
#   thread_id -> scopes SHORT-TERM memory (the checkpointer).
#                One thread = one conversation.
# ============================================================

import time
import uuid
import hashlib

import requests


# ============================================================
# DJANGO BACKEND
# ============================================================

DJANGO_BASE_URL = "http://127.0.0.1:8000/api"

REQUEST_TIMEOUT = 5

# Tried in order. The first one that returns a usable user
# wins, so a rename on the Django side doesn't take the
# chatbot down.
ME_ENDPOINTS = (
    "accounts/me/",
    "accounts/rasa-verify-token/",
)


# ============================================================
# IDENTITY CACHE
# ============================================================
#
# The old code fired a blocking HTTP call to Django from
# __init__ on every single request — every message, every
# thread-list fetch, every thread click. Same token, same
# answer, three round trips per message.
#
# Cached by a hash of the token (never the token itself) for a
# short TTL. Access tokens live 5 minutes, so 60s is safe: a
# revoked token stops working within a minute.
# ============================================================

_USER_CACHE: dict[str, tuple[float, dict | None]] = {}

CACHE_TTL_SECONDS = 60


def _cache_key(jwt_token: str) -> str:

    return hashlib.sha256(
        jwt_token.encode("utf-8")
    ).hexdigest()


def _cache_get(jwt_token: str):
    """
    Returns (hit, value). `hit` distinguishes "cached as None"
    (a token we already know is bad) from "not cached at all".
    """

    entry = _USER_CACHE.get(_cache_key(jwt_token))

    if entry is None:
        return False, None

    stored_at, value = entry

    if time.time() - stored_at > CACHE_TTL_SECONDS:

        _USER_CACHE.pop(_cache_key(jwt_token), None)

        return False, None

    return True, value


def _cache_set(jwt_token: str, value: dict | None) -> None:

    _USER_CACHE[_cache_key(jwt_token)] = (
        time.time(),
        value,
    )

    # Keep it from growing without bound in a long-running
    # process.
    if len(_USER_CACHE) > 500:

        now = time.time()

        for key, (stored_at, _) in list(_USER_CACHE.items()):

            if now - stored_at > CACHE_TTL_SECONDS:
                _USER_CACHE.pop(key, None)


# ============================================================
# FIELD EXTRACTION
# ============================================================
#
# THIS IS WHERE THE ORIGINAL BUG WAS.
#
# /accounts/me/ is the UserDetail view, serialised with
# CustomUserSerializer:
#
#     fields = ['id', 'email', 'username', 'Role']
#
# There is no "user_id" key in that payload. The old code read
# user.get("user_id"), got None, and silently fell through to
# the guest branch on every logged-in request — while the
# print above it still said "LOGGED IN USER" because it read
# `email` separately, and `email` does exist.
#
# Probing a list of candidates means this keeps working
# whether Django returns `id` (UserDetail), `user_id`
# (rasa_verify_token), or a nested `user` object
# (rasa_get_token).
# ============================================================

ID_KEYS = ("user_id", "id", "pk")

EMAIL_KEYS = ("email", "user_email")

USERNAME_KEYS = ("username", "user_name")

# Django's field is `Role`, capital R. The old code read
# "role" and always got None.
ROLE_KEYS = ("Role", "role")

# Some of your endpoints nest the user one level down.
NESTED_KEYS = ("user", "data", "profile")


def _flatten(payload: dict) -> dict:
    """
    Merge a nested user object up into the top level, with
    top-level keys winning.
    """

    if not isinstance(payload, dict):
        return {}

    merged = {}

    for key in NESTED_KEYS:

        nested = payload.get(key)

        if isinstance(nested, dict):
            merged.update(nested)

    merged.update(payload)

    return merged


def _first(payload: dict, keys) -> str | None:

    for key in keys:

        value = payload.get(key)

        if value is None:
            continue

        value = str(value).strip()

        if value and value.lower() not in ("none", "null"):
            return value

    return None


# ============================================================
# CHATBOT IDENTITY / VALIDATION
# ============================================================

class Chatbot:

    def __init__(
        self,
        jwt_token=None,
        thread_id=None,
    ):
        """
        jwt_token:
            JWT forwarded from the frontend. None for guests.

        thread_id:
            Existing conversation id -> resume it.
            Absent -> mint a new one.
        """

        self.jwt_token = (
            jwt_token.strip()
            if isinstance(jwt_token, str)
            else None
        )

        # Tolerate a full "Bearer xxx" string being passed in
        # by mistake.
        if (
            self.jwt_token
            and self.jwt_token.lower().startswith("bearer ")
        ):
            self.jwt_token = self.jwt_token[7:].strip()

        if not self.jwt_token:
            self.jwt_token = None

        # ----------------------------------------------------
        # THREAD ID
        # ----------------------------------------------------
        #
        # Honour whatever the client sent, verbatim. Resuming a
        # previous conversation only works if this id round
        # trips unchanged.
        # ----------------------------------------------------

        if thread_id and str(thread_id).strip():
            self.thread_id = str(thread_id).strip()

        else:
            self.thread_id = str(uuid.uuid4())

        # ----------------------------------------------------
        # Resolved lazily, on the first get_identity() call —
        # not in __init__, so constructing a Chatbot is free.
        # ----------------------------------------------------

        self.user = None
        self.is_authenticated = False

        self._identity = None
        self._resolved = False

    # ========================================================
    # HTTP HEADERS
    # ========================================================

    def headers(self):

        headers = {
            "Content-Type": "application/json",
        }

        if self.jwt_token:

            headers["Authorization"] = (
                f"Bearer {self.jwt_token}"
            )

        return headers

    # ========================================================
    # GET CURRENT USER
    # ========================================================

    def get_current_user(self):
        """
        Ask Django to identify the caller from the JWT.
        Returns the flattened user dict, or None.
        """

        if not self.jwt_token:
            return None

        hit, cached = _cache_get(self.jwt_token)

        if hit:
            return cached

        unreachable = False

        for endpoint in ME_ENDPOINTS:

            url = f"{DJANGO_BASE_URL}/{endpoint}"

            try:

                response = requests.get(
                    url,
                    headers=self.headers(),
                    timeout=REQUEST_TIMEOUT,
                )

            except requests.RequestException as exc:

                # Network-level failure: Django down, wrong
                # port, timeout. NOT the same as a rejected
                # token, so this is never cached — the next
                # request retries.
                unreachable = True

                print(
                    "Identity lookup could not reach Django "
                    f"at {url}: "
                    f"{type(exc).__name__}: {exc}"
                )

                continue

            # ------------------------------------------------
            # Token genuinely rejected
            # ------------------------------------------------

            if response.status_code in (401, 403):

                print(
                    "JWT rejected by Django "
                    f"({response.status_code}) at {endpoint}."
                )

                _cache_set(self.jwt_token, None)

                return None

            # ------------------------------------------------
            # Endpoint missing / erroring -> try the next one
            # ------------------------------------------------

            if not response.ok:

                print(
                    f"Identity endpoint {endpoint} returned "
                    f"{response.status_code}."
                )

                continue

            try:
                payload = response.json()

            except ValueError:

                print(
                    f"Identity endpoint {endpoint} returned "
                    "non-JSON."
                )

                continue

            user = _flatten(payload)

            if not _first(user, ID_KEYS):

                # Responded fine but carries no id under any
                # known key. Loud, because this is the exact
                # failure that used to masquerade as a guest.
                print(
                    f"Identity endpoint {endpoint} returned "
                    "no usable id. Keys present: "
                    f"{sorted(user.keys())}. Add the right "
                    "key to ID_KEYS."
                )

                continue

            _cache_set(self.jwt_token, user)

            return user

        if unreachable:

            print(
                "All identity endpoints unreachable — "
                "treating caller as guest for this request."
            )

        return None

    # ========================================================
    # RESOLVE
    # ========================================================

    def _resolve(self):

        if self._resolved:
            return

        self._resolved = True

        if not self.jwt_token:
            return

        self.user = self.get_current_user()

        self.is_authenticated = bool(
            self.user
            and _first(self.user, ID_KEYS)
        )

    # ========================================================
    # GET IDENTITY
    # ========================================================

    def get_identity(self):
        """
        Identity passed into LangGraph.

        Authenticated -> user_id is Django's real user id, as
                         a string.
        Guest         -> user_id is guest-{thread_id}, so two
                         guests never share a long-term memory
                         namespace.

        user_id is NEVER None, and authenticated=True always
        implies a real id. An authenticated-with-null-id
        identity is what wrote ChatThread rows with a null
        owner and made resuming a thread 404.
        """

        if self._identity is not None:
            return self._identity

        self._resolve()

        if self.is_authenticated:

            user = self.user or {}

            self._identity = {
                "authenticated": True,
                "user_id": _first(user, ID_KEYS),
                "username": _first(user, USERNAME_KEYS),
                "email": _first(user, EMAIL_KEYS),
                "role": _first(user, ROLE_KEYS),
                "thread_id": self.thread_id,
            }

        else:

            self._identity = {
                "authenticated": False,
                "user_id": f"guest-{self.thread_id}",
                "username": None,
                "email": None,
                "role": None,
                "thread_id": self.thread_id,
            }

        self.print_identity()

        return self._identity

    # ========================================================
    # BACKEND API CALL
    # ========================================================

    def call_backend(
        self,
        endpoint,
        method="GET",
        data=None,
    ):
        """
        Call a Django endpoint with the caller's JWT attached.

            bot.call_backend("bookings/", method="GET")
        """

        method = method.upper()

        if method not in (
            "GET",
            "POST",
            "PATCH",
            "PUT",
            "DELETE",
        ):

            raise ValueError(
                f"Unsupported HTTP method: {method}"
            )

        url = f"{DJANGO_BASE_URL}/{endpoint.lstrip('/')}"

        kwargs = {
            "headers": self.headers(),
            "timeout": REQUEST_TIMEOUT,
        }

        if method in ("POST", "PATCH", "PUT"):
            kwargs["json"] = data or {}

        try:

            response = requests.request(
                method,
                url,
                **kwargs,
            )

            try:
                result = response.json()

            except ValueError:
                result = response.text

            return {
                "success": response.ok,
                "status": response.status_code,
                "data": result,
            }

        except requests.RequestException as exc:

            return {
                "success": False,
                "status": None,
                "data": None,
                "error": str(exc),
            }

    # ========================================================
    # DEBUG / PRINT IDENTITY
    # ========================================================

    def print_identity(self):

        identity = self._identity or {}

        print()
        print("=" * 70)

        if identity.get("authenticated"):
            print("LOGGED IN USER")
        else:
            print("GUEST USER")

        print("=" * 70)

        print("User ID:  ", identity.get("user_id"))
        print("Username: ", identity.get("username"))
        print("Email:    ", identity.get("email"))
        print("Role:     ", identity.get("role"))
        print("Thread ID:", identity.get("thread_id"))

        print("=" * 70)
        print()

        return identity