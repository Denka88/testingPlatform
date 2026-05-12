import math
import time

from django.core.cache import cache

WINDOW_SECONDS = 30
MAX_MESSAGES_PER_WINDOW = 10
MUTE_SECONDS = 60
WARNING_TTL_SECONDS = 1800


def _history_key(user_id):
    return f'chat_rate_limit:history:{user_id}'


def _warning_key(user_id):
    return f'chat_rate_limit:warning:{user_id}'


def _muted_until_key(user_id):
    return f'chat_rate_limit:muted_until:{user_id}'


def get_chat_mute_remaining_seconds(user_id):
    muted_until = cache.get(_muted_until_key(user_id))
    if not muted_until:
        return 0

    remaining = math.ceil(muted_until - time.time())
    if remaining <= 0:
        cache.delete(_muted_until_key(user_id))
        return 0

    return remaining


def register_message_attempt(user_id):
    remaining_seconds = get_chat_mute_remaining_seconds(user_id)
    if remaining_seconds > 0:
        return {
            'status': 'muted',
            'remaining_seconds': remaining_seconds,
        }

    now = time.time()
    history_key = _history_key(user_id)
    history = cache.get(history_key, [])
    history = [timestamp for timestamp in history if now - timestamp <= WINDOW_SECONDS]
    history.append(now)
    cache.set(history_key, history, WINDOW_SECONDS + 5)

    if len(history) <= MAX_MESSAGES_PER_WINDOW:
        return {'status': 'ok'}

    warning_key = _warning_key(user_id)
    warnings_count = cache.get(warning_key, 0)

    if warnings_count >= 1:
        cache.set(_muted_until_key(user_id), now + MUTE_SECONDS, MUTE_SECONDS + 5)
        cache.delete(history_key)
        cache.delete(warning_key)
        return {
            'status': 'muted',
            'remaining_seconds': MUTE_SECONDS,
        }

    cache.set(warning_key, warnings_count + 1, WARNING_TTL_SECONDS)
    cache.delete(history_key)
    return {'status': 'warning'}
