import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Создает резервную копию базы PostgreSQL через pg_dump."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            dest="output_dir",
            help="Каталог для сохранения бэкапов (по умолчанию <BASE_DIR>/backups).",
        )
        parser.add_argument(
            "--keep",
            type=int,
            default=5,
            help="Сколько последних файлов оставлять в каталоге. 0 — не удалять старые.",
        )
        parser.add_argument(
            "--file-prefix",
            dest="file_prefix",
            help="Префикс имени файла (по умолчанию имя базы данных).",
        )

    def handle(self, *args, **options):
        db_settings = settings.DATABASES.get("default", {})
        engine = db_settings.get("ENGINE", "")
        if "postgresql" not in engine:
            raise CommandError("Команда поддерживает только PostgreSQL (pg_dump).")

        output_dir = Path(options["output_dir"] or (settings.BASE_DIR / "backups"))
        output_dir.mkdir(parents=True, exist_ok=True)

        file_prefix = options["file_prefix"] or db_settings.get("NAME", "db")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = output_dir / f"{file_prefix}_{timestamp}.dump"

        host = db_settings.get("HOST") or "localhost"
        port = str(db_settings.get("PORT") or "5432")
        user = db_settings.get("USER") or ""
        db_name = db_settings.get("NAME") or ""

        cmd = ["pg_dump", "-h", host, "-p", port, "-F", "c", "-f", str(backup_path)]
        if user:
            cmd.extend(["-U", user])
        cmd.append(db_name)

        env = os.environ.copy()
        if db_settings.get("PASSWORD"):
            env["PGPASSWORD"] = db_settings["PASSWORD"]

        try:
            subprocess.run(cmd, check=True, env=env)
        except FileNotFoundError as exc:
            raise CommandError(
                "Не найден pg_dump. Установите PostgreSQL клиентские утилиты и добавьте их в PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise CommandError(f"pg_dump завершился с ошибкой: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Бэкап создан: {backup_path}"))
        self._cleanup_old_backups(output_dir, file_prefix, options["keep"])

    def _cleanup_old_backups(self, output_dir: Path, prefix: str, keep: int):
        if not keep or keep < 0:
            return

        backups = sorted(
            output_dir.glob(f"{prefix}_*.dump"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for obsolete in backups[keep:]:
            try:
                obsolete.unlink(missing_ok=True)
            except OSError:
                # Если удалить не получилось, просто пропускаем — основной бэкап уже создан.
                continue
