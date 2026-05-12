import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .rate_limit import register_message_attempt


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for one-to-one chat.

    URL: ws://server/ws/chat/<other_user_id>/
    """

    async def connect(self):
        self.user = self.scope['user']
        user_model = get_user_model()
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']

        if self.user.role == 'admin':
            await self.close()
            return

        try:
            self.other_user = await self.get_user(self.other_user_id, user_model)
            if not self.other_user or self.other_user.role == 'admin':
                await self.close()
                return
        except Exception:
            await self.close()
            return

        user_ids = sorted([int(self.user.id), int(self.other_user_id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.mark_messages_as_read()
        await self.accept()

        messages = await self.get_messages_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action', 'send')

        if action == 'delete_messages':
            message_ids = data.get('message_ids') or []
            try:
                message_ids = [int(message_id) for message_id in message_ids]
            except (TypeError, ValueError):
                return

            if not message_ids:
                return

            deleted_ids = await self.delete_own_messages(message_ids)
            if not deleted_ids:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_deleted',
                    'message_ids': deleted_ids,
                }
            )
            await self.send_conversation_updates()
            return

        message_text = data.get('message', '').strip()
        if not message_text:
            return

        rate_limit_result = await self.check_rate_limit()
        if rate_limit_result['status'] == 'muted':
            await self.send(text_data=json.dumps({
                'type': 'chat_muted',
                'remaining_seconds': rate_limit_result['remaining_seconds'],
            }))
            return

        if rate_limit_result['status'] == 'warning':
            await self.send(text_data=json.dumps({
                'type': 'spam_warning',
                'message': 'Вы отправляете сообщения слишком часто. Пожалуйста, не спамьте.',
            }))

        message = await self.save_message(message_text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message['id'],
                'message': message['text'],
                'sender_id': int(self.user.id),
                'sender_name': self.user.get_full_name() or self.user.username,
                'timestamp': message['timestamp'],
            }
        )

        await self.channel_layer.group_send(
            f'notifications_{self.other_user_id}',
            {
                'type': 'new_message',
                'sender_id': int(self.user.id),
                'sender_name': self.user.get_full_name() or self.user.username,
                'message': message['text'],
                'unread_count': await self.get_unread_count_for(self.other_user, self.user),
            }
        )

        await self.send_conversation_updates()

    async def chat_message(self, event):
        if event['sender_id'] != int(self.user.id):
            await self.mark_messages_as_read()
            unread_count = await self.get_unread_count_for(self.user, self.other_user)
            await self.channel_layer.group_send(
                f'notifications_{self.user.id}',
                {
                    'type': 'new_message',
                    'sender_id': event['sender_id'],
                    'sender_name': event['sender_name'],
                    'message': event['message'],
                    'unread_count': unread_count,
                }
            )

        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event.get('timestamp', ''),
        }))

    async def messages_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'messages_deleted',
            'message_ids': event['message_ids'],
        }))

    @database_sync_to_async
    def check_rate_limit(self):
        return register_message_attempt(self.user.id)

    @database_sync_to_async
    def get_user(self, user_id, user_model):
        try:
            return user_model.objects.get(id=user_id)
        except user_model.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, text):
        from .models import Message

        message = Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            text=text,
        )
        return {
            'id': message.id,
            'text': message.text,
            'timestamp': message.created_at.isoformat(),
        }

    @database_sync_to_async
    def delete_own_messages(self, message_ids):
        from .models import Message

        messages = Message.objects.filter(
            id__in=message_ids,
            sender=self.user,
            receiver=self.other_user,
        )
        deleted_ids = list(messages.values_list('id', flat=True))
        if deleted_ids:
            messages.delete()
        return deleted_ids

    @database_sync_to_async
    def get_messages_history(self):
        from .models import Message

        messages = Message.get_conversation(self.user, self.other_user)
        return [
            {
                'id': message.id,
                'text': message.text,
                'sender_id': message.sender.id,
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'timestamp': message.created_at.isoformat(),
                'is_read': message.is_read,
            }
            for message in messages
        ]

    @database_sync_to_async
    def get_unread_count_for(self, receiver, sender):
        from .models import Message

        return Message.objects.filter(
            receiver=receiver,
            sender=sender,
            is_read=False,
        ).count()

    @database_sync_to_async
    def get_conversation_state(self, viewer, partner):
        from .models import Message
        from .presence import get_last_seen_at, is_user_online

        last_message = Message.get_conversation(viewer, partner).order_by('-created_at').first()
        unread_count = Message.objects.filter(
            sender=partner,
            receiver=viewer,
            is_read=False,
        ).count()
        profile = getattr(partner, 'profile', None)
        avatar = getattr(profile, 'avatar', None)
        last_seen_at = get_last_seen_at(partner)

        return {
            'partner_id': int(partner.id),
            'partner_name': (partner.get_full_name() or partner.username).strip(),
            'partner_role': partner.get_role_display(),
            'partner_avatar_url': avatar.url if avatar else '',
            'has_messages': bool(last_message),
            'last_message': (last_message.text[:40] if last_message else ''),
            'last_message_sender_id': int(last_message.sender_id) if last_message else None,
            'last_message_time': last_message.created_at.isoformat() if last_message else '',
            'unread_count': unread_count,
            'partner_is_online': is_user_online(partner.id),
            'partner_last_seen_at': last_seen_at.isoformat() if last_seen_at else '',
        }

    async def send_conversation_updates(self):
        sender_state = await self.get_conversation_state(self.user, self.other_user)
        receiver_state = await self.get_conversation_state(self.other_user, self.user)

        await self.channel_layer.group_send(
            f'notifications_{self.user.id}',
            {
                'type': 'conversation_updated',
                'conversation': sender_state,
            }
        )
        await self.channel_layer.group_send(
            f'notifications_{self.other_user.id}',
            {
                'type': 'conversation_updated',
                'conversation': receiver_state,
            }
        )

    @database_sync_to_async
    def mark_messages_as_read(self):
        from .models import Message

        Message.mark_as_read(self.user, self.other_user)
