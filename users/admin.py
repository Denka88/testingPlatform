from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html

from .models import Profile, User, UserRole

admin.site.unregister(Group)


class ProfileInlineForm(forms.ModelForm):
    """Форма для inline-профиля с проверкой роли."""

    class Meta:
        model = Profile
        fields = '__all__'

    def clean_group(self):
        """Группа обязательна только для студентов."""
        group = self.cleaned_data.get('group')
        submitted_role = self.data.get('role') if hasattr(self, 'data') else None
        effective_role = submitted_role if submitted_role in UserRole.values else None
        if effective_role is None and self.instance and self.instance.user:
            effective_role = self.instance.user.role
        if effective_role == UserRole.STUDENT:
            if not group:
                raise forms.ValidationError('Для студентов группа обязательна')
        return group


class ProfileInline(admin.StackedInline):
    """Профиль пользователя inline."""

    model = Profile
    can_delete = False
    verbose_name = 'Профиль'
    verbose_name_plural = 'Профиль'
    fk_name = 'user'
    form = ProfileInlineForm
    extra = 0

    def _get_effective_role(self, request, obj=None):
        submitted_role = request.POST.get('role') if request.method == 'POST' else None
        if submitted_role in UserRole.values:
            return submitted_role
        if obj:
            return obj.role
        return None

    def get_fieldsets(self, request, obj=None):
        """Скрываем поле группы для преподавателей и администраторов."""
        effective_role = self._get_effective_role(request, obj)
        if effective_role and effective_role != UserRole.STUDENT:
            return (
                ('Аватар', {'fields': ('avatar',)}),
                ('О себе', {'fields': ('bio',)}),
            )
        return (
            ('Аватар', {'fields': ('avatar',)}),
            ('Группа', {'fields': ('group', 'real_group')}),
            ('О себе', {'fields': ('bio',)}),
        )

    def get_fields(self, request, obj=None):
        """Адаптируем поля в зависимости от роли."""
        effective_role = self._get_effective_role(request, obj)
        if effective_role and effective_role != UserRole.STUDENT:
            return ('avatar', 'bio')
        return ('avatar', 'group', 'real_group', 'bio')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'last_name',
        'first_name',
        'patronymic',
        'email',
        'role',
        'has_profile',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('last_name', 'first_name', 'patronymic', 'email', 'phone', 'birth_date')}),
        ('Роль', {'fields': ('role',)}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'last_name', 'first_name', 'patronymic', 'role'),
        }),
    )

    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def save_formset(self, request, form, formset, change):
        if formset.model is Profile:
            instances = formset.save(commit=False)

            for deleted_object in formset.deleted_objects:
                deleted_object.delete()

            existing_profile = getattr(form.instance, 'profile', None)
            if existing_profile and instances:
                inline_profile = instances[0]
                existing_profile.avatar = inline_profile.avatar
                existing_profile.group = inline_profile.group
                existing_profile.real_group = inline_profile.real_group
                existing_profile.bio = inline_profile.bio
                existing_profile.save()
                formset.save_m2m()
                return

            for instance in instances:
                instance.save()
            formset.save_m2m()
            return

        super().save_formset(request, form, formset, change)

    def has_profile(self, obj):
        """Показывает статус наличия профиля."""
        if hasattr(obj, 'profile'):
            url = reverse('admin:users_profile_changelist')
            return format_html(
                '<a href="{}?user__id={}"><span style="color: green;">✓ Есть</span></a>',
                url,
                obj.id,
            )
        return format_html(
            '<a href="/admin/users/profile/add/?user_id={}" style="color: red;">✗ Нет профиля</a>',
            obj.id,
        )

    has_profile.short_description = 'Профиль'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user_link', 'get_user_role', 'group', 'real_group', 'created_at', 'updated_at')
    list_filter = ('group', 'user__role')
    search_fields = ('user__username', 'user__last_name', 'user__first_name')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            users_without_profile = User.objects.filter(profile__isnull=True)
            form.base_fields['user'].queryset = users_without_profile

            original_clean = form.clean

            def custom_clean():
                cleaned_data = original_clean()
                user = cleaned_data.get('user')
                group = cleaned_data.get('group')
                if user and user.role == UserRole.STUDENT and not group:
                    raise forms.ValidationError('Для студентов группа обязательна')
                return cleaned_data

            form.clean = custom_clean

        return form

    def get_fieldsets(self, request, obj=None):
        """Скрываем поле группы для преподавателей и администраторов."""
        if request.GET.get('user_id'):
            try:
                user = User.objects.get(id=request.GET.get('user_id'))
                if user.role != UserRole.STUDENT:
                    return (
                        ('Пользователь', {'fields': ('user',)}),
                        ('Аватар', {'fields': ('avatar',)}),
                        ('О себе', {'fields': ('bio',)}),
                        ('Даты', {'fields': ('created_at', 'updated_at')}),
                    )
            except User.DoesNotExist:
                pass

        if obj and obj.user.role != UserRole.STUDENT:
            return (
                ('Пользователь', {'fields': ('user',)}),
                ('Аватар', {'fields': ('avatar',)}),
                ('О себе', {'fields': ('bio',)}),
                ('Даты', {'fields': ('created_at', 'updated_at')}),
            )

        return (
            ('Пользователь', {'fields': ('user',)}),
            ('Аватар', {'fields': ('avatar',)}),
            ('Группа', {'fields': ('group', 'real_group')}),
            ('О себе', {'fields': ('bio',)}),
            ('Даты', {'fields': ('created_at', 'updated_at')}),
        )

    def get_fields(self, request, obj=None):
        """Адаптируем поля в зависимости от роли."""
        if request.GET.get('user_id'):
            try:
                user = User.objects.get(id=request.GET.get('user_id'))
                if user.role != UserRole.STUDENT:
                    return ('user', 'avatar', 'bio', 'created_at', 'updated_at')
            except User.DoesNotExist:
                pass

        if obj and obj.user.role != UserRole.STUDENT:
            return ('user', 'avatar', 'bio', 'created_at', 'updated_at')
        return ('user', 'avatar', 'group', 'real_group', 'bio', 'created_at', 'updated_at')

    def get_user_link(self, obj):
        """Ссылка на пользователя."""
        url = reverse('admin:users_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user)

    get_user_link.short_description = 'Пользователь'

    def get_user_role(self, obj):
        """Роль пользователя."""
        return obj.user.get_role_display()

    get_user_role.short_description = 'Роль'
