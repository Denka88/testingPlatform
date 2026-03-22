from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Основная страница чата (контакты + переписка)
    path('chat/', views.contacts_view, name='contacts'),
    
    # AJAX endpoints
    path('chat/api/add-contact/', views.add_contact_view, name='add_contact'),
    path('chat/api/remove-contact/', views.remove_contact_view, name='remove_contact'),
    path('chat/api/search-users/', views.search_users_view, name='search_users'),
    
    # Административные URL
    path('chat/admin/', views.admin_chat_list_view, name='admin_chat_list'),
    path('chat/admin/<int:user1_id>/<int:user2_id>/', views.admin_chat_view, name='admin_chat'),
]
