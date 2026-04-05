import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket потребитель для уведомлений (новые сообщения и т.д.).
    Каждый пользователь подключается к своей личной группе уведомлений.
    """

    async def connect(self):
        self.user = self.scope['user']

        logger.info(f'NotificationConsumer connect: user={self.user}, authenticated={self.user.is_authenticated}')

        if not self.user.is_authenticated:
            logger.warning('NotificationConsumer: anonymous user, closing')
            await self.close()
            return

        # Личная группа уведомлений пользователя
        self.group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f'NotificationConsumer accepted, group={self.group_name}')

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f'NotificationConsumer disconnected, group={self.group_name}')

    async def new_message(self, event):
        """Отправка уведомления о новом сообщении в WebSocket."""
        logger.info(f'NotificationConsumer sending new_message: sender={event.get("sender_id")}, unread={event.get("unread_count")}')
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event['message'],
            'unread_count': event['unread_count'],
        }))
