from django.urls import path
from . import views

urlpatterns = [
    # Index
    path('', views.index_view, name='index'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/dashboard/recent-results/', views.teacher_dashboard_recent_results, name='teacher_dashboard_recent_results'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/tests/', views.teacher_tests, name='teacher_tests'),
    path('teacher/tests/<int:subject_id>/', views.teacher_subject_tests, name='teacher_subject_tests'),
    # Результаты - новая структура
    path('teacher/results/', views.teacher_results, name='teacher_results'),
    path('teacher/results/subjects/', views.teacher_results_subjects, name='teacher_results_subjects'),
    path('teacher/results/subjects/<int:subject_id>/groups/', views.teacher_results_groups, name='teacher_results_groups'),
    path('teacher/results/subjects/<int:subject_id>/groups/<int:group_id>/tests/', views.teacher_results_tests, name='teacher_results_tests'),
    path('teacher/results/subjects/<int:subject_id>/groups/<int:group_id>/tests/<int:test_id>/students/', views.teacher_results_students, name='teacher_results_students'),
    path('teacher/results/subjects/<int:subject_id>/groups/<int:group_id>/tests/<int:test_id>/students/live-status/', views.teacher_results_students_live_status, name='teacher_results_students_live_status'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/dashboard/live-tests/', views.student_dashboard_live_tests, name='student_dashboard_live_tests'),
    path('student/subjects/', views.student_subjects, name='student_subjects'),
    path('student/subjects/<int:subject_id>/', views.student_subject_tests, name='student_subject_tests'),
    path('student/results/', views.student_results, name='student_results'),
]
