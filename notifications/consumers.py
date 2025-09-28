import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'message': 'WebSocket baglantisi kuruldu'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"WebSocket baglantisi kapandi: {close_code}")

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["content"]))

    async def receive(self, text_data):
         # Gelen mesajlarý iþle
        try:
            data = json.loads(text_data)
            await self.send(text_data=json.dumps({
                'message': f"Mesaj alindi: {data}"
            }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Gecersiz JSON formati'
            }))
        pass
