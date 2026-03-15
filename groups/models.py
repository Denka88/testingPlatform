from django.db import models
from django.conf import settings


class Group(models.Model):
    """Группа студентов с уникальным названием"""
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название группы',
        help_text='Например: ИС-2/25 или 11ИС-1/26'
    )
    admission_year = models.IntegerField(
        verbose_name='Год поступления',
        help_text='Год, когда студенты поступили в учебное заведение'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['admission_year', 'name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Учебный предмет/дисциплина"""
    name = models.CharField(
        max_length=200,
        verbose_name='Название предмета'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='subjects',
        limit_choices_to={'role': 'teacher'},
        verbose_name='Преподаватели'
    )
    groups = models.ManyToManyField(
        Group,
        related_name='subjects',
        verbose_name='Группы'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
        ordering = ['name']

    def __str__(self):
        return self.name
