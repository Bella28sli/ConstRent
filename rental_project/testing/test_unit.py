# -*- coding: utf-8 -*-
import datetime
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import connection
from django.contrib.auth import get_user_model

from rental_system import models as rm
from rental_system.services import RentalService

User = get_user_model()


class BusinessLogicTests(TestCase):
    def setUp(self):
        self.country = rm.EquipmentCountries.objects.create(country="Россия")
        self.brand = rm.EquipmentBrands.objects.create(brand="CAT")
        self.model = rm.EquipmentModels.objects.create(model_name="D6K2")
        self.staff = User.objects.create_user(username="staff", password="staff")
        self.equipment = rm.Equipment.objects.create(
            equipment_name="Бульдозер",
            equipment_code="CAT-D6K2-0001",
            description="",
            model=self.model,
            country=self.country,
            brand=self.brand,
            power=100,
            weight=1000,
            fuel_type="diesel",
            rental_price_day=1000,
            status="available",
        )

        self.client = rm.Client.objects.create(email="c@example.com", phone_number="+70000000000", type="individual")

    def test_generate_equipment_code(self):
        code = rm.Equipment.generate_equipment_code(self.brand, self.model)
        self.assertTrue(code.startswith("CAT-D6K2-"))

    def test_late_fee_calculation(self):
        staff = User.objects.create_user(username="test", password="test123")
        # Создаем аренду с просрочкой 2 дня
        rent = rm.Rent.objects.create(
            client=self.client,
            staff=self.staff,
            rent_agreement_number="A-TEST",
            rent_agreement_date=datetime.date.today(),
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            planned_end_date=datetime.date.today() - datetime.timedelta(days=2),
            actual_end_date=None,
            rent_status="active",
            total_amount=1000,
            is_paid=False,
        )
        fee = RentalService.calculate_late_fee(rent.id)
        self.assertGreaterEqual(fee, 0)

    def test_status_choices(self):
        self.equipment.status = "maintenance"
        self.equipment.save()
        self.assertEqual(rm.Equipment.objects.get(id=self.equipment.id).status, "maintenance")


class ValidationTests(TestCase):
    def test_address_required_fields(self):
        addr = rm.Address(
            region="М", city="Москва", street="", house="1", postal_code="101000", full_address="Москва, Тверская, 1"
        )
        # street пустая – ожидаем ValidationError при full_clean
        with self.assertRaises(ValidationError):
            addr.full_clean()


class MigrationTests(TestCase):
    def test_migrations_applied(self):
        """
        Простейшая проверка: таблица из основной модели существует.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'rental_system_equipment';"
            )
            exists = cursor.fetchone()
        self.assertIsNotNone(exists)
