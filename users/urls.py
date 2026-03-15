from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Admin
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/groups/', views.admin_groups, name='admin_groups'),
    path('admin-panel/subjects/', views.admin_subjects, name='admin_subjects'),
    
    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/subjects/', views.teacher_subjects, name='teacher_subjects'),
    path('teacher/tests/', views.teacher_tests, name='teacher_tests'),
    path('teacher/results/', views.teacher_results, name='teacher_results'),
    
    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/subjects/', views.student_subjects, name='student_subjects'),
    path('student/results/', views.student_results, name='student_results'),
]
