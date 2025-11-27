from django import template

register = template.Library()


ALIASES = {
    "admin": ["admin", "администратор", "админ", "администратор системы"],
    "leader": ["leader", "руководитель"],
    "manager": ["manager", "менеджер"],
    "technician": ["technician", "техник", "технический специалист"],
}


def _normalize_names(raw: str):
    if not raw:
        return []
    result = []
    for g in raw.split(","):
        g = g.strip().lower()
        if not g:
            continue
        result.append(g)
        # расширяем псевдонимы
        for k, alias_list in ALIASES.items():
            if g == k or g in alias_list:
                result.extend(alias_list)
                result.append(k)
    return set(result)


@register.filter
def has_group(user, group_name: str) -> bool:
    """Проверяет, состоит ли пользователь в группе (с учетом алиасов и регистра)."""
    try:
        if not user.is_authenticated:
            return False
        names = _normalize_names(group_name)
        user_groups = set(name.lower() for name in user.groups.values_list("name", flat=True))
        return bool(user_groups.intersection(names))
    except Exception:
        return False


@register.filter
def any_group(user, group_names: str) -> bool:
    """
    Проверяет, состоит ли пользователь хотя бы в одной из перечисленных групп
    (учитываются псевдонимы из ALIASES).
    """
    try:
        if not user.is_authenticated:
            return False
        names = _normalize_names(group_names)
        user_groups = set(name.lower() for name in user.groups.values_list("name", flat=True))
        return bool(user_groups.intersection(names))
    except Exception:
        return False
