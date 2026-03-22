from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, OuterRef, Subquery, Max
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse
from .models import Contact, Message

User = get_user_model()


@login_required
def contacts_view(request):
    """
    Страница со списком контактов и поиском пользователей.
    Доступно только для студентов и преподавателей.
    """
    if request.user.role == 'admin':
        return redirect('admin:index')

    # Получаем контакты пользователя
    contacts = Contact.objects.filter(user=request.user).select_related('contact')
    contact_ids = set(c.contact_id for c in contacts)

    # Получаем пользователей, с которыми была переписка (но не в контактах)
    conversations = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver')

    # Собираем всех собеседников
    conversation_partners = []
    for msg in conversations:
        partner = msg.sender if msg.receiver_id == request.user.id else msg.receiver
        if partner.id != request.user.id and partner.id not in contact_ids and partner.role != 'admin':
            contact_ids.add(partner.id)
            conversation_partners.append(partner)

    # Формируем список контактов (добавленные + переписка)
    contact_list = []

    # Добавленные контакты
    for contact in contacts:
        last_message = Message.objects.filter(
            Q(sender=contact.contact, receiver=request.user) |
            Q(sender=request.user, receiver=contact.contact)
        ).order_by('-created_at').first()

        unread_count = Message.objects.filter(
            sender=contact.contact,
            receiver=request.user,
            is_read=False
        ).count()

        contact_list.append({
            'contact': contact.contact,
            'last_message': last_message,
            'unread_count': unread_count,
            'is_contact': True,  # явно добавлен в контакты
        })

    # Собеседники из переписки (не добавленные в контакты)
    for partner in conversation_partners:
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
            'is_contact': False,  # не добавлен в контакты
        })

    # Сортируем по последнему сообщению
    contact_list.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else None, reverse=True)

    # Поиск пользователей (не администраторов)
    search_query = request.GET.get('search', '')
    users_found = []
    if search_query:
        # Исключаем администраторов и самого себя
        users = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        ).exclude(role='admin').exclude(id=request.user.id)

        # Добавляем флаг: уже в контактах
        my_contact_ids = Contact.objects.filter(user=request.user).values_list('contact_id', flat=True)
        users_found = [
            {
                'user': user,
                'is_contact': user.id in my_contact_ids,
            }
            for user in users[:20]  # Ограничиваем результат
        ]

    # Активный чат (если выбран через ?chat=<user_id>)
    active_chat = None
    messages = []
    chat_user_id = request.GET.get('chat')
    
    if chat_user_id:
        try:
            active_chat = User.objects.get(id=chat_user_id, role__in=['student', 'teacher'])
            # Получаем историю сообщений
            messages = Message.get_conversation(request.user, active_chat)
            # Помечаем сообщения как прочитанные
            Message.mark_as_read(request.user, active_chat)
        except User.DoesNotExist:
            pass

    context = {
        'contacts': contact_list,
        'users_found': users_found,
        'search_query': search_query,
        'active_chat': active_chat,
        'messages': messages,
    }
    return render(request, 'chat/contacts.html', context)


@login_required
@require_POST
def add_contact_view(request):
    """
    Добавить пользователя в контакты.
    """
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Не указан пользователь'}, status=400)

    other_user = get_object_or_404(User, id=user_id)

    if other_user.role == 'admin':
        return JsonResponse({'error': 'Нельзя добавить администратора в контакты'}, status=403)

    if other_user.id == request.user.id:
        return JsonResponse({'error': 'Нельзя добавить себя в контакты'}, status=400)

    contact, created = Contact.objects.get_or_create(
        user=request.user,
        contact=other_user
    )

    return JsonResponse({
        'success': True,
        'created': created,
        'message': 'Контакт добавлен' if created else 'Уже в контактах'
    })


@login_required
@require_POST
def remove_contact_view(request):
    """
    Удалить пользователя из контактов.
    """
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Не указан пользователь'}, status=400)

    other_user = get_object_or_404(User, id=user_id)

    Contact.objects.filter(user=request.user, contact=other_user).delete()

    return JsonResponse({'success': True, 'message': 'Контакт удалён'})


@login_required
@require_GET
def search_users_view(request):
    """
    AJAX поиск пользователей.
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'users': []})

    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(role='admin').exclude(id=request.user.id)[:10]

    my_contact_ids = list(Contact.objects.filter(user=request.user).values_list('contact_id', flat=True))

    result = [
        {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'is_contact': user.id in my_contact_ids,
        }
        for user in users
    ]

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
    messages = Message.get_conversation(user1, user2)

    context = {
        'user1': user1,
        'user2': user2,
        'messages': messages,
    }
    return render(request, 'chat/admin_chat.html', context)
