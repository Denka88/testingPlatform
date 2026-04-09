"""
Скрипт для создания тестов преподавателя teacher2.
Запуск: python manage.py shell < seed_teacher2.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testingPlatform.settings')
django.setup()

from django.db import transaction
from groups.models import Subject
from tests.models import Test, Question, Answer
from users.models import User


@transaction.atomic
def seed():
    teacher = User.objects.get(username='teacher2')

    # Получаем предметы teacher2
    math_subject = Subject.objects.get(name='Математика', teachers=teacher)
    inf_subject = Subject.objects.get(name='Информатика', teachers=teacher)

    # Получаем группы из предмета Информатика (teacher1)
    inf_t1 = Subject.objects.get(name='Информатика')
    groups = list(inf_t1.groups.all())
    if not groups:
        from groups.models import Group
        group, _ = Group.objects.get_or_create(name='ИС3/23', defaults={'admission_year': 2023})
        groups = [group]

    tests_data = {
        math_subject: [
            {
                'title': 'Линейная алгебра',
                'description': 'Матрицы, определители, системы линейных уравнений.',
                'time_limit': 30,
                'questions': [
                    {
                        'text': 'Что такое определитель матрицы?',
                        'type': 'single',
                        'answers': [
                            ('Число, соответствующее квадратной матрице', True),
                            ('Тип матрицы', False),
                            ('Сумма всех элементов', False),
                            ('Произведение элементов главной диагонали', False),
                        ]
                    },
                    {
                        'text': 'Какие методы решения систем линейных уравнений существуют? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('Метод Гаусса', True),
                            ('Метод Крамера', True),
                            ('Метод Ньютона', False),
                            ('Метод подстановки', True),
                        ]
                    },
                    {
                        'text': 'Если определитель матрицы равен нулю, то матрица...',
                        'type': 'single',
                        'answers': [
                            ('Вырожденная', True),
                            ('Единичная', False),
                            ('Диагональная', False),
                            ('Симметричная', False),
                        ]
                    },
                    {
                        'text': 'Что такое ранг матрицы?',
                        'type': 'single',
                        'answers': [
                            ('Максимальное число линейно независимых строк или столбцов', True),
                            ('Количество строк матрицы', False),
                            ('Количество столбцов матрицы', False),
                            ('Сумма элементов матрицы', False),
                        ]
                    },
                    {
                        'text': 'Какие свойства определителя верны? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('При транспонировании определитель не меняется', True),
                            ('При перестановке двух строк определитель меняет знак', True),
                            ('Определитель всегда положителен', False),
                            ('Определитель единичной матрицы равен 1', True),
                        ]
                    },
                ]
            },
            {
                'title': 'Математический анализ',
                'description': 'Пределы, производные, интегралы.',
                'time_limit': 35,
                'questions': [
                    {
                        'text': 'Чему равен предел sin(x)/x при x, стремящемся к 0?',
                        'type': 'single',
                        'answers': [
                            ('1', True),
                            ('0', False),
                            ('Бесконечность', False),
                            ('-1', False),
                        ]
                    },
                    {
                        'text': 'Что такое производная функции?',
                        'type': 'single',
                        'answers': [
                            ('Скорость изменения функции', True),
                            ('Значение функции в точке', False),
                            ('Площадь под графиком', False),
                            ('Сумма всех значений', False),
                        ]
                    },
                    {
                        'text': 'Чему равна производная функции f(x) = x²?',
                        'type': 'single',
                        'answers': [
                            ('2x', True),
                            ('x²', False),
                            ('2', False),
                            ('x', False),
                        ]
                    },
                    {
                        'text': 'Какие правила дифференцирования верны? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('(uv)\' = u\'v + uv\'', True),
                            ('(u+v)\' = u\' + v\'', True),
                            ('(u/v)\' = u\'/v\'', False),
                            ('(sin x)\' = cos x', True),
                        ]
                    },
                    {
                        'text': 'Что показывает определённый интеграл? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('Площадь под кривой', True),
                            ('Приращение первообразной', True),
                            ('Скорость изменения функции', False),
                            ('Объём тела вращения', True),
                        ]
                    },
                ]
            },
        ],
        inf_subject: [
            {
                'title': 'Основы программирования Python',
                'description': 'Базовый синтаксис, типы данных, функции Python.',
                'time_limit': 30,
                'questions': [
                    {
                        'text': 'Какой тип данных является неизменяемым в Python?',
                        'type': 'single',
                        'answers': [
                            ('str (строка)', True),
                            ('list (список)', False),
                            ('dict (словарь)', False),
                            ('set (множество)', False),
                        ]
                    },
                    {
                        'text': 'Какие из следующих являются встроенными типами Python? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('tuple (кортеж)', True),
                            ('arraylist', False),
                            ('frozenset', True),
                            ('queue', False),
                        ]
                    },
                    {
                        'text': 'Что делает ключевое слово lambda?',
                        'type': 'single',
                        'answers': [
                            ('Создаёт анонимную функцию', True),
                            ('Объявляет переменную', False),
                            ('Импортирует модуль', False),
                            ('Создаёт класс', False),
                        ]
                    },
                    {
                        'text': 'Какой метод используется для добавления элемента в конец списка?',
                        'type': 'single',
                        'answers': [
                            ('append()', True),
                            ('add()', False),
                            ('insert()', False),
                            ('push()', False),
                        ]
                    },
                    {
                        'text': 'Что такое декоратор в Python? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('Функция, изменяющая поведение другой функции', True),
                            ('Тип данных', False),
                            ('Обёртка вокруг функции', True),
                            ('Ключевое слово для объявления классов', False),
                        ]
                    },
                ]
            },
            {
                'title': 'Алгоритмы и структуры данных',
                'description': 'Сортировки, графы, деревья поиска.',
                'time_limit': 40,
                'questions': [
                    {
                        'text': 'Какой алгоритм использует жадную стратегию?',
                        'type': 'single',
                        'answers': [
                            ('Алгоритм Дейкстры', True),
                            ('Сортировка пузырьком', False),
                            ('Бинарный поиск', False),
                            ('Быстрая сортировка', False),
                        ]
                    },
                    {
                        'text': 'Какие структуры данных являются нелинейными? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('Дерево', True),
                            ('Граф', True),
                            ('Стек', False),
                            ('Очередь', False),
                        ]
                    },
                    {
                        'text': 'Какова сложность поиска в сбалансированном бинарном дереве поиска?',
                        'type': 'single',
                        'answers': [
                            ('O(log n)', True),
                            ('O(n)', False),
                            ('O(1)', False),
                            ('O(n²)', False),
                        ]
                    },
                    {
                        'text': 'Что такое обход дерева в ширину (BFS)?',
                        'type': 'single',
                        'answers': [
                            ('Обход уровня за уровнем', True),
                            ('Глубокий обход слева направо', False),
                            ('Обход справа налево', False),
                            ('Обход только листьев', False),
                        ]
                    },
                    {
                        'text': 'Какие из утверждений о графах верны? (Несколько вариантов)',
                        'type': 'multiple',
                        'answers': [
                            ('Граф может быть ориентированным', True),
                            ('Граф может содержать циклы', True),
                            ('В полном графе все вершины попарно соединены', True),
                            ('Граф не может иметь более 100 вершин', False),
                        ]
                    },
                ]
            },
        ],
    }

    for subject, tests_list in tests_data.items():
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
                test.groups.set(groups)
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
            else:
                print(f"⏭️ Тест уже существует: {test.title}")

    print("\n🎉 Тесты для teacher2 созданы!")


if __name__ == '__main__':
    seed()
