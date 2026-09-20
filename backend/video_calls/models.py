import uuid

from django.conf import settings
from django.db import models


class VideoCall(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_video_calls",
    )
    title = models.CharField(
        max_length=255,
    )

    subject = models.TextField()
    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    def __str__(self):
        return f"{self.title} - {self.created_by.username}"
