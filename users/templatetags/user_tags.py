from django import template

register = template.Library()


@register.simple_tag
def has_group_permission(user, group):
    """Проверяет, имеет ли пользователь доступ к группе"""
    if user.is_admin:
        return True
    if user.is_teacher:
        return group.subjects.filter(teachers=user).exists()
    if user.is_student:
        return hasattr(user, 'profile') and user.profile.group == group
    return False


@register.simple_tag
def can_access_test(user, test):
    """Проверяет, имеет ли пользователь доступ к тесту"""
    if user.is_admin:
        return True
    if user.is_teacher:
        return test.created_by == user or test.subject.teachers.filter(id=user.id).exists()
    if user.is_student:
        if not test.is_published:
            return False
        return test.groups.filter(id=user.profile.group_id).exists() if hasattr(user, 'profile') else False
    return False


@register.filter
def get_item(dictionary, key):
    """Получение элемента из словаря по ключу"""
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    """Умножение двух значений"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Деление двух значений"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0
