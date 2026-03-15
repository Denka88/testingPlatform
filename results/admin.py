from django.contrib import admin
from .models import Result, StudentAnswer


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'is_correct')
    filter_horizontal = ('answers',)
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'grade', 'correct_answers_count', 'total_questions', 
                    'started_at', 'completed_at', 'device_info', 'tab_switches_count')
    list_filter = ('grade', 'test', 'student', 'is_reset')
    search_fields = ('student__username', 'student__last_name', 'test__title')
    ordering = ('-completed_at', '-started_at')
    raw_id_fields = ('student', 'test')
    
    fieldsets = (
        ('Информация', {
            'fields': ('test', 'student')
        }),
        ('Оценка', {
            'fields': ('grade', 'correct_answers_count', 'total_questions')
        }),
        ('Время', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Устройство и активность', {
            'fields': ('device_info', 'tab_switches_count')
        }),
        ('Статус', {
            'fields': ('is_reset',)
        }),
    )
    
    readonly_fields = ('started_at', 'correct_answers_count', 'total_questions')
    
    inlines = [StudentAnswerInline]
    
    actions = ['reset_test_for_students']
    
    @admin.action(description='Сбросить прохождение теста для выбранных студентов')
    def reset_test_for_students(self, request, queryset):
        for result in queryset:
            result.is_reset = True
            result.grade = None
            result.save()
        self.message_user(request, f"Сброшено {queryset.count()} результатов")
