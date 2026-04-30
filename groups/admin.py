from django.contrib import admin

from .models import Group, Subject


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "admission_year", "created_at")
    list_filter = ("admission_year",)
    search_fields = ("name",)
    ordering = ("admission_year", "name")
    fieldsets = (
        ("Информация о группе", {"fields": ("name", "admission_year")}),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "get_teachers", "get_groups_count", "created_at")
    list_filter = ("teachers", "groups")
    search_fields = ("name", "description")
    filter_horizontal = ("teachers", "groups")
    ordering = ("name",)
    fieldsets = (
        ("Информация о предмете", {"fields": ("name", "description", "image")}),
        ("Преподаватели", {"fields": ("teachers",)}),
        ("Группы", {"fields": ("groups",)}),
    )

    def get_teachers(self, obj):
        return ", ".join(teacher.last_name for teacher in obj.teachers.all())

    get_teachers.short_description = "Преподаватели"

    def get_groups_count(self, obj):
        return obj.groups.count()

    get_groups_count.short_description = "Кол-во групп"
