from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Max
from django.http import JsonResponse
from datetime import datetime, timezone
from .models import Message
from .presence import get_last_seen_at, is_user_online

User = get_user_model()


@login_required
def contacts_view(request):
    """
    Страница со списком контактов и поиском пользователей.
    Доступно только для студентов и преподавателей.
    """
    if request.user.role == 'admin':
        return redirect('admin:index')

    # Получаем пользователей, с которыми была переписка
    conversations = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver')

    # Собираем всех собеседников
    conversation_partners = {}
    for msg in conversations:
        partner = msg.sender if msg.receiver_id == request.user.id else msg.receiver
        if partner.id != request.user.id and partner.role != 'admin':
            conversation_partners[partner.id] = partner

    # Формируем список контактов
    contact_list = []

    for partner_id, partner in conversation_partners.items():
        last_message = Message.objects.filter(
            Q(sender=partner, receiver=request.user) |
            Q(sender=request.user, receiver=partner)
        ).order_by('-created_at').first()

        unread_count = Message.objects.filter(
            sender=partner,
            receiver=request.user,
            is_read=False
        ).count()

        contact_list.append({
            'contact': partner,
            'last_message': last_message,
            'unread_count': unread_count,
            'is_online': is_user_online(partner.id),
            'last_seen_at': get_last_seen_at(partner),
        })

    # Сортируем по последнему сообщению
    contact_list.sort(
        key=lambda x: x['last_message'].created_at if x['last_message'] else datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )

    # Активный чат (если выбран через ?chat=<user_id>)
    active_chat = None
    chat_messages = []
    chat_user_id = request.GET.get('chat')
    
    if chat_user_id:
        try:
            active_chat = User.objects.get(id=chat_user_id, role__in=['student', 'teacher'])
            # Получаем историю сообщений с разделителями по датам
            chat_messages = Message.get_conversation_with_dates(request.user, active_chat)
            # Помечаем сообщения как прочитанные
            Message.mark_as_read(request.user, active_chat)
        except User.DoesNotExist:
            pass

    context = {
        'contacts': contact_list,
        'active_chat': active_chat,
        'chat_messages': chat_messages,
        'active_chat_is_online': is_user_online(active_chat.id) if active_chat else False,
        'active_chat_last_seen_at': get_last_seen_at(active_chat) if active_chat else None,
    }
    return render(request, 'chat/contacts.html', context)


@login_required
def search_users_ajax(request):
    """
    AJAX поиск пользователей (case-insensitive).
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'users': []})

    # Разбиваем запрос на слова для более гибкого поиска
    words = query.split()

    # Строим Q-объект: каждое слово ищется в любом из полей (OR между полями, AND между словами)
    q_objects = Q()
    for word in words:
        q_objects &= (
            Q(username__icontains=word) |
            Q(first_name__icontains=word) |
            Q(last_name__icontains=word) |
            Q(email__icontains=word)
        )

    users = User.objects.filter(q_objects).exclude(role='admin').exclude(id=request.user.id)[:15]

    # IDs пользователей, с которыми уже есть переписка
    messages_qs = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    )
    chat_partner_ids = set()
    for msg in messages_qs:
        if msg.sender_id != request.user.id:
            chat_partner_ids.add(msg.sender_id)
        if msg.receiver_id != request.user.id:
            chat_partner_ids.add(msg.receiver_id)

    result = []
    for user in users:
        avatar_url = ''
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar_url = user.profile.avatar.url

        result.append({
            'id': user.id,
            'username': user.username,
            'full_name': f'{user.last_name} {user.first_name}'.strip() or user.username,
            'email': user.email,
            'role': user.get_role_display(),
            'avatar_url': avatar_url,
            'has_chatted': user.id in chat_partner_ids,
        })

    return JsonResponse({'users': result})


# =============================================================================
# Административные views для просмотра чатов
# =============================================================================

@login_required
def admin_chat_list_view(request):
    """
    Список всех активных чатов для администратора.
    Доступно только администраторам.
    """
    if request.user.role != 'admin':
        return redirect('chat:contacts')

    # Получаем все пары пользователей, у которых есть сообщения
    from django.db.models import Min

    # Группируем сообщения по парам пользователей
    conversations = Message.objects.values('sender', 'receiver').annotate(
        last_message=Max('created_at'),
        message_count=Count('id')
    ).order_by('-last_message')

    # Уникальные пары (нормализуем порядок ID)
    seen_pairs = set()
    unique_conversations = []
    for conv in conversations:
        pair = tuple(sorted([conv['sender'], conv['receiver']]))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            user1 = User.objects.get(id=pair[0])
            user2 = User.objects.get(id=pair[1])
            unique_conversations.append({
                'user1': user1,
                'user2': user2,
                'last_message': conv['last_message'],
                'message_count': conv['message_count'],
            })

    context = {
        'conversations': unique_conversations,
    }
    return render(request, 'chat/admin_chat_list.html', context)


@login_required
def admin_chat_view(request, user1_id, user2_id):
    """
    Просмотр переписки между двумя пользователями (для администратора).
    """
    if request.user.role != 'admin':
        return redirect('chat:contacts')

    user1 = get_object_or_404(User, id=user1_id)
    user2 = get_object_or_404(User, id=user2_id)

    # Получаем историю сообщений
    chat_messages = Message.get_conversation(user1, user2)

    context = {
        'user1': user1,
        'user2': user2,
        'chat_messages': chat_messages,
    }
    return render(request, 'chat/admin_chat.html', context)
