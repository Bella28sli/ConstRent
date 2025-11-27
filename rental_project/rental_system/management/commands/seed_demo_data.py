from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rental_system import models as rm
from rental_system.services import RentalService


class Command(BaseCommand):
    help = (
        "Seed demo data for all tables (15+ rows per table, diverse rent scenarios). "
        "Safe to run multiple times; uses get_or_create."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        manager, _ = User.objects.get_or_create(
            username="manager", defaults={"email": "manager@example.com", "is_staff": True}
        )
        tech, _ = User.objects.get_or_create(
            username="tech", defaults={"email": "tech@example.com", "is_staff": True}
        )
        leader, _ = User.objects.get_or_create(
            username="leader", defaults={"email": "leader@example.com", "is_staff": True}
        )
        users = {"manager": manager, "tech": tech, "leader": leader}

        # Addresses (15)
        addresses = []
        addr_seed = [
            ("Moscow oblast", "Moscow", "Tverskaya", "10", None, "125009", "Moscow, Tverskaya, 10"),
            ("Saint-Petersburg", "Saint-Petersburg", "Nevsky", "35", "B", "191025", "Saint-Petersburg, Nevsky, 35B"),
            ("Tatarstan", "Kazan", "Baumana", "5", None, "420111", "Kazan, Baumana, 5"),
            ("Siberia", "Novosibirsk", "Lenina", "1", None, "630007", "Novosibirsk, Lenina, 1"),
            ("Urals", "Yekaterinburg", "Malysheva", "15", None, "620014", "Yekaterinburg, Malysheva, 15"),
            ("Nizhny Novgorod", "Nizhny Novgorod", "Bolshaya Pokrovskaya", "22", None, "603000", "Nizhny Novgorod, Bolshaya Pokrovskaya, 22"),
            ("Krasnodar", "Krasnodar", "Krasnaya", "120", None, "350000", "Krasnodar, Krasnaya, 120"),
            ("Samara", "Samara", "Leningradskaya", "45", None, "443000", "Samara, Leningradskaya, 45"),
            ("Rostov", "Rostov-on-Don", "Pushkinskaya", "78", None, "344000", "Rostov-on-Don, Pushkinskaya, 78"),
            ("Perm", "Perm", "Komsomolsky", "50", None, "614000", "Perm, Komsomolsky, 50"),
            ("Chelyabinsk", "Chelyabinsk", "Truda", "12", None, "454000", "Chelyabinsk, Truda, 12"),
            ("Voronezh", "Voronezh", "Revolutsii", "30", None, "394000", "Voronezh, Revolutsii, 30"),
            ("Khabarovsk", "Khabarovsk", "Muravyova-Amurskogo", "14", None, "680000", "Khabarovsk, Muravyova-Amurskogo, 14"),
            ("Sochi", "Sochi", "Kurortny", "8", "A", "354000", "Sochi, Kurortny, 8A"),
            ("Omsk", "Omsk", "Frunze", "6", None, "644000", "Omsk, Frunze, 6"),
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

        # Individual clients (10)
        clients = []
        ind_seed = [
            ("iv1@example.com", "+70000000001", "Ivanov", "Ivan", "Petrovich", "1234 567890", "OVD Moscow", date(2015, 5, 10), "770-001", date(1990, 1, 1), 0),
            ("pt1@example.com", "+70000000002", "Petrova", "Tatiana", "Sergeevna", "1234 567891", "OVD SPB", date(2016, 6, 11), "770-002", date(1991, 2, 2), 1),
            ("sd1@example.com", "+70000000005", "Sidorov", "Dmitry", "", "1234 567892", "OVD Kazan", date(2017, 7, 12), "770-003", date(1988, 3, 3), 2),
            ("sm1@example.com", "+70000000006", "Smirnov", "Maxim", "Olegovich", "1234 567893", "OVD Novosibirsk", date(2014, 4, 13), "770-004", date(1992, 4, 4), 3),
            ("kr1@example.com", "+70000000007", "Karpov", "Roman", "Igorevich", "1234 567894", "OVD Ekaterinburg", date(2013, 3, 14), "770-005", date(1985, 5, 5), 4),
            ("er1@example.com", "+70000000008", "Ermakova", "Alina", "Vladimirovna", "1234 567895", "OVD NN", date(2012, 2, 15), "770-006", date(1993, 6, 6), 5),
            ("vl1@example.com", "+70000000009", "Volkova", "Lidia", "Petrovna", "1234 567896", "OVD Perm", date(2011, 1, 16), "770-007", date(1994, 7, 7), 6),
            ("ko1@example.com", "+70000000010", "Kolesnik", "Olga", "Nikolaevna", "1234 567897", "OVD Rostov", date(2010, 12, 17), "770-008", date(1995, 8, 8), 7),
            ("mi1@example.com", "+70000000015", "Mishin", "Egor", "Andreevich", "1234 567898", "OVD Sochi", date(2018, 10, 5), "770-009", date(1996, 9, 9), 8),
            ("bo1@example.com", "+70000000016", "Bogdanova", "Maria", "Dmitrievna", "1234 567899", "OVD Omsk", date(2019, 9, 9), "770-010", date(1997, 10, 10), 9),
        ]
        for email, phone, ln, fn, pn, passport, issued_by, issued_date, code, bdate, addr_idx in ind_seed:
            c, _ = rm.Client.objects.get_or_create(email=email, defaults={"phone_number": phone, "type": "individual"})
            rm.IndClient.objects.get_or_create(
                client=c,
                defaults={
                    "last_name": ln,
                    "first_name": fn,
                    "patronymic": pn or None,
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

        # Company clients (10)
        comp_seed = [
            ("comp1@example.com", "+70000000003", "StroyInvest", 10, "7701234567", "770101001", "1207700000000"),
            ("comp2@example.com", "+70000000004", "MostGroup", 11, "7801234567", "780101001", "1207800000000"),
            ("comp3@example.com", "+70000000011", "RoadBuild", 12, "5401234567", "540101001", "1205400000000"),
            ("comp4@example.com", "+70000000012", "TechRent", 13, "3601234567", "360101001", "1203600000000"),
            ("comp5@example.com", "+70000000013", "LogiTrans", 6, "5201234567", "520101001", "1205200000000"),
            ("comp6@example.com", "+70000000014", "CityWorks", 7, "6101234567", "610101001", "1206100000000"),
            ("comp7@example.com", "+70000000017", "BridgeLine", 8, "8601234567", "860101001", "1208600000000"),
            ("comp8@example.com", "+70000000018", "NorthDrill", 9, "5402234567", "540201001", "1205402000000"),
            ("comp9@example.com", "+70000000019", "SouthEnergy", 2, "2301234567", "230101001", "1202300000000"),
            ("comp10@example.com", "+70000000020", "UralMining", 4, "7401234567", "740101001", "1207400000000"),
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
                    "bank_name": "Demo Bank",
                    "bank_bik": "044525000",
                    "bank_account": "40702810900000000001",
                    "bank_corr": "30101810400000000001",
                    "director_first_name": "Sergey",
                    "director_last_name": "Smirnov",
                    "director_patronymic": "Ivanovich",
                    "position": "CEO",
                },
            )
            clients.append(c)

        # Countries, brands, models
        countries = [rm.EquipmentCountries.objects.get_or_create(country=n)[0] for n in ["Russia", "Japan", "Sweden", "Germany", "USA", "UK"]]
        brands = [rm.EquipmentBrands.objects.get_or_create(brand=n)[0] for n in ["Caterpillar", "Komatsu", "Volvo", "Hitachi", "Liebherr", "JCB"]]
        models = [
            rm.EquipmentModels.objects.get_or_create(model_name=n)[0]
            for n in ["Bulldozer", "Dump Truck", "Wheel Loader", "Excavator", "Mobile Crane", "Road Roller", "Grader"]
        ]

        # Equipment (15)
        equipments = []
        equipment_seed = [
            ("Bulldozer CAT D6K2", models[0], countries[0], brands[0], 150.0, 12000, "diesel", 15000),
            ("Dump Truck Volvo A40F", models[1], countries[2], brands[2], 320.0, 19000, "diesel", 22000),
            ("Wheel Loader Komatsu L90H", models[2], countries[1], brands[1], 110.0, 9500, "diesel", 18000),
            ("Excavator Hitachi ZX200", models[3], countries[3], brands[3], 170.0, 20000, "diesel", 21000),
            ("Mobile Crane Liebherr LTM 1050", models[4], countries[4], brands[4], 250.0, 25000, "diesel", 30000),
            ("Road Roller Caterpillar CS56", models[5], countries[0], brands[0], 140.0, 15000, "diesel", 17000),
            ("Bulldozer Komatsu D65", models[0], countries[1], brands[1], 180.0, 18000, "diesel", 20000),
            ("Wheel Loader Volvo L120H", models[2], countries[2], brands[2], 160.0, 16000, "diesel", 19500),
            ("Excavator Hitachi ZX350", models[3], countries[3], brands[3], 240.0, 32000, "diesel", 28000),
            ("Mobile Crane Liebherr LTM 1060", models[4], countries[4], brands[4], 300.0, 32000, "diesel", 34000),
            ("Dump Truck CAT 770", models[1], countries[0], brands[0], 370.0, 40000, "diesel", 36000),
            ("Road Roller Volvo SD115", models[5], countries[2], brands[2], 130.0, 14000, "diesel", 16500),
            ("Grader JCB 220", models[6], countries[5], brands[5], 145.0, 16000, "diesel", 18500),
            ("Bulldozer CAT D7R", models[0], countries[0], brands[0], 210.0, 24000, "diesel", 26000),
            ("Excavator Komatsu PC210", models[3], countries[1], brands[1], 200.0, 23000, "diesel", 24500),
        ]
        for name, model_obj, country, brand, power, weight, fuel, price in equipment_seed:
            code = rm.Equipment.generate_equipment_code(brand, model_obj)
            eq, _ = rm.Equipment.objects.get_or_create(
                equipment_code=code,
                defaults={
                    "equipment_name": name,
                    "description": f"{name} demo unit",
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

        # Maintenance types
        mtypes = [
            rm.MaintenanceType.objects.get_or_create(type_name=n)[0]
            for n in ["TO-500h", "Engine service", "Hydraulics check", "Seasonal inspection"]
        ]

        # Maintenance (12)
        maint_seed = [
            (timezone.now() + timedelta(days=1), mtypes[0], equipments[0], "Scheduled TO after 500h", "planned"),
            (timezone.now() + timedelta(days=2), mtypes[1], equipments[1], "Engine service before rent", "in_progress"),
            (timezone.now() - timedelta(days=1), mtypes[2], equipments[2], "Hydraulics check after heavy load", "completed"),
            (timezone.now() + timedelta(days=3), mtypes[3], equipments[3], "Seasonal inspection", "planned"),
            (timezone.now() - timedelta(days=2), mtypes[1], equipments[4], "Engine service completed", "completed"),
            (timezone.now() + timedelta(days=5), mtypes[0], equipments[5], "Routine TO", "planned"),
            (timezone.now() - timedelta(days=5), mtypes[3], equipments[6], "Winter prep completed", "completed"),
            (timezone.now() - timedelta(days=3), mtypes[2], equipments[7], "Hydraulics fix", "completed"),
            (timezone.now() + timedelta(days=7), mtypes[1], equipments[8], "Engine service upcoming", "planned"),
            (timezone.now() - timedelta(days=7), mtypes[0], equipments[9], "TO after rent", "completed"),
            (timezone.now() - timedelta(days=4), mtypes[3], equipments[10], "Seasonal inspection finished", "completed"),
            (timezone.now() + timedelta(days=9), mtypes[2], equipments[11], "Hydraulics scheduled", "planned"),
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

        # Rents (15 scenarios)
        rent_seed = [
            # 1 Active, two machines, unpaid
            (clients[0], equipments[0:2], date.today() - timedelta(days=5), date.today() + timedelta(days=2), None, "active", False),
            # 2 Completed and paid
            (clients[1], equipments[2:3], date.today() - timedelta(days=15), date.today() - timedelta(days=10), date.today() - timedelta(days=9), "completed", True),
            # 3 Active with potential delay
            (clients[2], equipments[3:4], date.today() - timedelta(days=12), date.today() - timedelta(days=2), None, "active", False),
            # 4 Completed, unpaid (debt)
            (clients[3], equipments[4:5], date.today() - timedelta(days=20), date.today() - timedelta(days=15), date.today() - timedelta(days=14), "completed", False),
            # 5 Active long term, prepaid
            (clients[4], equipments[5:6], date.today() - timedelta(days=3), date.today() + timedelta(days=10), None, "active", True),
            # 6 Completed multi-equip, paid
            (clients[5], equipments[6:8], date.today() - timedelta(days=25), date.today() - timedelta(days=20), date.today() - timedelta(days=19), "completed", True),
            # 7 Active multi-equip, unpaid
            (clients[6], equipments[8:10], date.today() - timedelta(days=2), date.today() + timedelta(days=5), None, "active", False),
            # 8 Extended rent
            (clients[7], equipments[10:11], date.today() - timedelta(days=8), date.today() + timedelta(days=6), None, "extended", True),
            # 9 Completed old, paid
            (clients[8], equipments[1:2], date.today() - timedelta(days=40), date.today() - timedelta(days=35), date.today() - timedelta(days=34), "completed", True),
            # 10 Active, overdue (planned date passed)
            (clients[9], equipments[9:10], date.today() - timedelta(days=18), date.today() - timedelta(days=8), None, "active", False),
            # 11 Completed large set
            (clients[10], equipments[0:3], date.today() - timedelta(days=22), date.today() - timedelta(days=12), date.today() - timedelta(days=11), "completed", False),
            # 12 Active, prepaid, two items
            (clients[11], equipments[7:9], date.today() - timedelta(days=1), date.today() + timedelta(days=7), None, "active", True),
            # 13 Active, single, unpaid short
            (clients[12], equipments[11:12], date.today() - timedelta(days=4), date.today() + timedelta(days=1), None, "active", False),
            # 14 Completed with late return (actual later than planned)
            (clients[13], equipments[12:13], date.today() - timedelta(days=14), date.today() - timedelta(days=7), date.today() - timedelta(days=5), "completed", False),
            # 15 Extended, prepaid large equipment
            (clients[14], equipments[13:15], date.today() - timedelta(days=6), date.today() + timedelta(days=12), None, "extended", True),
        ]

        for client, eq_list, start, planned_end, actual_end, status, paid in rent_seed:
            if not eq_list:
                continue
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
                rm.RentItems.objects.get_or_create(rent=rent, equipment=eq)
                eq.status = "available" if status == "completed" else "rented"
                eq.save(update_fields=["status"])

        self.stdout.write(self.style.SUCCESS("Demo data (15+ rows) has been created."))
