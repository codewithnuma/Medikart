from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def api_root(request):
    return JsonResponse({"status": "ok", "message": "Backend is running"})


urlpatterns = [
    path("", api_root, name="api-root"),

    # Django admin
    path(
        "admin/",
        admin.site.urls
    ),

    # Accounts API
    path(
        "api/accounts/",
        include("accounts.urls")
    ),

    # Reports API
    path(
        "api/",
        include("reports.urls")
    ),

    # Video calls API
    path(
        "api/video-calls/",
        include("video_calls.urls")
    ),
]


# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
