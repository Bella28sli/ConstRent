from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django import template
from rental_system.models import UserPreference

register = template.Library()


DATE_MAP = {
    "YYYY-MM-DD": "%Y-%m-%d",
    "DD.MM.YYYY": "%d.%m.%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
}

NUMBER_MAP = {
    UserPreference.NumberFormat.SPACE: (" ", "."),
    UserPreference.NumberFormat.COMMA: (",", "."),
    UserPreference.NumberFormat.DOT: (".", ","),
}


def _get_pref(request):
    if not request or not request.user.is_authenticated:
        return None
    return UserPreference.objects.filter(user=request.user).first()


@register.simple_tag(takes_context=True)
def user_date(context, value):
    if value is None:
        return ""
    request = context.get("request")
    pref = _get_pref(request)
    fmt = DATE_MAP.get(pref.date_format if pref else None, "%d.%m.%Y")
    try:
        # datetime/date both support strftime
        return value.strftime(fmt + (" %H:%M" if hasattr(value, "hour") else ""))
    except Exception:
        return value


@register.simple_tag(takes_context=True)
def user_number(context, value):
    if value is None:
        return ""
    request = context.get("request")
    pref = _get_pref(request)
    thousands, dec_sep = NUMBER_MAP.get(
        pref.number_format if pref else UserPreference.NumberFormat.SPACE,
        (" ", "."),
    )
    try:
        dec = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError):
        return value
    sign = "-" if dec < 0 else ""
    int_str, frac_str = f"{abs(dec):.2f}".split(".")
    grouped = ""
    while len(int_str) > 3:
        grouped = thousands + int_str[-3:] + grouped
        int_str = int_str[:-3]
    grouped = int_str + grouped
    return f"{sign}{grouped}{dec_sep}{frac_str}"
