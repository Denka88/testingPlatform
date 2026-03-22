from django.db import models
from django.conf import settings
from django.db.models import Q


class Contact(models.Model):
    """
    Контакты пользователя.
    Каждый пользователь может добавлять других пользователей в контакты.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='Пользователь',
    )
    contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacted_by',
        verbose_name='Контакт',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        unique_together = ('user', 'contact')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} -> {self.contact}'


class Message(models.Model):
    """
    Сообщение между двумя пользователями.
    Чат один-на-один, история хранится бессрочно.
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель',
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Получатель',
    )
    text = models.TextField(verbose_name='Текст сообщения')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sender', 'receiver', 'created_at']),
            models.Index(fields=['receiver', 'is_read']),
        ]

    def __str__(self):
        return f'{self.sender} -> {self.receiver}: {self.text[:50]}'

    @classmethod
    def get_conversation(cls, user1, user2):
        """
        Получить все сообщения между двумя пользователями.
        """
        return cls.objects.filter(
            Q(sender=user1, receiver=user2) | Q(sender=user2, receiver=user1)
        ).select_related('sender', 'receiver')

    @classmethod
    def mark_as_read(cls, user, other_user):
        """
        Пометить все сообщения от other_user для user как прочитанные.
        """
        cls.objects.filter(
            sender=other_user,
            receiver=user,
            is_read=False
        ).update(is_read=True)
