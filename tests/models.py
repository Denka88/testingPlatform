from django.db import models
from django.conf import settings


class Test(models.Model):
    """Тест для проверки знаний студентов"""
    subject = models.ForeignKey(
        'groups.Subject',
        on_delete=models.CASCADE,
        related_name='tests',
        verbose_name='Предмет'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Название теста'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    time_limit = models.PositiveIntegerField(
        default=60,
        verbose_name='Время на прохождение (минут)',
        help_text='Время в минутах на прохождение теста'
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name='Опубликован',
        help_text='Если отмечено, тест доступен студентам'
    )
    show_correct_answers = models.BooleanField(
        default=True,
        verbose_name='Показывать правильные ответы',
        help_text='Показывать ли правильные ответы после прохождения'
    )
    groups = models.ManyToManyField(
        'groups.Group',
        related_name='tests',
        verbose_name='Группы',
        help_text='Группы, которым доступен тест'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tests',
        limit_choices_to={'role': 'teacher'},
        verbose_name='Создал преподаватель'
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
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.subject.name})"

    def duplicate(self):
        """Создает копию теста с тем же названием + копия"""
        new_test = Test.objects.create(
            subject=self.subject,
            title=f"{self.title} (копия)",
            description=self.description,
            time_limit=self.time_limit,
            is_published=False,
            show_correct_answers=self.show_correct_answers,
            created_by=self.created_by
        )
        # Копируем вопросы
        for question in self.questions.all():
            question.duplicate_to(new_test)
        # Копируем группы
        new_test.groups.set(self.groups.all())
        return new_test


class Question(models.Model):
    """Вопрос теста"""
    QUESTION_TYPES = [
        ('single', 'Один правильный ответ'),
        ('multiple', 'Несколько правильных ответов'),
    ]

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Тест'
    )
    text = models.TextField(
        verbose_name='Текст вопроса'
    )
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default='single',
        verbose_name='Тип вопроса'
    )
    image = models.ImageField(
        upload_to='questions/',
        null=True,
        blank=True,
        verbose_name='Изображение к вопросу'
    )
    code_snippet = models.TextField(
        blank=True,
        verbose_name='Фрагмент кода',
        help_text='Код для вопроса (подсветка синтаксиса)'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок отображения'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Вопрос {self.order}: {self.text[:50]}..."

    def duplicate_to(self, new_test):
        """Копирует вопрос в другой тест"""
        new_question = Question.objects.create(
            test=new_test,
            text=self.text,
            question_type=self.question_type,
            image=self.image,
            code_snippet=self.code_snippet,
            order=self.order
        )
        # Копируем ответы
        for answer in self.answers.all():
            answer.duplicate_to(new_question)
        return new_question


class Answer(models.Model):
    """Вариант ответа на вопрос"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос'
    )
    text = models.TextField(
        verbose_name='Текст ответа'
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Правильный ответ'
    )
    image = models.ImageField(
        upload_to='answers/',
        null=True,
        blank=True,
        verbose_name='Изображение к ответу'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок отображения'
    )

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['order']

    def __str__(self):
        return self.text[:50]

    def duplicate_to(self, new_question):
        """Копирует ответ в другой вопрос"""
        return Answer.objects.create(
            question=new_question,
            text=self.text,
            is_correct=self.is_correct,
            image=self.image,
            order=self.order
        )
