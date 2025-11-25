# ConstRent

## План работ (недели)
1. Постановка задач: тема, документ ПЗ, список сущностей и атрибутов, черновик словаря данных, каркас репо + README.  
2. Логическое проектирование: ERD, инфо/дата-модель, таблица ограничений, первая миграция.  
3. Физическая БД и базовая серверная логика (CRUD, вью): тестовые данные, схемы/архитектура в доках.  
4. Серверная логика (процедуры>3, триггеры, транзакции): финализация ПЗ, SQL-пакет + коды ошибок.  
5. Безопасность/администрирование: роли, проверка прав, хэш паролей, маски, логирование, бэкап/восстановление и регламент.  
6. Клиент, API, интеграция: схема интерфейса, гайд по запуску клиента, рабочее приложение и API.  
7. Аналитика и тестирование: статистика/отчёты, функциональные/интеграционные/нагрузочные/отказоустойчивые/модульные тесты.  
8. Завершение: документация, Docker, презентация.

## Запуск локально
1) Установить зависимости в venv: `pip install -r requirements.txt` (или `pip install django djangorestframework psycopg2-binary`).  
2) Экспортировать переменные окружения (пример, замените своими):
```
set DJANGO_SECRET_KEY=dev-secret
set DJANGO_DEBUG=True
set DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
set DB_ENGINE=django.db.backends.postgresql
set DB_NAME=rental_system_db
set DB_USER=postgres
set DB_PASSWORD=yourpass
set DB_HOST=localhost
set DB_PORT=5432
```
3) `python manage.py migrate`  
4) (Опционально) `python manage.py setup_groups` (группы/права), `python manage.py seed_users` (базовые пользователи), `python manage.py seed_demo_data` (демо-данные).  
5) `python manage.py createsuperuser`  
6) `python manage.py runserver` → http://localhost:8000/

## Запуск в контейнерах
- Добавить docker-compose (web + db) и `.env` с переменными.  
- `docker-compose build`, `docker-compose up`, затем `docker-compose exec web python manage.py migrate` (и при необходимости `seed_demo_data`).

## Архитектура (кратко)
- Backend: Django + DRF, PostgreSQL.  
- Модели: Role, встроенный User, Address, Client/IndClient/CompClient, Equipment (+справочники), Maintenance(+Type), Rent, RentItems, UserPreference, Log.  
- API: ViewSet’ы, OpenAPI схема по `/api/schema/`.  
- Бэкап: `python manage.py backup_db`, скачивание `/admin/backups/<filename>/`.  
- Импорт/экспорт: `export_csv`/`import_csv`, SQL-дампы через `backup_db`/`pg_restore`.

## Роли и доступы
- Администратор: полный доступ, вход в админку.  
- Руководитель: только чтение всех данных.  
- Менеджер: редактирует оборудование, аренды, клиентов/адреса; остальное читает.  
- Техник: редактирует только обслуживание; остальное читает.  
- Чувствительные данные (паспорт/банковские реквизиты) в API маскируются для всех, кроме админов и менеджеров.

## Полезные команды
- `python manage.py setup_groups` — создать группы и права.  
- `python manage.py seed_users` — пользователи leader/tech/manager.  
- `python manage.py seed_demo_data` — демо-наполнение.  
- `python manage.py backup_db --output-dir backups` — дамп БД.  
- `python manage.py export_csv rental_system.Client --output clients.csv`  
- `python manage.py import_csv rental_system.Client --input clients.csv --pk-field id`
