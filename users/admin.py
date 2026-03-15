from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, UserRole


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'last_name', 'first_name', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'email', 'phone', 'birth_date')}),
        ('Роль', {'fields': ('role',)}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'role'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'real_group', 'created_at', 'updated_at')
    list_filter = ('group',)
    search_fields = ('user__username', 'user__last_name', 'user__first_name')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('Пользователь', {'fields': ('user',)}),
        ('Аватар', {'fields': ('avatar',)}),
        ('Группа', {'fields': ('group', 'real_group')}),
        ('О себе', {'fields': ('bio',)}),
        ('Даты', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
