from django.contrib import admin
from .models import Contact, Message


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name',
                     'contact__username', 'contact__first_name', 'contact__last_name')
    raw_id_fields = ('user', 'contact')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'text_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'sender__first_name', 'sender__last_name',
                     'receiver__username', 'receiver__first_name', 'receiver__last_name',
                     'text')
    raw_id_fields = ('sender', 'receiver')
    date_hierarchy = 'created_at'

    def text_preview(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')
    text_preview.short_description = 'Текст'
