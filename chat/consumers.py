from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from chat.models import UserStatus
from .models import ChatThread, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope["url_route"]["kwargs"]["thread_id"]
        self.group_name = f"chat_{self.thread_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

            # Sohbete bağlanınca diğer kullanıcıya read event gönder
            await self.mark_messages_read()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type", "message")

        if msg_type == "message":
            text = data.get("message", "")
            msg = await self.save_message(self.user.id, text)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat_message",
                    "sender": msg.sender.username,
                    "message": msg.text,
                    "file_url": msg.file.url if msg.file else None,
                    "timestamp": str(msg.timestamp),
                    "read": msg.read,
                    "id": msg.id,
                },
            )

        elif msg_type == "delete":
            msg_id = data.get("id")
            await self.delete_message(msg_id)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "delete_event",
                    "id": msg_id,
                },
            )

        elif msg_type == "read":
            # Handle both bulk read and single message read
            if 'id' in data:
                msg_id = data.get("id")
                await self.mark_as_read(msg_id)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "read_event",
                        "id": msg_id,
                    },
                )
            else:
                await self.mark_messages_read()

        elif msg_type == "typing":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "typing_event",
                    "user": self.user.username,
                    "is_typing": True,
                },
            )

        elif msg_type == "stop_typing":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "typing_event",
                    "user": self.user.username,
                    "is_typing": False,
                },
            )
        
        elif msg_type == "edit":
            msg_id = data.get("id")
            new_text = data.get("text", "")
            await self.edit_message(msg_id, new_text)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "edit_event",
                    "id": msg_id,
                    "text": new_text
                },
            )

        elif msg_type == "reaction":
            msg_id = data.get("id")
            emoji = data.get("emoji")
            action = data.get("action")
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "reaction_event",
                    "id": msg_id,
                    "emoji": emoji,
                    "user": self.user.username,
                    "action": action
                },
            )

    async def edit_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "edit",
            "id": event["id"],
            "text": event["text"]
        }))

    async def delete_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "delete",
            "id": event["id"]
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "user": event["user"],
            "is_typing": event["is_typing"]
        }))

    async def read_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "read",
            "id": event["id"],
        }))

    async def reaction_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "reaction",
            "id": event["id"],
            "emoji": event["emoji"],
            "user": event["user"],
            "action": event["action"]
        }))

    @sync_to_async
    def save_message(self, sender_id, text, file=None):
        thread = ChatThread.objects.get(id=self.thread_id)
        sender = User.objects.get(id=sender_id)
        return Message.objects.create(thread=thread, sender=sender, text=text, file=file)

    @sync_to_async
    def mark_messages_read(self):
        thread = ChatThread.objects.get(id=self.thread_id)
        Message.objects.filter(thread=thread).exclude(sender=self.user).update(read=True)

    @sync_to_async
    def delete_message(self, msg_id):
        try:
            msg = Message.objects.get(id=msg_id, sender=self.user)
            msg.delete()
        except Message.DoesNotExist:
            pass
    
    @sync_to_async
    def edit_message(self, msg_id, new_text):
        try:
            msg = Message.objects.get(id=msg_id, sender=self.user)
            msg.text = new_text
            msg.save()
        except Message.DoesNotExist:
            pass

    @sync_to_async
    def mark_as_read(self, msg_id):
        try:
            msg = Message.objects.get(id=msg_id)
            msg.read = True
            msg.save()
        except Message.DoesNotExist:
            pass

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            await self.set_online(user)
            await self.channel_layer.group_add("presence_updates", self.channel_name)
            await self.accept()

            await self.channel_layer.group_send(
                "presence_updates",
                {"type": "presence_update", "user": user.username, "status": "online"},
            )

    async def disconnect(self, close_code):
        user = self.scope["user"]
        await self.set_offline(user)
        await self.channel_layer.group_send(
            "presence_updates",
            {"type": "presence_update", "user": user.username, "status": "offline"},
        )
        await self.channel_layer.group_discard("presence_updates", self.channel_name)

    async def presence_update(self, event):
        await self.send(json.dumps(event))

    @sync_to_async
    def set_online(self, user):
        status, _ = UserStatus.objects.get_or_create(user=user)
        status.is_online = True
        status.save()

    @sync_to_async
    def set_offline(self, user):
        status, _ = UserStatus.objects.get_or_create(user=user)
        status.is_online = False
        status.save()