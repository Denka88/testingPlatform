from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Group, Subject


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'admission_year', 'created_at')
    list_filter = ('admission_year',)
    search_fields = ('name',)
    ordering = ('admission_year', 'name')
    
    fieldsets = (
        ('Информация о группе', {
            'fields': ('name', 'admission_year')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Проверка на дублирование названия при изменении
        if change and 'name' in form.changed_data:
            # Предупреждение о необходимости смены всех названий
            pass
        super().save_model(request, obj, form, change)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_teachers', 'get_groups_count', 'created_at')
    list_filter = ('teachers', 'groups')
    search_fields = ('name', 'description')
    filter_horizontal = ('teachers', 'groups')
    ordering = ('name',)
    
    fieldsets = (
        ('Информация о предмете', {
            'fields': ('name', 'description')
        }),
        ('Преподаватели', {
            'fields': ('teachers',)
        }),
        ('Группы', {
            'fields': ('groups',)
        }),
    )
    
    def get_teachers(self, obj):
        return ", ".join([t.last_name for t in obj.teachers.all()])
    get_teachers.short_description = 'Преподаватели'
    
    def get_groups_count(self, obj):
        return obj.groups.count()
    get_groups_count.short_description = 'Кол-во групп'
