from django.urls import path

from .views import (
    ChatView,
    ChatStreamView,
    VoiceToTextView,
    VoiceChatView,
    ThreadListView,
    ThreadHistoryView,
    PharmacyVerifyView,
)


urlpatterns = [
    path("chat/", ChatView.as_view()),
    path("chat/stream/", ChatStreamView.as_view()),

    # Voice audio → text only (kept for compatibility)
    path("voice/", VoiceToTextView.as_view()),
    path("pharmacy-verify/", PharmacyVerifyView.as_view()),

    # Voice audio → transcribe → run agent → text answer, one shot
    path("voice-chat/", VoiceChatView.as_view()),

    path("threads/", ThreadListView.as_view()),
    path(
        "threads/<str:thread_id>/messages/",
        ThreadHistoryView.as_view(),
    ),
]