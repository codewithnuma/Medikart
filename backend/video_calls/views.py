from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from accounts.views import JWTAuthenticationFromCookie
from accounts.permission import IsEmployee

from .models import VideoCall
from .serializers import VideoCallSerializer


class PharmacyVideoCallListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = VideoCallSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee,
    ]

    def get_queryset(self):
        return VideoCall.objects.filter(
            created_by=self.request.user,
            is_active=True,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )


class VideoCallJoinDetailView(
    generics.RetrieveAPIView
):
    serializer_class = VideoCallSerializer

    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
    ]

    lookup_field = "id"
    lookup_url_kwarg = "room_id"

    def get_queryset(self):
        return VideoCall.objects.filter(
            is_active=True
        )

class PharmacyVideoCallEndView(APIView):
    authentication_classes = [
        JWTAuthenticationFromCookie
    ]

    permission_classes = [
        IsAuthenticated,
        IsEmployee,
    ]

    def post(self, request, room_id):
        video_call = VideoCall.objects.filter(
            id=room_id,
            created_by=request.user,
            is_active=True,
        ).first()

        if video_call is None:
            return Response(
                {
                    "detail": "Active consultation not found."
                },
                status=404,
            )

        video_call.is_active = False
        video_call.save(
            update_fields=["is_active"]
        )

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(
            f"video_call_{video_call.id}",
            {
                "type": "consultation_ended",
            },
        )

        return Response(
            {
                "detail": "Consultation ended.",
                "id": str(video_call.id),
                "is_active": False,
            }
        )



