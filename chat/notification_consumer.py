import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket потребитель для уведомлений (новые сообщения и т.д.).
    Каждый пользователь подключается к своей личной группе уведомлений.
    """

    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Личная группа уведомлений пользователя
        self.group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def new_message(self, event):
        """Отправка уведомления о новом сообщении в WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event['message'],
            'unread_count': event['unread_count'],
        }))
