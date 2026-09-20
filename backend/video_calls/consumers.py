import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import VideoCall


@database_sync_to_async
def video_call_is_active(room_id):
    try:
        room_uuid = uuid.UUID(str(room_id))
    except (ValueError, TypeError, AttributeError):
        return False

    return VideoCall.objects.filter(
        id=room_uuid,
        is_active=True,
    ).exists()


class VideoCallConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]

        room_is_valid = await video_call_is_active(
            self.room_id
        )

        if not room_is_valid:
            await self.close(code=4404)
            return

        self.room_group_name = f"video_call_{self.room_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send_json(
            {
                "type": "connection_ready",
                "participant_id": self.channel_name,
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "participant_joined",
                "participant_id": self.channel_name,
            },
        )

    async def disconnect(self, close_code):
        if not hasattr(self, "room_group_name"):
            return

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "participant_left",
                "participant_id": self.channel_name,
            },
        )

    async def receive_json(self, content):
        message_type = content.get("type")
        target = content.get("target")

        allowed_types = {
            "offer",
            "answer",
            "ice_candidate",
        }

        if message_type not in allowed_types:
            return

        if not target:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "webrtc_signal",
                "sender": self.channel_name,
                "target": target,
                "message": content,
            },
        )

    async def webrtc_signal(self, event):
        if event["target"] != self.channel_name:
            return

        await self.send_json(
            {
                "type": "webrtc_signal",
                "sender": event["sender"],
                "message": event["message"],
            }
        )

    async def consultation_ended(self, event):
        await self.send_json(
            {
                "type": "consultation_ended",
            }
        )

    async def participant_joined(self, event):
        if event["participant_id"] == self.channel_name:
            return

        await self.send_json(
            {
                "type": "participant_joined",
                "participant_id": event["participant_id"],
            }
        )

    async def participant_left(self, event):
        if event["participant_id"] == self.channel_name:
            return

        await self.send_json(
            {
                "type": "participant_left",
                "participant_id": event["participant_id"],
            }
        )

