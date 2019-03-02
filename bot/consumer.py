from channels.generic.websocket import AsyncWebsocketConsumer
import json

from users.models import WebSocketToken


class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.authenticate()

    async def authenticate(self):
        websocket_token = self.scope['url_route']['kwargs']['websocket_token']
        valid = WebSocketToken.validate(websocket_token)
        self.room_name = valid
        self.room_group_name = 'log_%s' % self.room_name

        if valid:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()


async def disconnect(self, close_code):
    # Leave room group
    await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name
    )


# Receive message from WebSocket
async def receive(self, text_data):
    text_data_json = json.loads(text_data)
    message = text_data_json['message']

    # Send message to room group
    await self.channel_layer.group_send(
        self.room_group_name,
        {
            'type': 'log_message',
            'message': message
        }
    )


# Receive message from room group
async def log_message(self, event):
    message = event['message']

    # Send message to WebSocket
    await self.send(text_data=json.dumps({
        'message': message
    }))
