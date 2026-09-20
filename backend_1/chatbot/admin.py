# ============================================================
# admin.py
# ============================================================

from django.contrib import admin

from .models import ChatThread


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):

    # Columns shown in Django admin
    list_display = (
        "thread_id",
        "user_id",
        "title",
        "created_at",
        "updated_at",
    )

    # Searchable fields
    search_fields = (
        "thread_id",
        "user_id",
        "title",
    )

    # Filters in the right sidebar
    list_filter = (
        "created_at",
        "updated_at",
    )

    # Newest/updated conversations first
    ordering = (
        "-updated_at",
    )

    # Prevent accidental editing of timestamps
    readonly_fields = (
        "created_at",
        "updated_at",
    )
