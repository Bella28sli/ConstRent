from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404


BACKUP_DIR = Path(getattr(settings, "BACKUP_DIR", settings.BASE_DIR / "backups"))


@staff_member_required
def download_backup(request, filename: str):
    """
    Отдает файл бэкапа только для staff/admin. Простая валидация имени предотвращает обход каталога.
    """
    if ".." in filename or filename.startswith("."):
        raise Http404()

    path = BACKUP_DIR / filename
    if not path.exists() or not path.is_file():
        raise Http404("Файл не найден")

    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)
