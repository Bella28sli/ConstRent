from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from .metrics import http_errors_total
from rental_system.models import Log


class CurrentUserToDBMiddleware:
    """
    Прокидывает ID текущего пользователя в PostgreSQL через session setting
    application.user_id, чтобы триггеры могли писать staff_id.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.user.id if hasattr(request, "user") and request.user.is_authenticated else None
        with connection.cursor() as cursor:
            if user_id:
                cursor.execute("SET SESSION application.user_id = %s", [user_id])
            else:
                cursor.execute("SET SESSION application.user_id = DEFAULT")

        response = self.get_response(request)

        # Сбрасываем после запроса
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION application.user_id = DEFAULT")

        return response


class HttpErrorMetricsMiddleware:
    """
    Считает HTTP-ошибки (4xx/5xx) в счетчик prometheus.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            status = response.status_code
            if status >= 400:
                http_errors_total.labels(str(status)).inc()
        except Exception:
            pass
        return response


class ActionLogMiddleware(MiddlewareMixin):
    """
    Универсальный лог: фиксируем большинство действий по HTTP-методам.
    GET  -> VIEW, POST -> CREATE, PUT/PATCH -> UPDATE, DELETE -> DELETE.
    Для путей с export/download — DOWNLOAD, import/upload — UPLOAD.
    """

    def process_response(self, request, response):
        try:
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return response

            path = request.path or ""
            if path.startswith("/static") or path.startswith("/prometheus"):
                return response

            method = request.method.upper()
            action = Log.ActionType.VIEW
            if any(k in path for k in ["export", "download", "backup"]):
                action = Log.ActionType.DOWNLOAD
            elif any(k in path for k in ["import", "upload"]):
                action = Log.ActionType.UPLOAD
            elif method == "POST":
                action = Log.ActionType.CREATE
            elif method in ("PUT", "PATCH"):
                action = Log.ActionType.UPDATE
            elif method == "DELETE":
                action = Log.ActionType.DELETE

            Log.objects.create(
                staff=user,
                action_type=action,
                description_text=f"{method} {path}",
                success_status=response.status_code < 400,
            )
        except Exception:
            pass
        return response
