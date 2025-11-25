from django.db import connection


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
