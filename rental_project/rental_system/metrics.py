from datetime import timedelta
from django.utils import timezone
from prometheus_client import Counter, Gauge, REGISTRY
from rental_system.models import (
    EquipmentBrands,
    Maintenance,
    Rent,
    RentItems,
    Log,
)
from django.db.models import Count, Sum
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# --------- Базовые метрики ---------
http_errors_total = Counter(
    "app_http_errors_total",
    "Количество HTTP-ответов с кодом ошибки",
    ["status_code"],
)

brand_popularity = Gauge(
    "app_brand_popularity",
    "Популярность оборудования по брендам (кол-во арендованных позиций за период)",
    ["brand"],
)

maintenance_completed = Gauge(
    "app_maintenance_completed",
    "Выполненные ТО за период по техникам",
    ["technician"],
)

manager_activity = Gauge(
    "app_rents_created",
    "Активность менеджеров: успешные изменения (POST/PUT) за период",
    ["manager"],
)

finance_profit = Gauge(
    "app_finance_profit",
    "Прибыль за период (закрытые и оплаченные аренды)",
    ["currency"],
)

finance_debt = Gauge(
    "app_finance_debt",
    "Долги (неоплаченные аренды) за период",
    ["currency"],
)

user_activity = Gauge(
    "app_user_activity",
    "Активность пользователей (события в логе за период)",
    ["user"],
)

WINDOW_DAYS = 30


def update_custom_metrics():
    """
    Обновляет значения метрик (оконный период 30 дней).
    """
    since = timezone.now() - timedelta(days=WINDOW_DAYS)

    # 1. Популярность брендов
    brand_popularity.clear()
    brand_counts = (
        RentItems.objects.filter(rent__start_date__gte=since)
        .values("equipment__brand__brand")
        .annotate(cnt=Count("id"))
    )
    for row in brand_counts:
        brand_name = row["equipment__brand__brand"] or "unknown"
        brand_popularity.labels(brand=brand_name).set(row["cnt"])

    # 2. ТО по техникам
    maintenance_completed.clear()
    maint_counts = (
        Maintenance.objects.filter(maintenance_date__gte=since, status="completed")
        .values("staff__username")
        .annotate(cnt=Count("id"))
    )
    for row in maint_counts:
        tech = row["staff__username"] or "unknown"
        maintenance_completed.labels(technician=tech).set(row["cnt"])

    # 3. Активность менеджеров: успешные POST/PUT (берём из логов)
    manager_activity.clear()
    manager_group_ids = list(
        Group.objects.filter(name__in=["manager", "менеджер"]).values_list("id", flat=True)
    )
    activity_counts = (
        Log.objects.filter(
            log_date__gte=since,
            success_status=True,
            staff__groups__id__in=manager_group_ids,
        )
        .values("staff__username")
        .annotate(cnt=Count("id"))
    )
    for row in activity_counts:
        manager = row["staff__username"] or "unknown"
        manager_activity.labels(manager=manager).set(row["cnt"])

    # 4. Финансы: прибыль и долги
    profit_sum = (
        Rent.objects.filter(start_date__gte=since, rent_status="completed", is_paid=True)
        .aggregate(total=Sum("total_amount"))
        .get("total")
        or 0
    )
    debt_sum = (
        Rent.objects.filter(start_date__gte=since, is_paid=False)
        .aggregate(total=Sum("total_amount"))
        .get("total")
        or 0
    )
    finance_profit.labels(currency="RUB").set(float(profit_sum))
    finance_debt.labels(currency="RUB").set(float(debt_sum))

    # 5. Активность пользователей
    user_activity.clear()
    activity_counts = (
        Log.objects.filter(log_date__gte=since)
        .values("staff__username")
        .annotate(cnt=Count("id"))
    )
    for row in activity_counts:
        user = row["staff__username"] or "unknown"
        user_activity.labels(user=user).set(row["cnt"])
