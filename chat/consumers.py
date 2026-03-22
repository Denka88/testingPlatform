import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket потребитель для чата один-на-один.
    
    URL: ws://server/ws/chat/<other_user_id>/
    """

    async def connect(self):
        self.user = self.scope['user']
        
        # Получаем модель пользователя внутри async метода
        User = get_user_model()
        
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']

        # Проверка: пользователь не должен быть администратором
        if self.user.role == 'admin':
            await self.close()
            return

        # Проверка: другой пользователь существует и не администратор
        try:
            self.other_user = await self.get_user(self.other_user_id, User)
            if not self.other_user or self.other_user.role == 'admin':
                await self.close()
                return
        except Exception:
            await self.close()
            return

        # Создаем уникальное имя группы для этой пары пользователей
        # Сортируем ID чтобы группа была одинаковой для обоих направлений
        user_ids = sorted([int(self.user.id), int(self.other_user_id)])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Помечаем сообщения как прочитанные
        await self.mark_messages_as_read()

        await self.accept()

        # Отправляем историю сообщений при подключении
        messages = await self.get_messages_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        # Покидаем группу
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Получение сообщения от WebSocket.
        """
        data = json.loads(text_data)
        message_text = data.get('message', '').strip()

        if not message_text:
            return

        # Сохраняем сообщение в базу данных
        await self.save_message(message_text)

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_text,
                'sender_id': int(self.user.id),
                'sender_name': self.user.get_full_name() or self.user.username,
                'timestamp': data.get('timestamp', '')
            }
        )

    async def chat_message(self, event):
        """
        Отправка сообщения в WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event.get('timestamp', '')
        }))

    @database_sync_to_async
    def get_user(self, user_id, User):
        """
        Получить пользователя по ID.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, text):
        """
        Сохранить сообщение в базу данных.
        """
        from .models import Message
        Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            text=text
        )

    @database_sync_to_async
    def get_messages_history(self):
        """
        Получить историю сообщений между пользователями.
        """
        from .models import Message
        messages = Message.get_conversation(self.user, self.other_user)
        return [
            {
                'id': m.id,
                'text': m.text,
                'sender_id': m.sender.id,
                'sender_name': m.sender.get_full_name() or m.sender.username,
                'timestamp': m.created_at.isoformat(),
                'is_read': m.is_read
            }
            for m in messages
        ]

    @database_sync_to_async
    def mark_messages_as_read(self):
        """
        Пометить сообщения как прочитанные.
        """
        from .models import Message
        Message.mark_as_read(self.user, self.other_user)
