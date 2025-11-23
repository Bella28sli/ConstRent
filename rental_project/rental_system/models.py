from django.conf import settings
from django.db import connection, models

from rental_system.services import RentalService


# ---------- Roles ----------
class Role(models.Model):
    role_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.role_name


# ---------- Address ----------
class Address(models.Model):
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    house = models.CharField(max_length=20)
    building = models.CharField(max_length=20, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    full_address = models.CharField(max_length=255)

    def __str__(self):
        return self.full_address


# ---------- Logs ----------
class Log(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = "LOGIN", "Вход в систему"
        LOGOUT = "LOGOUT", "Выход из системы"
        CREATE = "CREATE", "Создание объекта"
        UPDATE = "UPDATE", "Обновление объекта"
        DELETE = "DELETE", "Удаление объекта"
        VIEW = "VIEW", "Просмотр объекта"
        EXPORT = "EXPORT", "Экспорт данных"
        IMPORT = "IMPORT", "Импорт данных"
        ASSIGN = "ASSIGN", "Назначение/переназначение"
        CHANGE_STATUS = "CHANGE_STATUS", "Изменение статуса"
        UPLOAD = "UPLOAD", "Загрузка файла"
        DOWNLOAD = "DOWNLOAD", "Скачивание файла"
        LOGIN_FAILED = "LOGIN_FAILED", "Неудачная попытка входа"
        PERMISSION_CHANGE = "PERMISSION_CHANGE", "Изменение прав доступа"
        OTHER = "OTHER", "Другое действие"

    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    log_date = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(
        max_length=100,
        choices=ActionType.choices,
        default=ActionType.OTHER
    )
    success_status = models.BooleanField(default=True)
    description_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.action_type} - {self.staff}"




# ---------- Clients ----------
class Client(models.Model):
    TYPE_CHOICES = [
        ('individual', 'Физическое лицо'),
        ('company', 'Юридическое лицо'),
    ]

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    @property
    def rental_history(self):
        return RentalService.get_client_rental_history(self.id)
        
    def __str__(self):
        return self.email
    


# ---------- Individual Clients ----------
class IndClient(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, primary_key=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    passport_number = models.CharField(max_length=20, unique=True)
    passport_issued_by = models.CharField(max_length=200)
    passport_issued_date = models.DateField()
    passport_code = models.CharField(max_length=20)
    birth_date = models.DateField()
    registration_address = models.ForeignKey(Address, related_name='registered_clients', on_delete=models.SET_NULL, null=True)
    actual_address = models.ForeignKey(Address, related_name='actual_clients', on_delete=models.SET_NULL, null=True)
    inn = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


# ---------- Company Clients ----------
class CompClient(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, primary_key=True)
    company_name = models.CharField(max_length=200)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    inn = models.CharField(max_length=20)
    kpp = models.CharField(max_length=20)
    ogrn = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100)
    bank_bik = models.CharField(max_length=20)
    bank_account = models.CharField(max_length=50)
    bank_corr = models.CharField(max_length=50)
    director_first_name = models.CharField(max_length=100)
    director_last_name = models.CharField(max_length=100)
    director_patronymic = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100)
    attorney_number = models.CharField(max_length=50, blank=True, null=True)
    attorney_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.company_name


# ---------- Equipment ----------
class EquipmentCountries(models.Model):
    country = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.country


class EquipmentBrands(models.Model):
    brand = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.brand


class EquipmentModels(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.model_name


class Equipment(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступно'),
        ('rented', 'В аренде'),
        ('maintenance', 'На обслуживании'),
    ]
    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('electric', 'Электричество'),
        ('hybrid', 'Гибрид'),
        ('gas', 'Газ'),
        ('other', 'Другое'),
    ]


    equipment_name = models.CharField(max_length=200)
    equipment_code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    model = models.ForeignKey(EquipmentModels, on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey(EquipmentCountries, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(EquipmentBrands, on_delete=models.SET_NULL, null=True)
    power = models.DecimalField(max_digits=8, decimal_places=2)
    weight = models.DecimalField(max_digits=8, decimal_places=2)
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='petrol')
    rental_price_day = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)

    def __str__(self):
        return self.equipment_name


# ---------- Maintenance ----------
class MaintenanceType(models.Model):
    type_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.type_name
    
class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('in_progress', 'Проводится'),
        ('completed', 'Завершено'),
    ]

    maintenance_date = models.DateTimeField()
    work_type = models.ForeignKey(MaintenanceType, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.equipment} — {self.get_status_display()} ({self.maintenance_date.strftime('%Y-%m-%d')})"



# ---------- Rent ----------
class Rent(models.Model):
    RENT_STATUS_CHOICES = [
        ('active', 'Активен'),
        ('completed', 'Завершен'),
        ('extended', 'Продлен'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Перевод'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rent_agreement_number = models.CharField(max_length=50)
    rent_agreement_date = models.DateField()
    start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_end_date = models.DateField(blank=True, null=True)
    rent_status = models.CharField(max_length=20, choices=RENT_STATUS_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    transaction_number = models.CharField(max_length=50, blank=True, null=True)

    @classmethod
    def generate_agreement_number(cls):
        with connection.cursor() as cursor:
            cursor.execute("SELECT generate_agreement_number()")
            return cursor.fetchone()[0]
    
    @property
    def late_fee(self):
        return RentalService.calculate_late_fee(self.id)
        
    def __str__(self):
        return f"Договор #{self.rent_agreement_number}"


# ---------- Rent Items ----------
class RentItems(models.Model):
    rent = models.ForeignKey(Rent, on_delete=models.CASCADE)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('rent', 'equipment')

    def __str__(self):
        return f"{self.rent} - {self.equipment}"


# ---------- User preferences ----------
class UserPreference(models.Model):
    class Theme(models.TextChoices):
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"
        SYSTEM = "system", "System"

    class DateFormat(models.TextChoices):
        YMD = "YYYY-MM-DD", "YYYY-MM-DD"
        DMY = "DD.MM.YYYY", "DD.MM.YYYY"
        MDY = "MM/DD/YYYY", "MM/DD/YYYY"

    class NumberFormat(models.TextChoices):
        SPACE = "space", "1 234 567.89"
        COMMA = "comma", "1,234,567.89"
        DOT = "dot", "1.234.567,89"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    theme = models.CharField(
        max_length=20,
        choices=Theme.choices,
        default=Theme.SYSTEM,
    )
    date_format = models.CharField(
        max_length=20,
        choices=DateFormat.choices,
        default=DateFormat.DMY,
    )
    number_format = models.CharField(
        max_length=20,
        choices=NumberFormat.choices,
        default=NumberFormat.SPACE,
    )
    page_size = models.PositiveIntegerField(default=50)
    saved_filters = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user}"
