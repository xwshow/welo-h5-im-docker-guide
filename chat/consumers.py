import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .models import Thread
from .services import persist_text_message


class ThreadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.thread_id = int(self.scope["url_route"]["kwargs"]["thread_id"])
        self.thread = await self._load_thread(self.thread_id)
        if not self.thread or self.user.pk not in {self.thread.user_a_id, self.thread.user_b_id}:
            await self.close(code=4403)
            return
        self.group = self.thread.group_name()
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if getattr(self, "group", None):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"type": "error", "message": "invalid json"}))
            return
        # Ignore any client-supplied sender identity.
        if payload.get("type") != "chat":
            return
        try:
            message = await self._save_message(payload.get("body", ""))
        except (ValueError, PermissionError) as exc:
            await self.send(json.dumps({"type": "error", "message": str(exc)}))
            return
        await self.channel_layer.group_send(
            self.group, {"type": "chat.message", "message": message}
        )

    async def chat_message(self, event):
        await self.send(json.dumps({"type": "chat", "message": event["message"]}))

    @database_sync_to_async
    def _load_thread(self, thread_id: int):
        return Thread.objects.filter(pk=thread_id).first()

    @database_sync_to_async
    def _save_message(self, body: str):
        msg = persist_text_message(self.thread, self.user, body)
        return {
            "id": msg.pk,
            "thread_id": msg.thread_id,
            "body": msg.body,
            "sender_id": msg.sender_id,
            "sender": self.user.username,
            "created_at": msg.created_at.isoformat(),
        }
