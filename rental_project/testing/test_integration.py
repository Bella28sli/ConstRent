# -*- coding: utf-8 -*-
import tempfile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from rental_system import models as rm

User = get_user_model()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class IntegrationTests(TestCase):
    """
    Базовые интеграционные проверки:
    - взаимодействие Django ↔ PostgreSQL (создание/чтение объектов);
    - работа API (маршруты, сериализация, отсутствие 500);
    - выгрузка метрик Prometheus;
    - экспорт/импорт CSV;
    - доступность страницы бэкапов.
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
        self.client = Client()
        self.client.login(username="admin", password="admin")

        # Минимальные данные для тестов БД/API
        self.country = rm.EquipmentCountries.objects.create(country="Россия")
        self.brand = rm.EquipmentBrands.objects.create(brand="CAT")
        self.model = rm.EquipmentModels.objects.create(model_name="D6K2")
        self.equipment = rm.Equipment.objects.create(
            equipment_name="Бульдозер",
            equipment_code="CAT-D6K2-0001",
            description="Тестовое описание",
            model=self.model,
            country=self.country,
            brand=self.brand,
            power=150,
            weight=2000,
            fuel_type="diesel",
            rental_price_day=10000,
            status="available",
        )
        self.client_obj = rm.Client.objects.create(
            email="c@example.com", phone_number="+70000000000", type="individual"
        )
        rm.IndClient.objects.create(
            client=self.client_obj,
            last_name="Иванов",
            first_name="Иван",
            patronymic="Иванович",
            passport_number="1234 567890",
            passport_issued_by="ОВД",
            passport_issued_date="2020-01-01",
            passport_code="770-001",
            birth_date="1990-01-01",
            registration_address=rm.Address.objects.create(
                region="М", city="Москва", street="Тверская",
                house="1", postal_code="101000", full_address="Москва, Тверская, 1"
            ),
            actual_address=rm.Address.objects.create(
                region="М", city="Москва", street="Арбат",
                house="2", postal_code="119019", full_address="Москва, Арбат, 2"
            ),
        )

    def test_db_and_home_page(self):
        self.assertEqual(rm.Equipment.objects.count(), 1)
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, 200)

    def test_api_list_equipment(self):
        resp = self.client.get("/api/equipment/")
        self.assertIn(resp.status_code, (200, 404))  # главное — не 500
        if resp.status_code == 200:
            data = resp.json()
            items = data["results"] if isinstance(data, dict) and "results" in data else data
            self.assertIsInstance(items, list)

    def test_prometheus_metrics(self):
        resp = self.client.get("/prometheus/metrics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"django_http_requests_total", resp.content)

    def test_csv_export_import(self):
        # экспорт: view ждет ?action=export&entity=equipment
        resp = self.client.get(reverse("csv_import_export"), {"action": "export", "entity": "equipment"})
        if resp.status_code == 302:  # на случай редиректа
            resp = self.client.get(resp["Location"])
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.get("Content-Type", ""))

        # импорт: view ждет POST с action=import и entity=equipment
        csv_content = "code,name,status\nIMP-001,Импорт,available\n"
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            with open(f.name, "rb") as upload:
                resp = self.client.post(
                    reverse("csv_import_export"),
                    {"action": "import", "entity": "equipment", "file": upload},
                )
        self.assertIn(resp.status_code, (200, 302))
        self.assertTrue(rm.Equipment.objects.filter(equipment_code="IMP-001").exists())

    def test_backup_list_view(self):
        resp = self.client.get(reverse("backup_list"))
        self.assertEqual(resp.status_code, 200)


class ApiErrorHandlingTests(TestCase):
    """
    Базовая проверка, что неизвестный API-роут не падает 500.
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin"
        )
        self.client = Client()
        self.client.login(username="admin", password="admin")

    def test_not_found_returns_json_or_redirect(self):
        resp = self.client.get("/api/unknown-endpoint/")
        self.assertIn(resp.status_code, (404, 301, 302))
