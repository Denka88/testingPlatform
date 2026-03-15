from django.contrib import admin
from .models import Test, Question, Answer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ('text', 'is_correct', 'image', 'order')
    ordering = ('order',)


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = ('text', 'question_type', 'image', 'code_snippet', 'order')
    ordering = ('order',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.extra = 0
        return formset


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'created_by', 'is_published', 'show_correct_answers', 'time_limit', 'created_at')
    list_filter = ('is_published', 'show_correct_answers', 'subject', 'created_by')
    search_fields = ('title', 'description')
    filter_horizontal = ('groups',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'subject', 'created_by')
        }),
        ('Настройки', {
            'fields': ('time_limit', 'is_published', 'show_correct_answers')
        }),
        ('Группы', {
            'fields': ('groups',)
        }),
    )
    
    inlines = [QuestionInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # При создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['duplicate_tests']
    
    @admin.action(description='Дублировать выбранные тесты')
    def duplicate_tests(self, request, queryset):
        for test in queryset:
            test.duplicate()
        self.message_user(request, f"Создано {queryset.count()} копий тестов")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'question_type', 'order', 'created_at')
    list_filter = ('question_type', 'test')
    search_fields = ('text', 'code_snippet')
    inlines = [AnswerInline]
    ordering = ('test', 'order')
    
    fieldsets = (
        ('Вопрос', {
            'fields': ('test', 'text', 'question_type', 'order')
        }),
        ('Медиа', {
            'fields': ('image', 'code_snippet')
        }),
    )
