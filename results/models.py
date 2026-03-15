from django.db import models
from django.conf import settings


class Result(models.Model):
    """Результат прохождения теста студентом"""
    GRADE_CHOICES = [
        (2, '2 (Неудовлетворительно)'),
        (3, '3 (Удовлетворительно)'),
        (4, '4 (Хорошо)'),
        (5, '5 (Отлично)'),
    ]

    test = models.ForeignKey(
        'tests.Test',
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='Тест'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_results',
        limit_choices_to={'role': 'student'},
        verbose_name='Студент'
    )
    grade = models.PositiveSmallIntegerField(
        choices=GRADE_CHOICES,
        null=True,
        blank=True,
        verbose_name='Оценка',
        help_text='Оценка за тест (2-5) или пусто, если не проверено'
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время начала'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время завершения'
    )
    correct_answers_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество верных ответов'
    )
    total_questions = models.PositiveIntegerField(
        default=0,
        verbose_name='Общее количество вопросов'
    )
    device_info = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Устройство',
        help_text='Информация об устройстве, с которого проходил тест'
    )
    tab_switches_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Переключения вкладок',
        help_text='Количество раз, когда страница становилась неактивной'
    )
    is_reset = models.BooleanField(
        default=False,
        verbose_name='Сброшен',
        help_text='Если отмечено, студент может пройти тест заново'
    )

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
        ordering = ['-completed_at', '-started_at']
        unique_together = ['test', 'student', 'is_reset']

    def __str__(self):
        return f"{self.student.last_name} {self.student.first_name} - {self.test.title} ({self.grade or 'Не проверено'})"

    @property
    def duration_seconds(self):
        """Возвращает длительность прохождения в секундах"""
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    @property
    def percentage(self):
        """Возвращает процент правильных ответов"""
        if self.total_questions == 0:
            return 0
        return int((self.correct_answers_count / self.total_questions) * 100)


class StudentAnswer(models.Model):
    """Выбранные ответы студента"""
    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='Результат'
    )
    question = models.ForeignKey(
        'tests.Question',
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='Вопрос'
    )
    answers = models.ManyToManyField(
        'tests.Answer',
        related_name='student_answers',
        verbose_name='Выбранные ответы'
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Верно ли отвечено'
    )

    class Meta:
        verbose_name = 'Ответ студента'
        verbose_name_plural = 'Ответы студентов'

    def __str__(self):
        return f"Ответ на вопрос: {self.question.text[:50]}..."
