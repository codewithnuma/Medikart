from rest_framework import serializers

from .models import VideoCall


class VideoCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoCall
        fields = (
            "id",
            "title",
            "subject",
            "created_by",
            "is_active",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_by",
            "is_active",
            "created_at",
        )
