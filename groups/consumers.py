# groups/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Baðlantýyý kabul et
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket baglantisi kuruldu'
        }))

    async def disconnect(self, close_code):
        # Baðlantý kapandýðýnda yapýlacaklar
        print(f"WebSocket baglantisi kapandi: {close_code}")

    async def receive(self, text_data):
        # Ýstemciden mesaj alýndýðýnda
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '')
            
            # Gelen mesajý iþle ve cevap gönder
            await self.send(text_data=json.dumps({
                'type': 'message_received',
                'message': f'Alinan mesaj: {message}'
            }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Gecersiz JSON formati'
            }))
