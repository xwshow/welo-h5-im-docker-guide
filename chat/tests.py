from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import Client, TestCase, TransactionTestCase
from channels.testing import WebsocketCommunicator

from im_guide.asgi import application
from .models import Friendship, Message, Thread
from .services import persist_text_message, request_friend, accept_friend


class FriendAndMessageTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user("alice", password="password123")
        self.b = User.objects.create_user("bob", password="password123")

    def test_friend_flow_and_persist_first(self):
        row = request_friend(self.a, "bob")
        self.assertEqual(row.status, Friendship.PENDING)
        accept_friend(self.b, row.pk)
        thread = Thread.get_or_create_for(self.a.pk, self.b.pk)
        msg = persist_text_message(thread, self.a, "hello")
        self.assertEqual(msg.body, "hello")
        self.assertEqual(thread.messages.count(), 1)

    def test_pages_require_login(self):
        client = Client()
        self.assertEqual(client.get("/").status_code, 302)
        client.login(username="alice", password="password123")
        self.assertEqual(client.get("/").status_code, 200)


class WebsocketTests(TransactionTestCase):
    def setUp(self):
        self.a = User.objects.create_user("alice", password="password123")
        self.b = User.objects.create_user("bob", password="password123")
        row = request_friend(self.a, "bob")
        accept_friend(self.b, row.pk)
        self.thread = Thread.get_or_create_for(self.a.pk, self.b.pk)

    async def test_ws_ignores_client_sender_and_persists(self):
        communicator = WebsocketCommunicator(
            application,
            f"/ws/thread/{self.thread.pk}/",
            headers=[
                (b"host", b"localhost"),
                (b"origin", b"http://localhost"),
            ],
        )
        communicator.scope["user"] = self.a
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to(
            {"type": "chat", "body": "ping", "sender_id": 999, "sender": "hacker"}
        )
        event = await communicator.receive_json_from()
        self.assertEqual(event["type"], "chat")
        self.assertEqual(event["message"]["body"], "ping")
        self.assertEqual(event["message"]["sender_id"], self.a.pk)
        await communicator.disconnect()
        count = await sync_to_async(Message.objects.filter(thread=self.thread).count)()
        self.assertEqual(count, 1)
