# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from groups.models import Group, Subject
from tests.models import Test, Question, Answer
from users.models import User, Profile


class Command(BaseCommand):
    help = 'Заполнение БД тестовыми данными: группы, предметы, тесты, вопросы, ответы'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        teacher = User.objects.get(username='teacher1')

        # --- Создаём новых студентов ---
        new_students_data = [
            ('student4', 'ИС3/23'),
            ('student5', 'ИП4/22'),
        ]
        for username, _ in new_students_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'role': 'student',
                    'first_name': username.capitalize(),
                    'last_name': 'Студентов',
                    'email': f'{username}@example.com',
                }
            )
            if created:
                user.set_password('django_password')
                user.save()
                self.stdout.write(f'[OK] Создан студент: {username}')

        students = list(User.objects.filter(role='student'))

        # --- Все группы (старые + новые) ---
        all_groups = list(Group.objects.all())

        # --- Группы ---
        group_is, _ = Group.objects.get_or_create(
            name='ИС3/23', defaults={'admission_year': 2023}
        )
        group_ip, _ = Group.objects.get_or_create(
            name='ИП4/22', defaults={'admission_year': 2022}
        )
        self.stdout.write(f'[OK] Группы: {group_is.name}, {group_ip.name}')

        # --- Привязка студентов к группам ---
        for i, student in enumerate(students):
            group = group_is if i % 2 == 0 else group_ip
            profile, created = Profile.objects.get_or_create(
                user=student, defaults={'group': group}
            )
            if not profile.group:
                profile.group = group
                profile.save()
            self.stdout.write(f'     {student.username} -> {profile.group.name}')

        # --- Предметы (каждый привязан к НЕСКОЛЬКИМ группам) ---
        lit, _ = Subject.objects.get_or_create(
            name='Литература',
            defaults={
                'description': 'Курс русской и зарубежной литературы. Анализ произведений, сочинения, эссе.'
            }
        )
        lit.teachers.set([teacher])
        lit.groups.set([group_is, group_ip])
        lit.save()
        self.stdout.write(f'[OK] Предмет: {lit.name} -> группы: ИС3/23, ИП4/22')

        inf, _ = Subject.objects.get_or_create(
            name='Информатика',
            defaults={
                'description': 'Основы программирования, алгоритмы, базы данных и информационные системы.'
            }
        )
        inf.teachers.set([teacher])
        inf.groups.set([group_is, group_ip])
        inf.save()
        self.stdout.write(f'[OK] Предмет: {inf.name} -> группы: ИС3/23, ИП4/22')

        # --- Данные тестов ---
        test_data = {
            lit: [
                {
                    'title': 'Русская литература XIX века',
                    'description': 'Тест по произведениям Пушкина, Лермонтова, Гоголя и Достоевского.',
                    'time_limit': 45,
                    'questions': [
                        {
                            'text': 'Кто является автором романа «Евгений Онегин»?',
                            'type': 'single',
                            'answers': [
                                ('А.С. Пушкин', True),
                                ('М.Ю. Лермонтов', False),
                                ('Н.В. Гоголь', False),
                                ('И.С. Тургенев', False),
                            ]
                        },
                        {
                            'text': 'Какое произведение написал Ф.М. Достоевский?',
                            'type': 'single',
                            'answers': [
                                ('«Война и мир»', False),
                                ('«Преступление и наказание»', True),
                                ('«Мёртвые души»', False),
                                ('«Отцы и дети»', False),
                            ]
                        },
                        {
                            'text': 'Какие произведения принадлежат перу Н.В. Гоголя? (Несколько вариантов)',
                            'type': 'multiple',
                            'answers': [
                                ('«Ревизор»', True),
                                ('«Мёртвые души»', True),
                                ('«Герой нашего времени»', False),
                                ('«Шинель»', True),
                            ]
                        },
                        {
                            'text': 'В каком году был опубликован роман «Отцы и дети» И.С. Тургенева?',
                            'type': 'single',
                            'answers': [
                                ('1856', False),
                                ('1862', True),
                                ('1869', False),
                                ('1875', False),
                            ]
                        },
                        {
                            'text': 'Кто из авторов написал стихотворение «Бородино»?',
                            'type': 'single',
                            'answers': [
                                ('А.С. Пушкин', False),
                                ('Ф.И. Тютчев', False),
                                ('М.Ю. Лермонтов', True),
                                ('А.А. Фет', False),
                            ]
                        },
                    ]
                },
                {
                    'title': 'Зарубежная литература',
                    'description': 'Тест по зарубежной классике: Шекспир, Сервантес, Ремарк и другие.',
                    'time_limit': 40,
                    'questions': [
                        {
                            'text': 'Кто написал трагедию «Гамлет»?',
                            'type': 'single',
                            'answers': [
                                ('Уильям Шекспир', True),
                                ('Мольер', False),
                                ('Иоганн Гёте', False),
                                ('Лопе де Вега', False),
                            ]
                        },
                        {
                            'text': 'Как зовут главного героя романа «Дон Кихот»?',
                            'type': 'single',
                            'answers': [
                                ('Алонсо Кихано', True),
                                ('Санчо Панса', False),
                                ('Дон Жуан', False),
                                ('Дориан Грей', False),
                            ]
                        },
                        {
                            'text': 'Какие произведения написал Эрих Мария Ремарк? (Несколько вариантов)',
                            'type': 'multiple',
                            'answers': [
                                ('«На Западном фронте без перемен»', True),
                                ('«Три товарища»', True),
                                ('«Старик и море»', False),
                                ('«Триумфальная арка»', True),
                            ]
                        },
                        {
                            'text': 'Кто написал роман «Сто лет одиночества»?',
                            'type': 'single',
                            'answers': [
                                ('Марио Варгас Льоса', False),
                                ('Габриэль Гарсиа Маркес', True),
                                ('Хулио Кортасар', False),
                                ('Хорхе Борхес', False),
                            ]
                        },
                        {
                            'text': 'Какое произведение принадлежит Францу Кафке?',
                            'type': 'single',
                            'answers': [
                                ('«Процесс»', True),
                                ('«Тошнота»', False),
                                ('«Чума»', False),
                                ('«Степной волк»', False),
                            ]
                        },
                    ]
                },
            ],
            inf: [
                {
                    'title': 'Основы алгоритмов',
                    'description': 'Тест по основам алгоритмизации: сортировки, поиск, сложность.',
                    'time_limit': 35,
                    'questions': [
                        {
                            'text': 'Какова временная сложность бинарного поиска в отсортированном массиве?',
                            'type': 'single',
                            'answers': [
                                ('O(n)', False),
                                ('O(log n)', True),
                                ('O(n^2)', False),
                                ('O(1)', False),
                            ]
                        },
                        {
                            'text': 'Какие алгоритмы сортировки имеют сложность O(n log n)? (Несколько вариантов)',
                            'type': 'multiple',
                            'answers': [
                                ('Сортировка пузырьком', False),
                                ('Сортировка слиянием', True),
                                ('Быстрая сортировка', True),
                                ('Сортировка вставками', False),
                            ]
                        },
                        {
                            'text': 'Что такое рекурсия?',
                            'type': 'single',
                            'answers': [
                                ('Цикл в программе', False),
                                ('Вызов функцией самой себя', True),
                                ('Тип данных', False),
                                ('Метод сортировки', False),
                            ]
                        },
                        {
                            'text': 'Какая структура данных работает по принципу FIFO?',
                            'type': 'single',
                            'answers': [
                                ('Стек', False),
                                ('Очередь', True),
                                ('Дек', False),
                                ('Дерево', False),
                            ]
                        },
                        {
                            'text': 'Какие структуры данных являются линейными? (Несколько вариантов)',
                            'type': 'multiple',
                            'answers': [
                                ('Массив', True),
                                ('Связный список', True),
                                ('Дерево', False),
                                ('Граф', False),
                            ]
                        },
                    ]
                },
                {
                    'title': 'Базы данных SQL',
                    'description': 'Тест по основам реляционных баз данных и SQL-запросов.',
                    'time_limit': 40,
                    'questions': [
                        {
                            'text': 'Какая команда SQL используется для выборки данных?',
                            'type': 'single',
                            'answers': [
                                ('FETCH', False),
                                ('GET', False),
                                ('SELECT', True),
                                ('RETRIEVE', False),
                            ]
                        },
                        {
                            'text': 'Какие из операторов используются для фильтрации? (Несколько вариантов)',
                            'type': 'multiple',
                            'answers': [
                                ('WHERE', True),
                                ('HAVING', True),
                                ('ORDER BY', False),
                                ('GROUP BY', False),
                            ]
                        },
                        {
                            'text': 'Что такое первичный ключ (PRIMARY KEY)?',
                            'type': 'single',
                            'answers': [
                                ('Пароль для доступа к базе', False),
                                ('Уникальный идентификатор записи в таблице', True),
                                ('Связь между двумя таблицами', False),
                                ('Индекс для ускорения запросов', False),
                            ]
                        },
                        {
                            'text': 'Какой тип связи реализуется через внешнюю ссылку (FOREIGN KEY)?',
                            'type': 'single',
                            'answers': [
                                ('Один к одному', False),
                                ('Один ко многим', True),
                                ('Многие ко многим без промежуточной таблицы', False),
                                ('Ни один из перечисленных', False),
                            ]
                        },
                        {
                            'text': 'Какие команды относятся к DDL? (Несколько вариантов)',
                            'type': 'multiple',
                            'answers': [
                                ('CREATE', True),
                                ('INSERT', False),
                                ('ALTER', True),
                                ('DROP', True),
                            ]
                        },
                    ]
                },
            ],
        }

        for subject, tests_list in test_data.items():
            for test_info in tests_list:
                test, created = Test.objects.get_or_create(
                    title=test_info['title'],
                    defaults={
                        'subject': subject,
                        'description': test_info['description'],
                        'time_limit': test_info['time_limit'],
                        'is_published': True,
                        'show_correct_answers': False,
                        'created_by': teacher,
                    }
                )
                if created:
                    test.groups.set([group_is, group_ip])
                    self.stdout.write(f'[OK] Тест: {test.title}')

                    for q_info in test_info['questions']:
                        question = Question.objects.create(
                            test=test,
                            text=q_info['text'],
                            question_type=q_info['type'],
                        )
                        for ans_text, is_correct in q_info['answers']:
                            Answer.objects.create(
                                question=question,
                                text=ans_text,
                                is_correct=is_correct,
                            )
                        short = question.text[:60]
                        cnt = len(q_info['answers'])
                        self.stdout.write(f'     ? {short}... ({cnt} ответов)')

        self.stdout.write(self.style.SUCCESS('\nБаза данных успешно заполнена!'))
