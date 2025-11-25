from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rental_system import models as rm
from rental_system.services import RentalService


class Command(BaseCommand):
    help = "Заполняет БД тестовыми данными (3–4 записи в основных таблицах). Пользователи не создаются."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        users = {
            "manager": User.objects.filter(username="manager").first(),
            "tech": User.objects.filter(username="tech").first(),
        }

        # Адреса
        addresses = []
        addr_seed = [
            ("Москва", "Москва", "Тверская", "10", None, "125009", "Москва, Тверская, 10"),
            ("Санкт-Петербург", "Санкт-Петербург", "Невский", "35", "Б", "191025", "СПб, Невский 35Б"),
            ("Казань", "Казань", "Баумана", "5", None, "420111", "Казань, Баумана 5"),
            ("Новосибирск", "Новосибирск", "Ленина", "1", None, "630007", "Новосибирск, Ленина 1"),
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
                },
            )
            addresses.append(obj)

        # Клиенты: 2 физлица, 2 компании
        clients = []
        ind_seed = [
            ("iv1@example.com", "+70000000001", "Иванов", "Иван", "Иванович", "1234 567890", "ОВД №1", date(2015, 5, 10), "770-001", date(1990, 1, 1), 0),
            ("pt1@example.com", "+70000000002", "Петров", "Петр", "Петрович", "1234 567891", "ОВД №2", date(2016, 6, 11), "770-002", date(1991, 2, 2), 1),
        ]
        for email, phone, ln, fn, pn, passport, issued_by, issued_date, code, bdate, addr_idx in ind_seed:
            c, _ = rm.Client.objects.get_or_create(email=email, defaults={"phone_number": phone, "type": "individual"})
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
                },
            )
            clients.append(c)

        comp_seed = [
            ("comp1@example.com", "+70000000003", "ООО ПрокатСервис", 2, "7701234567", "770101001", "1207700000000"),
            ("comp2@example.com", "+70000000004", "ООО ТехАренда", 3, "7801234567", "780101001", "1207800000000"),
        ]
        for email, phone, name, addr_idx, inn, kpp, ogrn in comp_seed:
            c, _ = rm.Client.objects.get_or_create(email=email, defaults={"phone_number": phone, "type": "company"})
            rm.CompClient.objects.get_or_create(
                client=c,
                defaults={
                    "company_name": name,
                    "address": addresses[addr_idx],
                    "inn": inn,
                    "kpp": kpp,
                    "ogrn": ogrn,
                    "bank_name": "Банк Развития",
                    "bank_bik": "044525000",
                    "bank_account": "40702810900000000001",
                    "bank_corr": "30101810400000000001",
                    "director_first_name": "Олег",
                    "director_last_name": "Варнава",
                    "director_patronymic": "Иванович",
                    "position": "Генеральный директор",
                },
            )
            clients.append(c)

        # Справочники
        countries = [rm.EquipmentCountries.objects.get_or_create(country=n)[0] for n in ["США", "Германия", "Япония"]]
        brands = [rm.EquipmentBrands.objects.get_or_create(brand=n)[0] for n in ["Caterpillar", "Komatsu", "Volvo"]]
        models = [rm.EquipmentModels.objects.get_or_create(model_name=n)[0] for n in ["Самосвал", "Бульдозер", "Погрузчик"]]

        # Крупногабаритные машины (имя задаём вручную)
        equipments = []
        equipment_seed = [
            ("Бульдозер D6K2", models[1], countries[0], brands[0], 150.0, 12000, "diesel", 15000),
            ("Самосвал A40F", models[0], countries[2], brands[2], 320.0, 19000, "diesel", 22000),
            ("Погрузчик L90H", models[2], countries[1], brands[1], 110.0, 9500, "diesel", 18000),
        ]
        for name, model_obj, country, brand, power, weight, fuel, price in equipment_seed:
            code = rm.Equipment.generate_equipment_code(brand, model_obj)
            eq, _ = rm.Equipment.objects.get_or_create(
                equipment_code=code,
                defaults={
                    "equipment_name": name,
                    "description": f"{name} крупногабаритная машина",
                    "model": model_obj,
                    "country": country,
                    "brand": brand,
                    "power": power,
                    "weight": weight,
                    "fuel_type": fuel,
                    "rental_price_day": price,
                    "status": "available",
                },
            )
            equipments.append(eq)

        # Типы обслуживания
        mtypes = [rm.MaintenanceType.objects.get_or_create(type_name=n)[0] for n in ["Плановое ТО", "Ремонт", "Диагностика"]]

        # Обслуживание
        maint_seed = [
            (timezone.now() + timedelta(days=1), mtypes[0], equipments[0], "Замена расходников", "planned"),
            (timezone.now() + timedelta(days=2), mtypes[1], equipments[1], "Ремонт узлов", "in_progress"),
            (timezone.now() - timedelta(days=1), mtypes[2], equipments[2], "Проверка электроники", "completed"),
        ]
        for dt, mt, eq, desc, status in maint_seed:
            rm.Maintenance.objects.get_or_create(
                maintenance_date=dt,
                equipment=eq,
                defaults={
                    "work_type": mt,
                    "status": status,
                    "staff": users.get("tech"),
                    "description": desc,
                },
            )

        # Аренды: добавлены просроченные и незакрытые
        rent_seed = [
            # активная, просроченная (не вернули)
            (clients[0], equipments[0:1], date.today() - timedelta(days=7), date.today() - timedelta(days=2), None, "active", False),
            # завершена, но не оплачена
            (clients[1], equipments[1:2], date.today() - timedelta(days=10), date.today() - timedelta(days=5), date.today() - timedelta(days=3), "completed", False),
            # активная, оплаченная, срок не вышел
            (clients[2], equipments[2:3], date.today() - timedelta(days=1), date.today() + timedelta(days=4), None, "active", True),
            # ещё одна просроченная и неоплаченная
            (clients[3], equipments[0:2], date.today() - timedelta(days=6), date.today() - timedelta(days=1), None, "active", False),
        ]
        for client, eq_list, start, planned_end, actual_end, status, paid in rent_seed:
            total = RentalService.calculate_rental_cost([e.id for e in eq_list], start, planned_end)
            agreement_number = rm.Rent.generate_agreement_number()
            rent = rm.Rent.objects.create(
                rent_agreement_number=agreement_number,
                client=client,
                staff=users.get("manager"),
                rent_agreement_date=start,
                start_date=start,
                planned_end_date=planned_end,
                actual_end_date=actual_end,
                rent_status=status,
                total_amount=total,
                is_paid=paid,
                payment_date=date.today() if paid else None,
            )
            for eq in eq_list:
                rm.RentItems.objects.create(rent=rent, equipment=eq)
                eq.status = "available" if status == "completed" else "rented"
                eq.save(update_fields=["status"])

        self.stdout.write(self.style.SUCCESS("Тестовые данные добавлены/обновлены."))
