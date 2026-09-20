from django.urls import path

from .views import (
    PharmacyVideoCallEndView,
    PharmacyVideoCallListCreateView,
    VideoCallJoinDetailView,
)


urlpatterns = [
    path(
        "pharmacy/",
        PharmacyVideoCallListCreateView.as_view(),
        name="pharmacy-video-calls",
    ),

    path(
        "pharmacy/<uuid:room_id>/end/",
        PharmacyVideoCallEndView.as_view(),
        name="pharmacy-video-call-end",
    ),

    path(
        "join/<uuid:room_id>/",
        VideoCallJoinDetailView.as_view(),
        name="video-call-join-detail",
    ),
]
