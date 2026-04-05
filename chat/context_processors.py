from .models import Message


def unread_messages_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'total_unread_messages': count}
    return {'total_unread_messages': 0}
