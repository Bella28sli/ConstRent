import csv
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Экспортирует данные модели в CSV. Пример: python manage.py export_csv rental_system.Client --output clients.csv"

    def add_arguments(self, parser):
        parser.add_argument("model", help="Модель в виде app_label.ModelName, например rental_system.Client")
        parser.add_argument("--output", required=True, help="Путь к CSV-файлу для сохранения")
        parser.add_argument("--fields", nargs="+", help="Список полей для экспорта (по умолчанию все полевые атрибуты)")

    def handle(self, *args, **options):
        model_label = options["model"]
        output_path = Path(options["output"])
        fields = options.get("fields")

        try:
            app_label, model_name = model_label.split(".")
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as exc:
            raise CommandError(f"Неверная модель: {model_label}") from exc

        qs = model.objects.all()
        if not fields:
            fields = [f.name for f in model._meta.fields]

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for obj in qs.iterator():
                row = {}
                for field in fields:
                    row[field] = getattr(obj, field, "")
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS(f"Экспортировано {qs.count()} записей в {output_path}"))
