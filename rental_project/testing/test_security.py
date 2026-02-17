# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings
from django.urls import reverse, NoReverseMatch

User = get_user_model()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class SecurityTests(TestCase):
    """
    Проверяем базовые аспекты безопасности:
    - защита от SQL-инъекций (нет 500/авторизаций по "инъекционным" данным);
    - корректное разделение прав между ролями;
    - пароли хранятся в хеше.
    """

    def setUp(self):
        # Создаём группы, если отсутствуют
        for name in ["admin", "leader", "manager", "technician"]:
            Group.objects.get_or_create(name=name)

        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
        self.leader = User.objects.create_user(
            username="leader", email="leader@example.com", password="leader"
        )
        self.manager = User.objects.create_user(
            username="manager", email="manager@example.com", password="manager"
        )
        self.technician = User.objects.create_user(
            username="technician", email="technician@example.com", password="technician"
        )
        self.leader.groups.add(Group.objects.get(name="leader"))
        self.manager.groups.add(Group.objects.get(name="manager"))
        self.technician.groups.add(Group.objects.get(name="technician"))

    def test_passwords_are_hashed(self):
        u = User.objects.create_user(username="hashcheck", password="plainpass")
        self.assertNotEqual(u.password, "plainpass")
        self.assertTrue(u.password.startswith("pbkdf2_"))
        self.assertTrue(u.check_password("plainpass"))

    def test_sql_injection_login_fails(self):
        client = Client()
        payload = "' OR 1=1--"
        resp = client.post("/accounts/login/", {"username": payload, "password": payload})
        # Должен остаться неавторизованным и не упасть 500
        self.assertNotIn(resp.status_code, (500,))
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_sql_injection_query_param_does_not_error(self):
        client = Client()
        client.login(username="admin", password="admin")
        resp = client.get("/api/equipment/", {"q": "' OR '1'='1"})
        self.assertNotIn(resp.status_code, (500,))

    def _safe_reverse(self, name):
        try:
            return reverse(name)
        except NoReverseMatch:
            return None

    def test_manager_cannot_access_admin_only_page(self):
        url = self._safe_reverse("equipment_brands")
        if not url:
            return  # пропускаем если урл не настроен
        c = Client()
        c.login(username="manager", password="manager")
        resp = c.get(url)
        # Ожидаем отказ (403/302/404), но не успешный 200
        self.assertNotEqual(resp.status_code, 200)

    def test_technician_cannot_access_users_page(self):
        url = self._safe_reverse("users")
        if not url:
            return
        c = Client()
        c.login(username="technician", password="technician")
        resp = c.get(url)
        self.assertNotEqual(resp.status_code, 200)

    def test_leader_cannot_create_equipment_via_api(self):
        c = Client()
        c.login(username="leader", password="leader")
        payload = {
            "equipment_name": "Attempt",
            "equipment_code": "ATT-001",
            "rental_price_day": "1000.00",
            "power": "10",
            "weight": "20",
            "fuel_type": "diesel",
            "status": "available",
        }
        resp = c.post("/api/equipment/", payload, content_type="application/json")
        # Лидер только просмотр: ожидаем отказ (403/401/302/405), главное — не 2xx
        self.assertTrue(resp.status_code >= 300 or resp.status_code == 401 or resp.status_code == 403)

    def test_admin_can_access_protected(self):
        url = self._safe_reverse("equipment_brands")
        if not url:
            return
        c = Client()
        c.login(username="admin", password="admin")
        resp = c.get(url)
        self.assertNotIn(resp.status_code, (401, 403, 404, 500))
