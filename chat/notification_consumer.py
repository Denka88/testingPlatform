import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .presence import (
    get_presence_payload,
    get_related_user_ids,
    mark_connection_active,
    mark_connection_idle,
    mark_user_connected,
    mark_user_disconnected,
    update_last_seen,
)


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        self.is_active = True

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()
        became_online = await sync_to_async(mark_user_connected)(self.user.id)
        if became_online:
            await self.broadcast_presence_update()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

        if getattr(self, 'user', None) and self.user.is_authenticated:
            became_offline = await sync_to_async(mark_user_disconnected)(self.user.id, self.is_active)
            if became_offline:
                await sync_to_async(update_last_seen)(self.user)
                await self.broadcast_presence_update()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data or not getattr(self, 'user', None) or not self.user.is_authenticated:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        event_type = data.get('type')

        if event_type == 'presence_ping':
            await self.handle_presence_ping()
        elif event_type == 'presence_idle':
            await self.handle_presence_idle()

    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event['message'],
            'unread_count': event['unread_count'],
        }))

    async def conversation_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'conversation_updated',
            'conversation': event['conversation'],
        }))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'presence': event['presence'],
        }))

    async def broadcast_presence_update(self):
        presence = await sync_to_async(get_presence_payload)(self.user)
        related_user_ids = await sync_to_async(get_related_user_ids)(self.user.id)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'presence_update',
                'presence': presence,
            }
        )

        for user_id in related_user_ids:
            await self.channel_layer.group_send(
                f'notifications_{user_id}',
                {
                    'type': 'presence_update',
                    'presence': presence,
                }
            )

    async def handle_presence_ping(self):
        if self.is_active:
            return

        self.is_active = True
        became_online = await sync_to_async(mark_connection_active)(self.user.id)
        if became_online:
            await self.broadcast_presence_update()

    async def handle_presence_idle(self):
        if not self.is_active:
            return

        self.is_active = False
        became_offline = await sync_to_async(mark_connection_idle)(self.user.id)
        if became_offline:
            await sync_to_async(update_last_seen)(self.user)
            await self.broadcast_presence_update()
