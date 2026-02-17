# -*- coding: utf-8 -*-
import random
import string
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from rental_system import models as rm


User = get_user_model()


def random_code(prefix: str, length: int = 6) -> str:
    return f"{prefix}-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class Command(BaseCommand):
    """
    Нагрузочная заготовка:
    - массовое создание оборудования (bulk_create);
    - массовое создание аренд с позицией оборудования;
    - массовое обновление оборудования.

    Пример:
        python manage.py load_test_data --equipment 2000 --rents 800 --update 500 --chunk 500
    """

    help = "Массовое создание и обновление оборудования/аренд для нагрузочного тестирования."

    def add_arguments(self, parser):
        parser.add_argument("--equipment", type=int, default=0, help="Сколько новых единиц оборудования создать")
        parser.add_argument("--rents", type=int, default=0, help="Сколько аренд создать")
        parser.add_argument("--update", type=int, default=0, help="Сколько единиц оборудования обновить (статус/цену)")
        parser.add_argument("--chunk", type=int, default=500, help="Размер пачки bulk_create/bulk_update")
        parser.add_argument("--max-items-per-rent", type=int, default=3, help="Максимум позиций оборудования на аренду")

    def handle(self, *args, **options):
        equipment_count = options["equipment"]
        rents_count = options["rents"]
        update_count = options["update"]
        chunk_size = options["chunk"]
        max_items_per_rent = options["max_items_per_rent"]

        self.stdout.write(self.style.MIGRATE_HEADING("Генерируем справочники/пользователей..."))
        country, _ = rm.EquipmentCountries.objects.get_or_create(country="Россия")
        brand, _ = rm.EquipmentBrands.objects.get_or_create(brand="LOAD")
        model, _ = rm.EquipmentModels.objects.get_or_create(model_name="PERF")
        client, _ = rm.Client.objects.get_or_create(email="loadtest@example.com", phone_number="+70000000001", type="individual")
        if not rm.IndClient.objects.filter(client=client).exists():
            addr = rm.Address.objects.create(
                region="М", city="Москва", street="Тестовая", house="1", postal_code="101000", full_address="Москва, Тестовая, 1"
            )
            rm.IndClient.objects.create(
                client=client,
                last_name="Тестов",
                first_name="Тест",
                patronymic="Тестович",
                passport_number="9999 999999",
                passport_issued_by="ОВД",
                passport_issued_date="2020-01-01",
                passport_code="770-001",
                birth_date="1990-01-01",
                registration_address=addr,
                actual_address=addr,
            )

        staff = User.objects.filter(is_staff=True).first()
        if not staff:
            staff = User.objects.create_superuser(username="load_admin", email="load_admin@example.com", password="load_admin")
            self.stdout.write(self.style.WARNING("Создан тестовый суперпользователь load_admin / load_admin"))

        # Массовое создание оборудования
        if equipment_count > 0:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Создаем оборудование: {equipment_count}"))
            batch = []
            created = 0
            for i in range(equipment_count):
                code = f"LOAD-{random_code('EQ', 4)}-{i:04d}"
                batch.append(
                    rm.Equipment(
                        equipment_name=f"Нагрузка-{i}",
                        equipment_code=code,
                        description="Тест нагрузка",
                        model=model,
                        country=country,
                        brand=brand,
                        power=100 + i % 50,
                        weight=1000 + i % 300,
                        fuel_type="diesel",
                        rental_price_day=5000 + i % 2000,
                        status="available",
                    )
                )
                if len(batch) >= chunk_size:
                    rm.Equipment.objects.bulk_create(batch, ignore_conflicts=True)
                    created += len(batch)
                    batch.clear()
            if batch:
                rm.Equipment.objects.bulk_create(batch, ignore_conflicts=True)
                created += len(batch)
            self.stdout.write(self.style.SUCCESS(f"Готово: создано ~{created} единиц оборудования"))

        equipments = list(rm.Equipment.objects.all())

        # Массовое создание аренд с транзакцией
        if rents_count > 0 and equipments:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Создаем аренды: {rents_count}"))
            rents_created = 0
            rent_items = []
            today = date.today()

            for i in range(rents_count):
                # выбираем случайные позиции
                items = random.sample(equipments, k=min(max_items_per_rent, len(equipments)))
                with transaction.atomic():
                    rent = rm.Rent.objects.create(
                        client=client,
                        staff=staff,
                        rent_agreement_number=rm.Rent.generate_agreement_number(),
                        rent_agreement_date=today,
                        start_date=today,
                        planned_end_date=today + timedelta(days=7),
                        rent_status="active",
                        total_amount=10000,
                        is_paid=False,
                    )
                    for eq in items:
                        rent_items.append(rm.RentItems(rent=rent, equipment=eq))
                    # Обновляем статус использованного оборудования
                    rm.Equipment.objects.filter(id__in=[eq.id for eq in items]).update(status="rented")
                rents_created += 1
                # вставляем пачками
                if len(rent_items) >= chunk_size:
                    rm.RentItems.objects.bulk_create(rent_items, ignore_conflicts=True)
                    rent_items.clear()

            if rent_items:
                rm.RentItems.objects.bulk_create(rent_items, ignore_conflicts=True)

            self.stdout.write(self.style.SUCCESS(f"Готово: создано {rents_created} аренд"))

        # Массовое обновление оборудования (устойчивость UPDATE)
        if update_count > 0:
            self.stdout.write(self.style.MIGRATE_HEADING(f"Обновляем оборудование: {update_count} записей"))
            qs = rm.Equipment.objects.all()[:update_count]
            for chunk_start in range(0, qs.count(), chunk_size):
                chunk = list(qs[chunk_start:chunk_start + chunk_size])
                for obj in chunk:
                    obj.status = "maintenance" if obj.status == "available" else "available"
                    obj.rental_price_day = obj.rental_price_day + 100
                rm.Equipment.objects.bulk_update(chunk, ["status", "rental_price_day"])
            self.stdout.write(self.style.SUCCESS("Обновление выполнено"))

        self.stdout.write(self.style.NOTICE("Завершено. Используйте Prometheus/Grafana для наблюдения за метриками под нагрузкой."))
