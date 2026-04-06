"""
Скрипт для заполнения базы данных тестовыми данными.
Запуск: python manage.py shell < seed_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testingPlatform.settings')
django.setup()

from django.db import transaction
from groups.models import Group, Subject
from tests.models import Test, Question, Answer
from users.models import User, Profile

@transaction.atomic
def seed():
    # ─── Получаем преподавателя ───
    teacher = User.objects.get(username='teacher1')

    # ─── Получаем студентов ───
    students = list(User.objects.filter(role='student'))

    # ─── 1. Добавляем новые группы ───
    group_is, _ = Group.objects.get_or_create(
        name='ИС3/23',
        defaults={'admission_year': 2023}
    )
    group_ip, _ = Group.objects.get_or_create(
        name='ИП4/22',
        defaults={'admission_year': 2022}
    )
    print(f"✅ Группы: {group_is.name}, {group_ip.name}")

    # ─── Обновляем профили студентов — привязываем к новым группам ───
    # Распределяем студентов по группам и добавляем профили тем, у кого нет
    for i, student in enumerate(students):
        group = group_is if i % 2 == 0 else group_ip
        profile, created = Profile.objects.get_or_create(
            user=student,
            defaults={'group': group}
        )
        if not profile.group:
            profile.group = group
            profile.save()
        print(f"  📌 {student.username} → {profile.group.name}")

    # ─── 2. Добавляем новые предметы ───
    # Литература — привязываем к ИС3/23 и части студентов
    lit_subject, _ = Subject.objects.get_or_create(
        name='Литература',
        defaults={
            'description': 'Курс русской и зарубежной литературы. Анализ произведений, сочинения, эссе.',
        }
    )
    lit_subject.teachers.set([teacher])
    lit_subject.groups.set([group_is])
    lit_subject.save()
    print(f"✅ Предмет: {lit_subject.name}")

    # Информатика — привязываем к ИП4/22 и части студентов
    inf_subject, _ = Subject.objects.get_or_create(
        name='Информатика',
        defaults={
            'description': 'Основы программирования, алгоритмы, базы данных и информационные системы.',
        }
    )
    inf_subject.teachers.set([teacher])
    inf_subject.groups.set([group_ip])
    inf_subject.save()
    print(f"✅ Предмет: {inf_subject.name}")

    # ─── 3. Тесты, вопросы, ответы ───

    test_data = {
        lit_subject: [
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
        inf_subject: [
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
                            ('O(n²)', False),
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
                test.groups.set(subject.groups.all())
                print(f"✅ Тест: {test.title}")

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
                    print(f"  ❓ {question.text[:60]}... ({len(q_info['answers'])} ответов)")

    print("\n🎉 База данных успешно заполнена!")


if __name__ == '__main__':
    seed()
