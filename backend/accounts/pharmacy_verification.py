# ============================================================
# accounts/pharmacy_verification.py   (NEW FILE — main backend)
#
# - is_internal_request()          : checks the shared secret header
# - start_pharmacy_verification()  : after a pharmacy registration is
#                                    saved, calls the AI agent in a
#                                    background thread, so the register
#                                    request returns immediately.
#
# Outcomes returned by the agent:
#
#   accepted        -> the agent already created the user through
#                      /accounts/register/pharmacy/ (which also marked
#                      the RegistrationRequest "accepted")
#   denied          -> this module marks the RegistrationRequest "denied"
#   pending_review  -> agent/NPC/backend problem: request stays "pending"
#                      so an admin can still review it manually
# ============================================================

import hmac
import logging
import threading

import requests
from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

from .models import RegistrationRequest

logger = logging.getLogger(__name__)


# ============================================================
# INTERNAL AUTH
# ============================================================

def is_internal_request(request) -> bool:

    expected = (getattr(settings, "INTERNAL_API_KEY", "") or "").strip()
    provided = (request.headers.get("X-Internal-Key", "") or "").strip()

    if not expected:
        return False

    return hmac.compare_digest(expected.encode(), provided.encode())


# ============================================================
# AGENT CALL
# ============================================================

def _call_agent(payload: dict) -> dict:

    key = (getattr(settings, "INTERNAL_API_KEY", "") or "").strip()

    if not key:
        raise RuntimeError(
            "INTERNAL_API_KEY is empty in the main backend. "
            "Set INTERNAL_API_KEY in the backend .env and use "
            "config('INTERNAL_API_KEY') in settings.py."
        )

    url = getattr(
        settings,
        "PHARMACY_AGENT_URL",
        "http://127.0.0.1:8001/api/chat/pharmacy-verify/",
    )

    timeout = getattr(settings, "PHARMACY_AGENT_TIMEOUT", 120)

    response = requests.post(
        url,
        json=payload,
        headers={"X-Internal-Key": key},
        timeout=timeout,
    )

    if not response.ok:
        logger.error(
            "Agent returned %s: %s",
            response.status_code,
            response.text[:500],
        )

    response.raise_for_status()

    return response.json()


def _finalize(registration_id: int, result: dict) -> None:

    outcome = result.get("outcome")

    registration = RegistrationRequest.objects.get(pk=registration_id)

    if outcome == "denied":

        if registration.status == "pending":

            registration.status = "denied"
            registration.reviewed_at = timezone.now()
            registration.rejection_reason = (
                result.get("denial_reason")
                or "Pharmacy registration number could not be verified."
            )
            registration.save()

            logger.info("Registration %s denied by AI agent.", registration_id)

        return

    if outcome == "accepted":

        logger.info(
            "Registration %s accepted by AI agent (user_id=%s, email_sent=%s).",
            registration_id,
            result.get("user_id"),
            result.get("email_sent"),
        )

        return

    logger.warning(
        "Registration %s left pending for admin review "
        "(status=%s, create_error=%s).",
        registration_id,
        result.get("status"),
        result.get("create_error"),
    )


def _worker(registration_id: int, payload: dict) -> None:

    close_old_connections()

    try:

        result = _call_agent(payload)

        _finalize(registration_id, result)

    except Exception:

        # Request stays "pending" -> admin can review it manually.
        logger.exception(
            "Pharmacy verification failed for registration %s.",
            registration_id,
        )

    finally:

        close_old_connections()


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def start_pharmacy_verification(
    registration: RegistrationRequest,
    license_no: str,
) -> None:

    payload = {
        "registration_id": registration.id,
        "username": registration.username,
        "email": registration.email,
        "phone_number": getattr(registration, "phone_number", "") or "",
        "license_no": license_no,
    }

    # on_commit: if ATOMIC_REQUESTS is on, the agent must not call back
    # into /register/pharmacy/ before the RegistrationRequest is committed.
    transaction.on_commit(
        lambda: threading.Thread(
            target=_worker,
            args=(registration.id, payload),
            daemon=True,
            name=f"pharmacy-verify-{registration.id}",
        ).start()
    )