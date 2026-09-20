# ============================================================
# models.py
# ============================================================

from django.db import models


class ChatThread(models.Model):
    """
    One row per conversation thread, owned by an authenticated
    user. Guests never get a row here — their history isn't
    meant to persist or be listable, by design.
    """

    thread_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
    )

    user_id = models.CharField(
        max_length=64,
        db_index=True,
    )

    title = models.CharField(
        max_length=255,
        default="New conversation",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.thread_id})"