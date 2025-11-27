FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=rental_project.settings

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Статик (если нужен): python manage.py collectstatic --noinput
CMD ["gunicorn", "rental_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1"]
