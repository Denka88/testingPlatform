from django.contrib import admin

from .models import ArchivedResult, ArchivedStudentAnswer, Result, StudentAnswer


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ("question", "is_correct")
    filter_horizontal = ("answers",)

    def has_add_permission(self, request, obj=None):
        return False


class ArchivedStudentAnswerInline(admin.TabularInline):
    model = ArchivedStudentAnswer
    extra = 0
    readonly_fields = (
        "question_text",
        "question_order",
        "selected_answers",
        "correct_answers",
        "is_correct",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "test",
        "grade",
        "correct_answers_count",
        "total_questions",
        "started_at",
        "completed_at",
        "device_info",
        "tab_switches_count",
    )
    list_filter = ("grade", "test", "student")
    search_fields = ("student__username", "student__last_name", "test__title")
    ordering = ("-completed_at", "-started_at")
    raw_id_fields = ("student", "test")
    fieldsets = (
        ("Информация", {"fields": ("test", "student")}),
        ("Оценка", {"fields": ("grade", "correct_answers_count", "total_questions")}),
        ("Время", {"fields": ("started_at", "completed_at")}),
        ("Устройство и активность", {"fields": ("device_info", "tab_switches_count")}),
    )
    readonly_fields = ("started_at", "correct_answers_count", "total_questions")
    inlines = [StudentAnswerInline]
    actions = ["reset_test_for_students"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Сбросить прохождение теста для выбранных студентов")
    def reset_test_for_students(self, request, queryset):
        for result in queryset:
            result.delete()
        self.message_user(request, f"Сброшено {queryset.count()} результатов")


@admin.register(ArchivedResult)
class ArchivedResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "test",
        "grade",
        "correct_answers_count",
        "total_questions",
        "archived_at",
        "archived_by",
    )
    list_filter = ("grade", "test", "student", "archived_by")
    search_fields = ("student__username", "student__last_name", "test__title")
    ordering = ("-archived_at", "-completed_at", "-started_at")
    raw_id_fields = ("student", "test", "archived_by")
    readonly_fields = (
        "test",
        "student",
        "archived_by",
        "original_result_id",
        "grade",
        "started_at",
        "completed_at",
        "correct_answers_count",
        "total_questions",
        "device_info",
        "tab_switches_count",
        "archived_at",
    )
    inlines = [ArchivedStudentAnswerInline]

    def has_add_permission(self, request):
        return False
