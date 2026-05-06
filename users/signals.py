from django.db.backends.signals import connection_created
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создаёт профиль при создании нового пользователя.
    """
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    Сохраняет профиль при сохранении пользователя.
    """
    # Проверяем, существует ли профиль (может не существовать для старых записей)
    profile, _ = Profile.objects.get_or_create(user=instance)
    profile.save()
