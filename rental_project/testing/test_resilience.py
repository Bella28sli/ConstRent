# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command, CommandError
from django.db import transaction
from django.test import TestCase

from rental_system import models as rm


class BackupResilienceTests(TestCase):
    def test_backup_fails_when_pg_dump_missing(self):
        """Имитация отсутствия pg_dump: команда должна упасть с CommandError, а не с 500."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("pg_dump")):
            with self.assertRaises(CommandError):
                call_command("backup_db", output_dir=tempfile.gettempdir(), file_prefix="testdb", keep=1)

    def test_backup_creates_file_on_success(self):
        """Успешный бэкап: файл появляется в каталоге резервов (subprocess.run замокан)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            created_files = []

            def fake_run(cmd, check, env=None):
                # Ищем путь после флага -f и создаём пустой файл
                if "-f" in cmd:
                    outfile = cmd[cmd.index("-f") + 1]
                    Path(outfile).touch()
                    created_files.append(outfile)
                return mock.Mock(returncode=0)

            with mock.patch("subprocess.run", side_effect=fake_run):
                call_command("backup_db", output_dir=tmpdir, file_prefix="testdb", keep=3)

            self.assertTrue(created_files, "Бэкап не создал файл")
            for path in created_files:
                self.assertTrue(Path(path).exists(), f"Файл бэкапа не найден: {path}")


class TransactionRollbackTests(TestCase):
    def test_atomic_rollback_on_error(self):
        """Проверяем, что транзакция откатывается при ошибке."""
        before = rm.Equipment.objects.count()
        try:
            with transaction.atomic():
                country, _ = rm.EquipmentCountries.objects.get_or_create(country="Россия")
                brand, _ = rm.EquipmentBrands.objects.get_or_create(brand="TEST")
                model, _ = rm.EquipmentModels.objects.get_or_create(model_name="RESIL")
                rm.Equipment.objects.create(
                    equipment_name="Rollback test",
                    equipment_code="RES-ROLL-0001",
                    description="",
                    model=model,
                    country=country,
                    brand=brand,
                    power=100,
                    weight=200,
                    fuel_type="diesel",
                    rental_price_day=1000,
                    status="available",
                )
                # Имитируем сбой сервиса/БД
                raise RuntimeError("Simulated failure")
        except RuntimeError:
            pass

        after = rm.Equipment.objects.count()
        self.assertEqual(before, after, "Объект не должен сохраниться после отката транзакции")
