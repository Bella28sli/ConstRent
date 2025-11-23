from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model

from rental_system.models import Role


class Command(BaseCommand):
    help = "Создает базовые роли и по одному сотруднику с захешированными паролями."

    def handle(self, *args, **options):
        roles = ["Администратор", "Руководитель", "Техник", "Менеджер"]

        role_objects = {}
        for name in roles:
            role_obj, _ = Role.objects.get_or_create(role_name=name)
            role_objects[name] = role_obj

        staff_seed = [
            {
                "role": role_objects["Администратор"],
                "last_name": "Иванов",
                "first_name": "Админ",
                "patronymic": "",
                "login": "admin",
                "password": "admin123",
                "email": "admin@example.com",
            },
            {
                "role": role_objects["Руководитель"],
                "last_name": "Петров",
                "first_name": "Руководитель",
                "patronymic": "",
                "login": "lead",
                "password": "lead123",
                "email": "lead@example.com",
            },
            {
                "role": role_objects["Техник"],
                "last_name": "Сидоров",
                "first_name": "Техник",
                "patronymic": "",
                "login": "tech",
                "password": "tech123",
                "email": "tech@example.com",
            },
            {
                "role": role_objects["Менеджер"],
                "last_name": "Кузнецов",
                "first_name": "Менеджер",
                "patronymic": "",
                "login": "manager",
                "password": "manager123",
                "email": "manager@example.com",
            },
        ]

        User = get_user_model()
        created = 0
        for s in staff_seed:
            if User.objects.filter(username=s["login"]).exists():
                continue
            User.objects.create(
                username=s["login"],
                first_name=s["first_name"],
                last_name=s["last_name"],
                email=s["email"],
                password=make_password(s["password"]),
                is_staff=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Готово. Добавлено новых сотрудников: {created}"))
