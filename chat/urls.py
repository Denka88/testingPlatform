from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Основная страница чата
    path('chat/', views.contacts_view, name='contacts'),

    # AJAX endpoints
    path('chat/api/search/', views.search_users_ajax, name='search_users'),
]
