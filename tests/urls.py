from django.urls import path
from . import views

urlpatterns = [
    # Teacher test management
    path('teacher/test/create/', views.teacher_test_create, name='teacher_test_create'),
    path('teacher/test/<int:test_id>/edit/', views.teacher_test_edit, name='teacher_test_edit'),
    path('teacher/test/<int:test_id>/duplicate/', views.teacher_test_duplicate, name='teacher_test_duplicate'),
    path('teacher/test/<int:test_id>/delete/', views.teacher_test_delete, name='teacher_test_delete'),
    path('teacher/test/<int:test_id>/question/create/', views.teacher_question_create, name='teacher_question_create'),
    path('teacher/question/<int:question_id>/delete/', views.teacher_question_delete, name='teacher_question_delete'),
    
    # Student test taking
    path('test/<int:test_id>/take/', views.test_take, name='test_take'),
    path('test/submit/<int:result_id>/', views.test_submit, name='test_submit'),
    path('test/result/<int:result_id>/', views.test_result_detail, name='test_result_detail'),
    
    # Teacher result management
    path('teacher/result/<int:result_id>/grade/', views.test_result_update_grade, name='test_result_update_grade'),
    path('teacher/result/<int:result_id>/reset/', views.test_result_reset, name='test_result_reset'),
    path('teacher/test/<int:test_id>/toggle-answers/', views.test_toggle_answers, name='test_toggle_answers'),
]
