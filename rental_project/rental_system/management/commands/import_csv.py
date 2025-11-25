import csv
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Импортирует данные модели из CSV. Пример: python manage.py import_csv rental_system.Client --input clients.csv"

    def add_arguments(self, parser):
        parser.add_argument("model", help="Модель в виде app_label.ModelName, например rental_system.Client")
        parser.add_argument("--input", required=True, help="Путь к CSV-файлу для чтения")
        parser.add_argument(
            "--pk-field",
            default="id",
            help="Поле для поиска/обновления. Если указано, при совпадении обновляет, иначе создаёт.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        model_label = options["model"]
        input_path = Path(options["input"])
        pk_field = options["pk_field"]

        if not input_path.exists():
            raise CommandError(f"Файл {input_path} не найден")

        try:
            app_label, model_name = model_label.split(".")
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as exc:
            raise CommandError(f"Неверная модель: {model_label}") from exc

        with input_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if pk_field not in reader.fieldnames:
                raise CommandError(f"В CSV нет столбца {pk_field}")

            created = 0
            updated = 0
            for row in reader:
                lookup = {pk_field: row.get(pk_field) or None}
                data = {k: v for k, v in row.items() if k in [f.name for f in model._meta.fields]}

                obj, exists = model.objects.get_or_create(defaults=data, **lookup)
                if exists:
                    created += 1
                else:
                    for k, v in data.items():
                        setattr(obj, k, v)
                    obj.save()
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Импорт завершен. Создано: {created}, обновлено: {updated}"))
