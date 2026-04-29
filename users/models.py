from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Администратор'
    TEACHER = 'teacher', 'Преподаватель'
    STUDENT = 'student', 'Студент'


class User(AbstractUser):
    """Р Р°СЃС€РёСЂРµРЅРЅР°СЏ РјРѕРґРµР»СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ СЃ СЂРѕР»СЏРјРё"""
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        verbose_name='Р РѕР»СЊ'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='РўРµР»РµС„РѕРЅ'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Р”Р°С‚Р° СЂРѕР¶РґРµРЅРёСЏ'
    )
    patronymic = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='РћС‚С‡РµСЃС‚РІРѕ'
    )

    class Meta:
        verbose_name = 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ'
        verbose_name_plural = 'РџРѕР»СЊР·РѕРІР°С‚РµР»Рё'

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_teacher(self):
        return self.role == UserRole.TEACHER

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT


class Profile(models.Model):
    """РџСЂРѕС„РёР»СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ СЃ Р°РІР°С‚Р°СЂРѕРј Рё РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕР№ РёРЅС„РѕСЂРјР°С†РёРµР№"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='РђРІР°С‚Р°СЂ'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Рћ СЃРµР±Рµ'
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Р“СЂСѓРїРїР°',
        help_text='Р“СЂСѓРїРїР°, Рє РєРѕС‚РѕСЂРѕР№ РїСЂРёРЅР°РґР»РµР¶РёС‚ СЃС‚СѓРґРµРЅС‚'
    )
    real_group = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Р РµР°Р»СЊРЅР°СЏ РіСЂСѓРїРїР°',
        help_text='Р”Р»СЏ СЃС‚СѓРґРµРЅС‚РѕРІ РїРѕСЃР»Рµ 11 РєР»Р°СЃСЃР° (РЅР°РїСЂРёРјРµСЂ, 11РРЎ-1/26)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Р”Р°С‚Р° СЃРѕР·РґР°РЅРёСЏ'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Р”Р°С‚Р° РѕР±РЅРѕРІР»РµРЅРёСЏ'
    )
    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='РџРѕСЃР»РµРґРЅРёР№ Р·Р°С…РѕРґ РІ СЃРµС‚СЊ'
    )

    class Meta:
        verbose_name = 'РџСЂРѕС„РёР»СЊ'
        verbose_name_plural = 'РџСЂРѕС„РёР»Рё'

    def __str__(self):
        return f"РџСЂРѕС„РёР»СЊ: {self.user.last_name} {self.user.first_name}"

    def get_display_group(self):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РіСЂСѓРїРїСѓ РґР»СЏ РѕС‚РѕР±СЂР°Р¶РµРЅРёСЏ СЃ СѓС‡РµС‚РѕРј СЂРµР°Р»СЊРЅРѕР№ РіСЂСѓРїРїС‹"""
        if self.real_group:
            return f"{self.group.name} ({self.real_group})" if self.group else self.real_group
        return self.group.name if self.group else None
