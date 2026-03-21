from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from .models import Profile, UserRole
from .mixins import TeacherRequiredMixin, StudentRequiredMixin

User = get_user_model()


def index_view(request):
    """Главная страница - перенаправление по ролям"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'users/login.html')


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Перенаправление на дашборд по роли"""
    if request.user.is_admin:
        return redirect('admin:index')
    elif request.user.is_teacher:
        return redirect('teacher_dashboard')
    elif request.user.is_student:
        return redirect('student_dashboard')
    return redirect('profile')


# ==================== Admin Views ====================
# Администрирование через стандартную Django admin: /admin/


# ==================== Teacher Views ====================

@login_required
def teacher_dashboard(request):
    """Панель преподавателя"""
    from groups.models import Subject, Group
    from tests.models import Test
    from results.models import Result
    
    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    user = request.user
    
    # Предметы преподавателя
    subjects = user.subjects.all()
    
    # Группы, которые ведет преподаватель
    groups = Group.objects.filter(subjects__teachers=user).distinct()
    
    # Тесты преподавателя
    tests = Test.objects.filter(created_by=user).select_related('subject')
    
    # Последние результаты по тестам преподавателя
    recent_results = Result.objects.filter(
        test__in=tests
    ).select_related('student', 'test').order_by('-completed_at')[:10]
    
    context = {
        'subjects': subjects,
        'groups': groups,
        'tests': tests,
        'recent_results': recent_results,
    }
    return render(request, 'users/teacher/dashboard.html', context)


@login_required
def teacher_groups(request):
    """Группы преподавателя"""
    from groups.models import Group
    
    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    groups = Group.objects.filter(
        subjects__teachers=request.user
    ).distinct().annotate(
        students_count=Count('students', distinct=True)
    )
    
    context = {'groups': groups}
    return render(request, 'users/teacher/groups.html', context)


@login_required
def teacher_subjects(request):
    """Предметы преподавателя"""
    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    subjects = request.user.subjects.prefetch_related('groups')
    context = {'subjects': subjects}
    return render(request, 'users/teacher/subjects.html', context)


@login_required
def teacher_tests(request):
    """Тесты преподавателя - список предметов"""
    from groups.models import Subject

    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    # Поиск по предмету
    search = request.GET.get('search', '')
    
    # Получаем предметы преподавателя
    subjects = Subject.objects.filter(
        teachers=request.user
    ).distinct().annotate(
        tests_count=Count('tests', filter=Q(tests__created_by=request.user))
    ).order_by('name')
    
    # Поиск по названию предмета
    if search:
        subjects = subjects.filter(name__icontains=search)

    context = {
        'subjects': subjects,
        'search': search,
    }
    return render(request, 'users/teacher/tests.html', context)


@login_required
def teacher_subject_tests(request, subject_id):
    """Тесты конкретного предмета"""
    from tests.models import Test
    from groups.models import Subject

    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    subject = get_object_or_404(Subject, id=subject_id, teachers=request.user)
    
    # Поиск по названию теста
    search = request.GET.get('search', '')
    
    # Фильтр по статусу
    status_filter = request.GET.get('status', '')
    
    # Получаем тесты предмета
    tests = Test.objects.filter(
        subject=subject,
        created_by=request.user
    ).select_related('subject').prefetch_related('groups')
    
    # Поиск по названию теста
    if search:
        tests = tests.filter(title__icontains=search)
    
    # Фильтр по статусу
    if status_filter == 'published':
        tests = tests.filter(is_published=True)
    elif status_filter == 'draft':
        tests = tests.filter(is_published=False)

    context = {
        'subject': subject,
        'tests': tests,
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'users/teacher/subject_tests.html', context)


@login_required
def teacher_results(request):
    """Результаты тестов преподавателя"""
    from tests.models import Test
    from results.models import Result
    
    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    test_id = request.GET.get('test')
    group_id = request.GET.get('group')
    
    tests = Test.objects.filter(created_by=request.user)
    
    if test_id:
        tests = tests.filter(id=test_id)
    
    results = Result.objects.filter(
        test__in=tests
    ).select_related('student', 'test', 'student__profile')
    
    if group_id:
        results = results.filter(student__profile__group_id=group_id)
    
    context = {
        'results': results,
        'tests': tests,
    }
    return render(request, 'users/teacher/results.html', context)


# ==================== Student Views ====================

@login_required
def student_dashboard(request):
    """Панель студента"""
    from tests.models import Test
    from results.models import Result
    from groups.models import Subject
    
    if not request.user.is_student:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    user = request.user
    profile = getattr(user, 'profile', None)
    
    if not profile or not profile.group:
        messages.warning(request, 'Вы не прикреплены к группе. Обратитесь к администратору.')
        return render(request, 'users/student/dashboard.html', {
            'subjects': [],
            'available_tests': [],
            'recent_results': []
        })
    
    # Предметы группы студента
    subjects = Subject.objects.filter(groups=profile.group)

    # Получаем ID пройденных тестов
    completed_tests = Result.objects.filter(
        student=user,
        is_reset=False,
        completed_at__isnull=False
    ).values_list('test_id', flat=True)

    # Доступные тесты (исключая пройденные)
    available_tests = Test.objects.filter(
        groups=profile.group,
        is_published=True
    ).exclude(id__in=completed_tests).select_related('subject')

    # Результаты студента
    student_results = Result.objects.filter(
        student=user,
        is_reset=False
    ).select_related('test').order_by('-completed_at')[:10]

    context = {
        'profile': profile,
        'subjects': subjects,
        'available_tests': available_tests,
        'recent_results': student_results,
    }
    return render(request, 'users/student/dashboard.html', context)


@login_required
def student_subjects(request):
    """Предметы студента - список карточек предметов"""
    from groups.models import Subject

    if not request.user.is_student:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    user = request.user
    profile = getattr(user, 'profile', None)

    if not profile or not profile.group:
        messages.warning(request, 'Вы не прикреплены к группе.')
        return redirect('student_dashboard')

    # Поиск по предмету
    search = request.GET.get('search', '')

    # Получаем предметы группы студента
    subjects = Subject.objects.filter(
        groups=profile.group
    ).distinct().annotate(
        tests_count=Count('tests', filter=Q(
            tests__groups=profile.group,
            tests__is_published=True
        ))
    ).order_by('name')

    # Поиск по названию предмета
    if search:
        subjects = subjects.filter(name__icontains=search)

    context = {
        'subjects': subjects,
        'search': search,
    }
    return render(request, 'users/student/subjects.html', context)


@login_required
def student_subject_tests(request, subject_id):
    """Тесты конкретного предмета для студента"""
    from tests.models import Test
    from groups.models import Subject
    from results.models import Result

    if not request.user.is_student:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    subject = get_object_or_404(Subject, id=subject_id, groups=request.user.profile.group if request.user.profile else None)

    user = request.user
    profile = getattr(user, 'profile', None)

    # Поиск по названию теста
    search = request.GET.get('search', '')

    # Получаем все пройденные тесты студентом
    completed_results = Result.objects.filter(
        student=user,
        is_reset=False,
        completed_at__isnull=False
    ).select_related('test')

    # Создаём словарь: test_id -> result_id
    completed_tests_dict = {r.test.id: r.id for r in completed_results}

    # Получаем тесты предмета
    tests = Test.objects.filter(
        subject=subject,
        groups=profile.group if profile else None,
        is_published=True
    ).select_related('subject').prefetch_related('groups')

    # Поиск по названию теста
    if search:
        tests = tests.filter(title__icontains=search)

    context = {
        'subject': subject,
        'tests': tests,
        'completed_tests_dict': completed_tests_dict,
        'search': search,
    }
    return render(request, 'users/student/subject_tests.html', context)


@login_required
def student_results(request):
    """Результаты студента"""
    from results.models import Result
    
    if not request.user.is_student:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    results = Result.objects.filter(
        student=request.user,
        is_reset=False
    ).select_related('test__subject').order_by('-completed_at')
    
    context = {'results': results}
    return render(request, 'users/student/results.html', context)


# ==================== Profile Views ====================

@login_required
def profile_view(request):
    """Просмотр и редактирование профиля"""
    profile = getattr(request.user, 'profile', None)
    
    if request.method == 'POST':
        # Обновление данных пользователя
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.phone = request.POST.get('phone', '')
        
        if request.POST.get('birth_date'):
            request.user.birth_date = request.POST.get('birth_date')
        
        request.user.save()
        
        # Обновление профиля
        if not profile:
            profile = Profile.objects.create(user=request.user)
        
        profile.bio = request.POST.get('bio', '')
        
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES.get('avatar')
        
        profile.save()
        
        messages.success(request, 'Профиль обновлен')
        return redirect('profile')
    
    context = {'profile': profile}
    return render(request, 'users/profile.html', context)
