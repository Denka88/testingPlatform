from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Администратор'
    TEACHER = 'teacher', 'Преподаватель'
    STUDENT = 'student', 'Студент'


class User(AbstractUser):
    """Расширенная модель пользователя с ролями"""
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        verbose_name='Роль'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

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
    """Профиль пользователя с аватаром и дополнительной информацией"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='О себе'
    )
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Группа',
        help_text='Группа, к которой принадлежит студент'
    )
    real_group = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Реальная группа',
        help_text='Для студентов после 11 класса (например, 11ИС-1/26)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f"Профиль: {self.user.last_name} {self.user.first_name}"

    def get_display_group(self):
        """Возвращает группу для отображения с учетом реальной группы"""
        if self.real_group:
            return f"{self.group.name} ({self.real_group})" if self.group else self.real_group
        return self.group.name if self.group else None
