from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages


class RoleRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки роли пользователя"""
    required_role = None
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.required_role:
            return self.request.user.role == self.required_role
        return True
    
    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет доступа к этой странице')
        return redirect('dashboard')


class AdminRequiredMixin(RoleRequiredMixin):
    """Миксин для администраторов"""
    required_role = 'admin'


class TeacherRequiredMixin(RoleRequiredMixin):
    """Миксин для преподавателей"""
    required_role = 'teacher'


class StudentRequiredMixin(RoleRequiredMixin):
    """Миксин для студентов"""
    required_role = 'student'


class StaffOrTeacherRequiredMixin(UserPassesTestMixin):
    """Миксин для админов и преподавателей"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.is_admin or self.request.user.is_teacher


class IsOwnerOrAdminMixin(UserPassesTestMixin):
    """Миксин для проверки владения объектом или админ прав"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_admin:
            return True
        obj = self.get_object()
        if hasattr(obj, 'user'):
            return obj.user == self.request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == self.request.user
        return False
