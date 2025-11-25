from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rental_system import models as rm


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = rm.UserPreference
        fields = ["theme", "date_format", "number_format", "page_size"]
        widgets = {
            "theme": forms.Select(attrs={"class": "form-select"}),
            "date_format": forms.Select(attrs={"class": "form-select"}),
            "number_format": forms.Select(attrs={"class": "form-select"}),
            "page_size": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }
        labels = {
            "theme": "Тема",
            "date_format": "Формат даты",
            "number_format": "Формат чисел",
            "page_size": "Размер страницы",
        }


class EquipmentCountryForm(forms.ModelForm):
    class Meta:
        model = rm.EquipmentCountries
        fields = ["country"]
        widgets = {"country": forms.TextInput(attrs={"class": "form-control"})}
        labels = {"country": "Страна-производитель"}


class EquipmentBrandForm(forms.ModelForm):
    class Meta:
        model = rm.EquipmentBrands
        fields = ["brand"]
        widgets = {"brand": forms.TextInput(attrs={"class": "form-control"})}
        labels = {"brand": "Бренд"}


class EquipmentModelForm(forms.ModelForm):
    class Meta:
        model = rm.EquipmentModels
        fields = ["model_name"]
        widgets = {"model_name": forms.TextInput(attrs={"class": "form-control"})}
        labels = {"model_name": "Модель"}


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = rm.Equipment
        fields = [
            "equipment_name",
            "equipment_code",
            "description",
            "model",
            "country",
            "brand",
            "power",
            "weight",
            "fuel_type",
            "rental_price_day",
            "status",
            "image",
        ]
        widgets = {
            "equipment_name": forms.TextInput(attrs={"class": "form-control"}),
            "equipment_code": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "model": forms.Select(attrs={"class": "form-select"}),
            "country": forms.Select(attrs={"class": "form-select"}),
            "brand": forms.Select(attrs={"class": "form-select"}),
            "power": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "fuel_type": forms.Select(attrs={"class": "form-select"}),
            "rental_price_day": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        labels = {
            "equipment_name": "Название",
            "equipment_code": "Код",
            "description": "Описание",
            "model": "Модель",
            "country": "Страна",
            "brand": "Бренд",
            "power": "Мощность",
            "weight": "Вес",
            "fuel_type": "Тип топлива",
            "rental_price_day": "Цена аренды/день",
            "status": "Статус",
            "image": "Изображение",
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = rm.Client
        fields = ["email", "phone_number", "type"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7..."}),
            "type": forms.Select(attrs={"class": "form-select", "id": "client-type-select"}),
        }
        labels = {
            "email": "Email",
            "phone_number": "Телефон",
            "type": "Тип клиента",
        }


class IndividualClientForm(forms.ModelForm):
    class Meta:
        model = rm.IndClient
        exclude = ["client"]
        widgets = {
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "patronymic": forms.TextInput(attrs={"class": "form-control"}),
            "passport_number": forms.TextInput(attrs={"class": "form-control"}),
            "passport_issued_by": forms.TextInput(attrs={"class": "form-control"}),
            "passport_issued_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "passport_code": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "registration_address": forms.Select(attrs={"class": "form-select"}),
            "actual_address": forms.Select(attrs={"class": "form-select"}),
            "inn": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "last_name": "Фамилия",
            "first_name": "Имя",
            "patronymic": "Отчество",
            "passport_number": "Паспорт",
            "passport_issued_by": "Кем выдан",
            "passport_issued_date": "Дата выдачи",
            "passport_code": "Код подразделения",
            "birth_date": "Дата рождения",
            "registration_address": "Адрес регистрации",
            "actual_address": "Фактический адрес",
            "inn": "ИНН",
        }


class CompanyClientForm(forms.ModelForm):
    class Meta:
        model = rm.CompClient
        exclude = ["client"]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Select(attrs={"class": "form-select"}),
            "inn": forms.TextInput(attrs={"class": "form-control"}),
            "kpp": forms.TextInput(attrs={"class": "form-control"}),
            "ogrn": forms.TextInput(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "bank_bik": forms.TextInput(attrs={"class": "form-control"}),
            "bank_account": forms.TextInput(attrs={"class": "form-control"}),
            "bank_corr": forms.TextInput(attrs={"class": "form-control"}),
            "director_first_name": forms.TextInput(attrs={"class": "form-control"}),
            "director_last_name": forms.TextInput(attrs={"class": "form-control"}),
            "director_patronymic": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "attorney_number": forms.TextInput(attrs={"class": "form-control"}),
            "attorney_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        labels = {
            "company_name": "Компания",
            "address": "Адрес",
            "inn": "ИНН",
            "kpp": "КПП",
            "ogrn": "ОГРН",
            "bank_name": "Банк",
            "bank_bik": "БИК",
            "bank_account": "Расчетный счет",
            "bank_corr": "Корр. счет",
            "director_first_name": "Имя директора",
            "director_last_name": "Фамилия директора",
            "director_patronymic": "Отчество директора",
            "position": "Должность",
            "attorney_number": "Доверенность №",
            "attorney_date": "Дата доверенности",
        }


# ---------- Users ----------
User = get_user_model()


class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Оставьте пустым, если не меняете пароль",
        label="Пароль",
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=False,
        label="Группа (роль)",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="admin / leader / manager / technician",
    )

    class Meta:
        model = User
        fields = ["username", "email", "is_staff", "is_active", "group"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "username": "Логин",
            "email": "Email",
            "is_staff": "Доступ в админку",
            "is_active": "Активен",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = ["admin", "leader", "manager", "technician"]
        qs = Group.objects.filter(name__in=allowed)
        self.fields["group"].queryset = qs if qs.exists() else Group.objects.all()
        instance = kwargs.get("instance")
        if instance:
            current = instance.groups.filter(name__in=allowed).first() or instance.groups.first()
            if current:
                self.fields["group"].initial = current


# ---------- Addresses ----------
class AddressForm(forms.ModelForm):
    class Meta:
        model = rm.Address
        fields = [
            "region",
            "city",
            "street",
            "house",
            "building",
            "postal_code",
            "full_address",
        ]
        widgets = {
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "street": forms.TextInput(attrs={"class": "form-control"}),
            "house": forms.TextInput(attrs={"class": "form-control"}),
            "building": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "full_address": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "region": "Регион",
            "city": "Город",
            "street": "Улица",
            "house": "Дом",
            "building": "Корпус/строение",
            "postal_code": "Индекс",
            "full_address": "Полный адрес",
        }
