from channels.generic.websocket import AsyncJsonWebsocketConsumer


class VideoCallConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"video_call_{self.room_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive_json(self, content):
        message_type = content.get("type")

        allowed_types = {
            "offer",
            "answer",
            "ice_candidate",
        }

        if message_type not in allowed_types:
            return
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "webrtc_signal",
                "sender": self.channel_name,
                "message": content,
            },
        )
        
        async def webrtc_signal(self, event):
            if event["sender"] == self.channel_name:
                return

        await self.send_json(
            {
                "type": "webrtc_signal",
                "sender": event["sender"],
                "message": event["message"],
            }
        )