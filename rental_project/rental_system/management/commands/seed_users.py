from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Создает пользователей для групп Руководитель, Техник и Менеджер с простыми паролями."

    def handle(self, *args, **options):
        User = get_user_model()

        # гарантируем, что группы существуют
        leader_group, _ = Group.objects.get_or_create(name="Руководитель")
        tech_group, _ = Group.objects.get_or_create(name="Техник")
        manager_group, _ = Group.objects.get_or_create(name="Менеджер")

        users_seed = [
            {
                "username": "leader",
                "first_name": "Дмитрий",
                "last_name": "Ллойд",
                "email": "leader@example.com",
                "password": "leader123",
                "groups": [leader_group],
            },
            {
                "username": "tech",
                "first_name": "Майк",
                "last_name": "Уилер",
                "email": "tech@example.com",
                "password": "tech123",
                "groups": [tech_group],
            },
            {
                "username": "manager",
                "first_name": "Уилл",
                "last_name": "Байерс",
                "email": "manager@example.com",
                "password": "manager123",
                "groups": [manager_group],
            },
        ]

        created = 0
        for u in users_seed:
            if User.objects.filter(username=u["username"]).exists():
                continue
            user = User.objects.create(
                username=u["username"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                email=u["email"],
                password=make_password(u["password"]),
                is_staff=False,
                is_superuser=False,
            )
            user.groups.set(u["groups"])
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Готово. Добавлено пользователей: {created}"))
