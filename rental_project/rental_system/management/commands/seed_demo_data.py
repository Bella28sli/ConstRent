from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rental_system import models as rm


class Command(BaseCommand):
    help = "Заполняет БД демонстрационными данными (минимум 3 записи в каждой сущности)."

    @transaction.atomic
    def handle(self, *args, **options):

        # Адреса
        addresses = []
        addr_seed = [
            ("Москва", "Москва", "Тверская", "10", None, "125009", "Москва, Тверская, 10"),
            ("Санкт-Петербург", "Санкт-Петербург", "Невский", "35", "Б", "191025", "СПб, Невский 35Б"),
            ("Казань", "Казань", "Баумана", "5", None, "420111", "Казань, Баумана 5"),
        ]
        for region, city, street, house, building, postal, full in addr_seed:
            obj, _ = rm.Address.objects.get_or_create(
                full_address=full,
                defaults={
                    "region": region,
                    "city": city,
                    "street": street,
                    "house": house,
                    "building": building,
                    "postal_code": postal,
                }
            )
            addresses.append(obj)

        # Клиенты
        clients = []
        # Физлица
        ind_seed = [
            ("ivanoff@example.com", "+70000000001", "individual", "Иванов", "Иван", "Иванович", "1234 567890", "ОВД №1", date(2015, 5, 10), "770-001", date(1990, 1, 1), 0),
            ("petroff@example.com", "+70000000002", "individual", "Петров", "Петр", "Петрович", "1234 567891", "ОВД №2", date(2016, 6, 11), "770-002", date(1991, 2, 2), 1),
        ]
        for email, phone, ctype, ln, fn, pn, passport, issued_by, issued_date, code, bdate, addr_idx in ind_seed:
            c, _ = rm.Client.objects.get_or_create(email=email, defaults={"phone_number": phone, "type": ctype})
            rm.IndClient.objects.get_or_create(
                client=c,
                defaults={
                    "last_name": ln,
                    "first_name": fn,
                    "patronymic": pn,
                    "passport_number": passport,
                    "passport_issued_by": issued_by,
                    "passport_issued_date": issued_date,
                    "passport_code": code,
                    "birth_date": bdate,
                    "registration_address": addresses[addr_idx],
                    "actual_address": addresses[addr_idx],
                }
            )
            clients.append(c)

        # Юрлицо
        comp_email = "company@example.com"
        comp_client, _ = rm.Client.objects.get_or_create(email=comp_email, defaults={"phone_number": "+70000000003", "type": "company"})
        rm.CompClient.objects.get_or_create(
            client=comp_client,
            defaults={
                "company_name": "ООО ПрокатСервис",
                "address": addresses[2],
                "inn": "7701234567",
                "kpp": "770101001",
                "ogrn": "1207700000000",
                "bank_name": "Банк Развития",
                "bank_bik": "044525000",
                "bank_account": "40702810900000000001",
                "bank_corr": "30101810400000000001",
                "director_first_name": "Олег",
                "director_last_name": "Директор",
                "director_patronymic": "Иванович",
                "position": "Генеральный директор",
            }
        )
        clients.append(comp_client)

        # Страны, бренды, модели
        countries = [rm.EquipmentCountries.objects.get_or_create(country=n)[0] for n in ["Россия", "Германия", "Япония"]]
        brands = [rm.EquipmentBrands.objects.get_or_create(brand=n)[0] for n in ["Bosch", "Makita", "Interskol"]]
        models = [rm.EquipmentModels.objects.get_or_create(model_name=n)[0] for n in ["DR-100", "MX-200", "IS-300"]]

        # Оборудование
        equipment_seed = [
            ("Перфоратор", "EQ-001", "Мощный перфоратор", models[0], countries[0], brands[0], 2.5, 3.2, "electric", 1200),
            ("Шуруповерт", "EQ-002", "Аккумуляторный шуруповерт", models[1], countries[1], brands[1], 0.5, 1.1, "electric", 800),
            ("Болгарка", "EQ-003", "Углошлифовальная машина", models[2], countries[2], brands[2], 1.8, 2.0, "electric", 900),
        ]
        equipments = []
        for name, code, desc, model, country, brand, power, weight, fuel, price in equipment_seed:
            eq, _ = rm.Equipment.objects.get_or_create(
                equipment_code=code,
                defaults={
                    "equipment_name": name,
                    "description": desc,
                    "model": model,
                    "country": country,
                    "brand": brand,
                    "power": power,
                    "weight": weight,
                    "fuel_type": fuel,
                    "rental_price_day": price,
                    "status": "available",
                }
            )
            equipments.append(eq)

        # Типы обслуживания
        mtypes = [rm.MaintenanceType.objects.get_or_create(type_name=n)[0] for n in ["Плановое ТО", "Ремонт", "Диагностика"]]

        self.stdout.write(self.style.SUCCESS("Демо-данные созданы/обновлены."))
