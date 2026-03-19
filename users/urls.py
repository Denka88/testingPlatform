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
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/tests/', views.teacher_tests, name='teacher_tests'),
    path('teacher/tests/<int:subject_id>/', views.teacher_subject_tests, name='teacher_subject_tests'),
    path('teacher/results/', views.teacher_results, name='teacher_results'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/subjects/', views.student_subjects, name='student_subjects'),
    path('student/results/', views.student_results, name='student_results'),
]
