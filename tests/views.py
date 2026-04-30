from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
import json
import random

from tests.models import Test, Question, Answer
from results.models import ArchivedResult, ArchivedStudentAnswer, Result, StudentAnswer
from users.mixins import StaffOrTeacherRequiredMixin


def build_questions_with_answers(result):
    """Собирает вопросы теста вместе с ответами студента."""
    all_questions = result.test.questions.prefetch_related('answers').all().order_by('id')
    student_answers_dict = {sa.question_id: sa for sa in result.student_answers.all()}

    questions_with_answers = []
    for question in all_questions:
        questions_with_answers.append({
            'question': question,
            'student_answer': student_answers_dict.get(question.id),
        })

    return questions_with_answers


def archive_result_snapshot(result, archived_by):
    """Сохраняет снимок результата и ответов перед сбросом."""
    archived_result = ArchivedResult.objects.create(
        test=result.test,
        student=result.student,
        archived_by=archived_by,
        original_result_id=result.id,
        grade=result.grade,
        started_at=result.started_at,
        completed_at=result.completed_at,
        correct_answers_count=result.correct_answers_count,
        total_questions=result.total_questions,
        device_info=result.device_info,
        tab_switches_count=result.tab_switches_count,
    )

    questions_with_answers = build_questions_with_answers(result)
    archived_answers = []
    for index, item in enumerate(questions_with_answers, start=1):
        student_answer = item['student_answer']
        question = item['question']
        archived_answers.append(
            ArchivedStudentAnswer(
                archived_result=archived_result,
                question_text=question.text,
                question_order=index,
                selected_answers=[answer.text for answer in student_answer.answers.all()] if student_answer else [],
                correct_answers=[answer.text for answer in question.answers.all() if answer.is_correct],
                is_correct=student_answer.is_correct if student_answer else False,
            )
        )

    ArchivedStudentAnswer.objects.bulk_create(archived_answers)
    return archived_result


# ==================== Teacher Test Management ====================

@login_required
def teacher_test_create(request):
    """Создание теста"""
    from groups.models import Subject, Group
    
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        title = request.POST.get('title')
        description = request.POST.get('description')
        time_limit = int(request.POST.get('time_limit', 60))
        is_published = request.POST.get('is_published') == 'on'
        show_correct_answers = request.POST.get('show_correct_answers') == 'on'
        shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        group_ids = request.POST.getlist('groups')

        subject = get_object_or_404(Subject, id=subject_id)

        test = Test.objects.create(
            subject=subject,
            title=title,
            description=description,
            time_limit=time_limit,
            is_published=is_published,
            show_correct_answers=show_correct_answers,
            shuffle_questions=shuffle_questions,
            created_by=request.user
        )
        test.groups.set(group_ids)
        
        messages.success(request, f'Тест "{title}" создан')
        return redirect('teacher_test_edit', test_id=test.id)
    
    subjects = Subject.objects.filter(teachers=request.user) if request.user.is_teacher else Subject.objects.all()
    groups = Group.objects.all()
    
    context = {
        'subjects': subjects,
        'groups': groups,
    }
    return render(request, 'tests/teacher/test_form.html', context)


@login_required
def teacher_test_edit(request, test_id):
    """Редактирование теста"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    back_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('teacher_tests')
    
    if request.user.is_teacher and test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому тесту')
        return redirect('teacher_tests')
    
    if request.method == 'POST':
        back_url = request.POST.get('next') or back_url
        test.title = request.POST.get('title')
        test.description = request.POST.get('description')
        test.time_limit = int(request.POST.get('time_limit', 60))
        test.is_published = request.POST.get('is_published') == 'on'
        test.show_correct_answers = request.POST.get('show_correct_answers') == 'on'
        test.shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        test.groups.set(request.POST.getlist('groups'))
        test.save()
        
        messages.success(request, 'Тест обновлен')
        return redirect(f"{reverse('teacher_test_edit', args=[test.id])}?next={back_url}")
    
    context = {
        'test': test,
        'back_url': back_url,
    }
    return render(request, 'tests/teacher/test_edit.html', context)


@login_required
def teacher_test_duplicate(request, test_id):
    """Дублирование теста"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    
    if request.user.is_teacher and test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому тесту')
        return redirect('teacher_tests')
    
    new_test = test.duplicate()
    messages.success(request, f'Тест "{new_test.title}" создан')
    return redirect('teacher_test_edit', test_id=new_test.id)


@login_required
def teacher_test_delete(request, test_id):
    """Удаление теста"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    test = get_object_or_404(Test, id=test_id)
    redirect_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('teacher_subject_tests', args=[test.subject_id])
    
    if request.user.is_teacher and test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому тесту')
        return redirect(redirect_url)
    
    test.delete()
    messages.success(request, 'Тест удален')
    return redirect(redirect_url)


@login_required
def teacher_question_create(request, test_id):
    """Создание вопроса"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    test = get_object_or_404(Test, id=test_id)

    if request.user.is_teacher and test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому тесту')
        return redirect('teacher_tests')

    if request.method == 'POST':
        text = request.POST.get('text')
        question_type = request.POST.get('question_type')
        code_snippet = request.POST.get('code_snippet', '')
        order = int(request.POST.get('order', 0))

        question = Question.objects.create(
            test=test,
            text=text,
            question_type=question_type,
            code_snippet=code_snippet,
            order=order
        )

        # Сохраняем изображение
        if request.FILES.get('image'):
            question.image = request.FILES.get('image')
            question.save()

        # Сохраняем ответы
        answer_texts = request.POST.getlist('answer_text[]')
        answer_correct = request.POST.getlist('answer_correct[]')

        for i, answer_text in enumerate(answer_texts):
            if answer_text.strip():
                Answer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=i in [int(x) for x in answer_correct],
                    order=i
                )

        messages.success(request, 'Вопрос добавлен')
        return redirect('teacher_test_edit', test_id=test_id)

    context = {'test': test}
    return render(request, 'tests/teacher/question_form.html', context)


@login_required
def teacher_question_edit(request, question_id):
    """Редактирование вопроса"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    question = get_object_or_404(Question, id=question_id)
    test = question.test

    if request.user.is_teacher and test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому вопросу')
        return redirect('teacher_tests')

    if request.method == 'POST':
        question.text = request.POST.get('text')
        question.question_type = request.POST.get('question_type')
        question.code_snippet = request.POST.get('code_snippet', '')
        question.order = int(request.POST.get('order', 0))

        # Сохраняем изображение
        if request.FILES.get('image'):
            question.image = request.FILES.get('image')

        question.save()

        # Получаем текущие ответы
        answer_texts = request.POST.getlist('answer_text[]')
        answer_correct_indices = request.POST.getlist('answer_correct[]')
        answer_ids = request.POST.getlist('answer_id[]')

        # Преобразуем индексы правильных ответов в integers
        correct_indices = [int(x) for x in answer_correct_indices]

        # Удаляем ответы, которые были удалены из формы
        current_answer_ids = [int(x) for x in answer_ids if x]
        for answer in question.answers.all():
            if answer.id not in current_answer_ids:
                answer.delete()

        # Обновляем или создаём ответы
        for i, answer_text in enumerate(answer_texts):
            if answer_text.strip():
                answer_id = answer_ids[i] if i < len(answer_ids) else None
                is_correct = i in correct_indices
                
                if answer_id and answer_id.isdigit():
                    # Обновляем существующий
                    answer = get_object_or_404(Answer, id=int(answer_id), question=question)
                    answer.text = answer_text
                    answer.is_correct = is_correct
                    answer.order = i
                    answer.save()
                else:
                    # Создаём новый
                    Answer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=is_correct,
                        order=i
                    )

        messages.success(request, 'Вопрос обновлен')
        return redirect('teacher_test_edit', test_id=test.id)

    context = {'test': test, 'question': question}
    return render(request, 'tests/teacher/question_form.html', context)


@login_required
def teacher_question_delete(request, question_id):
    """Удаление вопроса"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    question = get_object_or_404(Question, id=question_id)
    test_id = question.test.id
    
    if request.user.is_teacher and question.test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этому вопросу')
        return redirect('teacher_tests')
    
    question.delete()
    messages.success(request, 'Вопрос удален')
    return redirect('teacher_test_edit', test_id=test_id)


# ==================== Student Test Taking ====================

@login_required
def test_take(request, test_id):
    """Прохождение теста студентом"""
    if not request.user.is_student:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    test = get_object_or_404(Test, id=test_id)
    profile = getattr(request.user, 'profile', None)

    # Проверка доступа
    if not test.is_published:
        messages.error(request, 'Тест еще не опубликован')
        return redirect('student_dashboard')

    if not profile or not profile.group or not test.groups.filter(id=profile.group.id).exists():
        messages.error(request, 'У вас нет доступа к этому тесту')
        return redirect('student_dashboard')

    # Проверка, есть ли завершённая попытка (нельзя пройти повторно)
    completed_result = Result.objects.filter(
        student=request.user,
        test=test,
        completed_at__isnull=False
    ).first()

    if completed_result:
        messages.info(request, 'Вы уже прошли этот тест. Повторное прохождение недоступно.')
        return redirect('student_subjects')

    # Проверка, есть ли активная попытка
    existing_result = Result.objects.filter(
        student=request.user,
        test=test,
        completed_at__isnull=True
    ).first()

    if existing_result:
        # Продолжение существующей попытки
        result = existing_result
    else:
        # Новая попытка
        result = Result.objects.create(
            student=request.user,
            test=test,
            total_questions=test.questions.count()
        )

    current_user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
    if current_user_agent and result.device_info != current_user_agent:
        result.device_info = current_user_agent
        result.save(update_fields=['device_info'])

    questions = list(test.questions.prefetch_related('answers').all())

    # Перемешиваем вопросы и ответы, если включено
    if test.shuffle_questions:
        random.shuffle(questions)
        for question in questions:
            answers_list = list(question.answers.all())
            random.shuffle(answers_list)
            question._prefetched_objects_cache = {'answers': answers_list}

    # Передаём started_at как unix-таймстамп (мс) для JS-вычисления
    started_at_timestamp = int(result.started_at.timestamp() * 1000)

    # Определяем, новая ли это попытка (создана только что или в текущую сессию)
    # Если elapsed < 10 секунд — считаем новой, нужно очистить старые ответы
    elapsed = (timezone.now() - result.started_at).total_seconds()
    is_new_attempt = elapsed < 10

    context = {
        'test': test,
        'result': result,
        'questions': questions,
        'started_at_ms': started_at_timestamp,
        'is_new_attempt': is_new_attempt,
    }
    return render(request, 'tests/student/test_take.html', context)


@require_POST
@login_required
def test_submit(request, result_id):
    """Отправка ответов студентом"""
    if not request.user.is_student:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    result = get_object_or_404(Result, id=result_id, student=request.user)
    
    if result.completed_at:
        return JsonResponse({'error': 'Тест уже завершен'}, status=400)
    
    # Получаем ответы из POST
    answers_data = json.loads(request.POST.get('answers', '{}'))
    try:
        tab_switches_count = max(0, int(request.POST.get('tab_switches_count', 0)))
    except (TypeError, ValueError):
        tab_switches_count = 0

    correct_count = 0

    for question_id, selected_answer_ids in answers_data.items():
        question = get_object_or_404(Question, id=question_id)

        student_answer = StudentAnswer.objects.create(
            result=result,
            question=question
        )

        # Получаем правильные ответы
        correct_answer_ids = list(question.answers.filter(is_correct=True).values_list('id', flat=True))

        # Проверяем правильность
        selected_ids = [int(x) for x in selected_answer_ids]

        if question.question_type == 'single':
            is_correct = selected_ids == correct_answer_ids
        else:
            is_correct = set(selected_ids) == set(correct_answer_ids)

        student_answer.is_correct = is_correct
        student_answer.save()
        
        # Сохраняем выбранные ответы (после сохранения student_answer)
        if selected_ids:
            student_answer.answers.set(selected_ids)

        if is_correct:
            correct_count += 1
    
    # Обновляем результат
    result.correct_answers_count = correct_count
    result.completed_at = timezone.now()
    result.tab_switches_count = tab_switches_count
    
    # Сохраняем информацию об устройстве
    result.device_info = request.META.get('HTTP_USER_AGENT', '')[:200]
    result.save()
    
    # Вычисляем оценку (ограничиваем 100%)
    actual_total = max(result.total_questions, correct_count)
    percentage = (correct_count / actual_total * 100) if actual_total > 0 else 0
    percentage = min(percentage, 100)
    
    if percentage >= 85:
        result.grade = 5
    elif percentage >= 70:
        result.grade = 4
    elif percentage >= 50:
        result.grade = 3
    else:
        result.grade = 2
    
    result.save()
    
    return JsonResponse({
        'success': True,
        'grade': result.grade,
        'correct_count': correct_count,
        'total_questions': result.total_questions,
        'show_answers': result.test.show_correct_answers
    })


@login_required
def test_result_detail(request, result_id):
    """Просмотр результатов теста"""
    # Получаем результат с prefetch для оптимизации
    result = get_object_or_404(
        Result.objects.prefetch_related(
            'student_answers__question__answers',
            'student_answers__answers'
        ),
        id=result_id
    )

    # Проверка прав
    if request.user.is_student and result.student != request.user:
        messages.error(request, 'У вас нет доступа к этому результату')
        return redirect('dashboard')

    if request.user.is_teacher:
        if not Test.objects.filter(id=result.test.id, created_by=request.user).exists():
            messages.error(request, 'У вас нет доступа к этому результату')
            return redirect('dashboard')
    # Получаем все вопросы теста
    all_questions = result.test.questions.prefetch_related('answers').all().order_by('id')

    # Создаём словарь ответов студента по question_id
    student_answers_dict = {sa.question_id: sa for sa in result.student_answers.all()}

    # Создаём список всех вопросов с ответами студента (или None)
    questions_with_answers = []
    for question in all_questions:
        student_answer = student_answers_dict.get(question.id)
        questions_with_answers.append({
            'question': question,
            'student_answer': student_answer,
        })

    reset_return_url = ''
    if request.user.is_teacher or request.user.is_admin:
        student_group_id = getattr(getattr(result.student, 'profile', None), 'group_id', None)
        if student_group_id:
            reset_return_url = reverse(
                'teacher_results_students',
                args=[result.test.subject_id, student_group_id, result.test_id]
            )
        else:
            reset_return_url = reverse('teacher_results')

    context = {
        'result': result,
        'questions_with_answers': questions_with_answers,
        'archived_results_count': (
            ArchivedResult.objects.filter(student_id=result.student_id, test_id=result.test_id).count()
            if request.user.is_teacher or request.user.is_admin else 0
        ),
        'archive_url': (
            f"{reverse('teacher_archived_results', args=[result.student_id, result.test_id])}?next={request.path}"
            if request.user.is_teacher else ''
        ),
        'reset_return_url': reset_return_url,
    }
    return render(request, 'tests/result_detail.html', context)


@login_required
def teacher_archived_results(request, student_id, test_id):
    """Список архивных результатов студента по конкретному тесту."""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    archived_results = ArchivedResult.objects.filter(
        student_id=student_id,
        test_id=test_id,
    ).select_related('student', 'test', 'test__subject', 'archived_by')

    archived_result = archived_results.first()
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
    if archived_result is None:
        messages.info(request, 'Архивных результатов пока нет')
        return redirect(next_url or 'teacher_results')

    if request.user.is_teacher and archived_result.test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    context = {
        'student': archived_result.student,
        'test': archived_result.test,
        'subject': archived_result.test.subject,
        'group': getattr(archived_result.student, 'profile', None).group if getattr(archived_result.student, 'profile', None) else None,
        'archived_results': archived_results,
    }
    return render(request, 'tests/teacher/archived_results.html', context)


@login_required
def teacher_archived_result_detail(request, archive_id):
    """Детальный просмотр архивной попытки."""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    archived_result = get_object_or_404(
        ArchivedResult.objects.prefetch_related('archived_answers').select_related('student', 'test', 'test__subject', 'archived_by'),
        id=archive_id,
    )

    if request.user.is_teacher and archived_result.test.created_by != request.user:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    context = {
        'archived_result': archived_result,
        'archived_answers': archived_result.archived_answers.all(),
    }
    return render(request, 'tests/teacher/archived_result_detail.html', context)


@login_required
def test_result_answers_fragment(request, result_id):
    """Возвращает HTML блока ответов для динамического обновления."""
    result = get_object_or_404(
        Result.objects.prefetch_related(
            'student_answers__question__answers',
            'student_answers__answers'
        ),
        id=result_id
    )

    if request.user.is_student and result.student != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.user.is_teacher:
        if not Test.objects.filter(id=result.test.id, created_by=request.user).exists():
            return JsonResponse({'error': 'Forbidden'}, status=403)
    elif not request.user.is_admin and not request.user.is_student:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    questions_with_answers = build_questions_with_answers(result)
    html = render_to_string(
        'tests/_result_answers.html',
        {
            'result': result,
            'questions_with_answers': questions_with_answers,
            'user': request.user,
        },
        request=request,
    )
    return JsonResponse({'html': html})


@login_required
def teacher_results_live_status(request):
    """Возвращает актуальный статус результатов для живого обновления."""
    if not request.user.is_teacher and not request.user.is_admin and not request.user.is_student:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    result_ids = []
    for raw_result_id in request.GET.getlist('result_ids'):
        try:
            result_ids.append(int(raw_result_id))
        except (TypeError, ValueError):
            continue

    if not result_ids:
        return JsonResponse({'results': []})

    results = Result.objects.filter(id__in=result_ids).select_related('test', 'student')

    if request.user.is_teacher:
        results = results.filter(test__created_by=request.user)
    elif request.user.is_student:
        results = results.filter(student=request.user)

    payload = []
    for result in results:
        reset_url = ''
        if (request.user.is_teacher or request.user.is_admin) and result.completed_at:
            student_group_id = getattr(getattr(result.student, 'profile', None), 'group_id', None)
            if student_group_id:
                reset_next_url = reverse(
                    'teacher_results_students',
                    args=[result.test.subject_id, student_group_id, result.test_id]
                )
            else:
                reset_next_url = reverse('teacher_results')
            reset_url = f"{reverse('test_result_reset', args=[result.id])}?next={reset_next_url}"

        payload.append({
            'id': result.id,
            'completed': bool(result.completed_at),
            'completed_at_display': timezone.localtime(result.completed_at).strftime('%d.%m.%Y %H:%M') if result.completed_at else '',
            'grade': result.grade,
            'correct_answers_count': result.correct_answers_count,
            'total_questions': result.total_questions,
            'remaining_seconds': result.remaining_seconds,
            'duration_seconds': result.duration_seconds,
            'device_type_display': result.device_type_display,
            'reset_url': reset_url,
        })

    return JsonResponse({'results': payload})


@login_required
def test_result_update_grade(request, result_id):
    """Обновление оценки преподавателем"""
    if not request.user.is_teacher and not request.user.is_admin:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    result = get_object_or_404(Result, id=result_id)
    
    if request.user.is_teacher:
        if not Test.objects.filter(id=result.test.id, created_by=request.user).exists():
            return JsonResponse({'error': 'Forbidden'}, status=403)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        if grade:
            result.grade = int(grade)
            result.save()
            return JsonResponse({'success': True, 'grade': result.grade})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def test_result_reset(request, result_id):
    """Сброс результата для перепрохождения"""
    if not request.user.is_teacher and not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    result = get_object_or_404(Result, id=result_id)

    if request.user.is_teacher:
        if not Test.objects.filter(id=result.test.id, created_by=request.user).exists():
            messages.error(request, 'У вас нет доступа к этому результату')
            return redirect('dashboard')

    # Сохраняем данные для сообщения
    next_url = request.GET.get('next')
    redirect_url = next_url

    if not redirect_url:
        student_group_id = getattr(getattr(result.student, 'profile', None), 'group_id', None)
        if student_group_id:
            redirect_url = reverse(
                'teacher_results_students',
                args=[result.test.subject_id, student_group_id, result.test_id]
            )
        else:
            redirect_url = reverse('teacher_results')

    student_name = result.student.last_name
    test_title = result.test.title

    if not result.completed_at:
        messages.error(request, 'Нельзя сбросить результат, пока студент ещё проходит тест.')
        return redirect(redirect_url)

    # Полностью удаляем результат (StudentAnswer удалятся по CASCADE)
    archive_result_snapshot(result, request.user)
    result.delete()

    messages.success(request, f'Результат студента {student_name} за тест "{test_title}" сброшен. Студент может пройти тест заново.')

    # Перенаправляем на общую страницу результатов (результат удалён, детальная страница не существует)
    return redirect(redirect_url)


@login_required
def test_toggle_answers(request, test_id):
    """Переключение видимости правильных ответов"""
    if not request.user.is_teacher and not request.user.is_admin:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    test = get_object_or_404(Test, id=test_id)
    
    if request.user.is_teacher and test.created_by != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    
    test.show_correct_answers = not test.show_correct_answers
    test.save()
    
    return JsonResponse({'success': True, 'show_correct_answers': test.show_correct_answers})
