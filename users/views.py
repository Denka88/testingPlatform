from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from .models import Profile, UserRole
from .mixins import AdminRequiredMixin, TeacherRequiredMixin, StudentRequiredMixin

User = get_user_model()


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
        return redirect('admin_dashboard')
    elif request.user.is_teacher:
        return redirect('teacher_dashboard')
    elif request.user.is_student:
        return redirect('student_dashboard')
    return redirect('profile')


# ==================== Admin Views ====================

@login_required
def admin_dashboard(request):
    """Панель администратора"""
    from groups.models import Group, Subject
    from tests.models import Test
    from results.models import Result
    
    if not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    context = {
        'users_count': User.objects.count(),
        'students_count': User.objects.filter(role='student').count(),
        'teachers_count': User.objects.filter(role='teacher').count(),
        'groups_count': Group.objects.count(),
        'subjects_count': Subject.objects.count(),
        'tests_count': Test.objects.count(),
        'results_count': Result.objects.count(),
    }
    return render(request, 'users/admin/dashboard.html', context)


@login_required
def admin_users(request):
    """Управление пользователями"""
    from users.models import UserRole
    
    if not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    users = User.objects.select_related('profile').all()
    
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'roles': UserRole.choices,
    }
    return render(request, 'users/admin/users.html', context)


@login_required
def admin_groups(request):
    """Управление группами"""
    from groups.models import Group
    
    if not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    groups = Group.objects.annotate(
        students_count=Count('students', distinct=True),
        subjects_count=Count('subjects', distinct=True)
    ).order_by('admission_year', 'name')
    
    context = {'groups': groups}
    return render(request, 'users/admin/groups.html', context)


@login_required
def admin_subjects(request):
    """Управление предметами"""
    from groups.models import Subject
    
    if not request.user.is_admin:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    subjects = Subject.objects.prefetch_related('teachers', 'groups').all()
    context = {'subjects': subjects}
    return render(request, 'users/admin/subjects.html', context)


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
    """Тесты преподавателя"""
    from tests.models import Test
    
    if not request.user.is_teacher:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')
    
    tests = Test.objects.filter(
        created_by=request.user
    ).select_related('subject').prefetch_related('groups')
    
    context = {'tests': tests}
    return render(request, 'users/teacher/tests.html', context)


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
    
    # Доступные тесты
    available_tests = Test.objects.filter(
        groups=profile.group,
        is_published=True
    ).select_related('subject')
    
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
    """Предметы студента с тестами"""
    from tests.models import Test
    from groups.models import Subject

    if not request.user.is_student:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')

    user = request.user
    profile = getattr(user, 'profile', None)

    if not profile or not profile.group:
        messages.warning(request, 'Вы не прикреплены к группе.')
        return redirect('student_dashboard')

    # Предметы группы студента с.prefetch для тестов
    subjects = Subject.objects.filter(
        groups=profile.group
    ).prefetch_related(
        'tests__groups'
    )

    # Фильтруем тесты для каждого предмета
    subjects_list = []
    for subject in subjects:
        subject_tests = Test.objects.filter(
            subject=subject,
            groups=profile.group,
            is_published=True
        )
        subjects_list.append({
            'subject': subject,
            'tests': subject_tests
        })

    context = {'subjects': subjects_list}
    return render(request, 'users/student/subjects.html', context)


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
