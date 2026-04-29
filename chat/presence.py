from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from .models import Message
from users.models import Profile


PRESENCE_TTL = 60 * 60 * 24


def get_presence_key(user_id):
    return f'chat_presence_connections_{user_id}'


def get_active_presence_key(user_id):
    return f'chat_presence_active_connections_{user_id}'


def get_online_connections(user_id):
    return int(cache.get(get_presence_key(user_id), 0) or 0)


def get_active_online_connections(user_id):
    return int(cache.get(get_active_presence_key(user_id), 0) or 0)


def is_user_online(user_id):
    return get_active_online_connections(user_id) > 0


def mark_user_connected(user_id):
    total_key = get_presence_key(user_id)
    active_key = get_active_presence_key(user_id)
    current_total_count = get_online_connections(user_id)
    current_active_count = get_active_online_connections(user_id)

    cache.set(total_key, current_total_count + 1, PRESENCE_TTL)
    cache.set(active_key, current_active_count + 1, PRESENCE_TTL)
    return current_active_count == 0


def mark_user_disconnected(user_id, was_active=True):
    total_key = get_presence_key(user_id)
    active_key = get_active_presence_key(user_id)
    current_total_count = get_online_connections(user_id)
    current_active_count = get_active_online_connections(user_id)
    next_total_count = max(0, current_total_count - 1)
    next_active_count = max(0, current_active_count - (1 if was_active else 0))

    if next_total_count:
        cache.set(total_key, next_total_count, PRESENCE_TTL)
    else:
        cache.delete(total_key)

    if next_active_count:
        cache.set(active_key, next_active_count, PRESENCE_TTL)
    else:
        cache.delete(active_key)

    return current_active_count > 0 and next_active_count == 0


def mark_connection_active(user_id):
    active_key = get_active_presence_key(user_id)
    current_active_count = get_active_online_connections(user_id)
    cache.set(active_key, current_active_count + 1, PRESENCE_TTL)
    return current_active_count == 0


def mark_connection_idle(user_id):
    active_key = get_active_presence_key(user_id)
    current_active_count = get_active_online_connections(user_id)
    next_active_count = max(0, current_active_count - 1)

    if next_active_count:
        cache.set(active_key, next_active_count, PRESENCE_TTL)
    else:
        cache.delete(active_key)

    return current_active_count > 0 and next_active_count == 0


def update_last_seen(user):
    last_seen_at = timezone.now()
    profile, _ = Profile.objects.get_or_create(user=user)
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode=MEMORY;')

    Profile.objects.filter(pk=profile.pk).update(last_seen_at=last_seen_at)
    profile.last_seen_at = last_seen_at
    return last_seen_at


def get_last_seen_at(user):
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return None
    return profile.last_seen_at


def get_presence_payload(user):
    last_seen_at = get_last_seen_at(user)
    return {
        'user_id': int(user.id),
        'is_online': is_user_online(user.id),
        'last_seen_at': last_seen_at.isoformat() if last_seen_at else '',
    }


def get_related_user_ids(user_id):
    User = get_user_model()
    user_ids = set()

    message_pairs = Message.objects.filter(
        Q(sender_id=user_id) | Q(receiver_id=user_id)
    ).values_list('sender_id', 'receiver_id')

    for sender_id, receiver_id in message_pairs:
        if sender_id != user_id:
            user_ids.add(sender_id)
        if receiver_id != user_id:
            user_ids.add(receiver_id)

    return list(
        User.objects.filter(id__in=user_ids, role__in=['student', 'teacher']).values_list('id', flat=True)
    )
