from django.contrib import admin

from .models import VideoCall


@admin.register(VideoCall)
class VideoCallAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "created_by",
        "is_active",
        "created_at",
    )

    search_fields = (
        "title",
        "subject",
        "created_by__username",
        "created_by__email",
    )

    list_filter = (
        "is_active",
        "created_at",
    )
