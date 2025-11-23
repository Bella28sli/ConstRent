from typing import Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers

from rental_system.models import (
    Role,
    Address,
    Log,
    Client,
    IndClient,
    CompClient,
    EquipmentCountries,
    EquipmentBrands,
    EquipmentModels,
    Equipment,
    MaintenanceType,
    Maintenance,
    Rent,
    RentItems,
    UserPreference,
)

User = get_user_model()


def _mask_sensitive(value: Optional[str], visible: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def _is_privileged(user) -> bool:
    # Полный доступ для админов и менеджеров
    return bool(
        user
        and user.is_authenticated
        and (user.is_staff or user.groups.filter(name="Менеджер").exists())
    )


# ---------- Roles ----------
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"


# ---------- Users ----------
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_staff", "is_active"]


# ---------- Logs ----------
class LogSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    staff_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="staff", write_only=True)

    class Meta:
        model = Log
        fields = ["id", "staff", "staff_id", "log_date", "action_type", "success_status", "description_text"]


# ---------- Clients ----------
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class IndClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndClient
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = getattr(self.context.get("request"), "user", None)
        if not _is_privileged(user):
            data["passport_number"] = _mask_sensitive(data.get("passport_number"), visible=2)
            data["passport_issued_by"] = "********"
            data["passport_issued_date"] = None
            data["passport_code"] = _mask_sensitive(data.get("passport_code"), visible=2)
            data["inn"] = _mask_sensitive(data.get("inn"), visible=2)
            data["birth_date"] = None
        return data


class CompClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompClient
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = getattr(self.context.get("request"), "user", None)
        if not _is_privileged(user):
            data["inn"] = _mask_sensitive(data.get("inn"), visible=3)
            data["kpp"] = _mask_sensitive(data.get("kpp"), visible=3)
            data["ogrn"] = _mask_sensitive(data.get("ogrn"), visible=3)
            data["bank_name"] = "********"
            data["bank_bik"] = _mask_sensitive(data.get("bank_bik"), visible=2)
            data["bank_account"] = _mask_sensitive(data.get("bank_account"), visible=4)
            data["bank_corr"] = _mask_sensitive(data.get("bank_corr"), visible=4)
            data["attorney_number"] = _mask_sensitive(data.get("attorney_number"), visible=2)
        return data


# ---------- Equipment dictionaries ----------
class EquipmentCountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCountries
        fields = "__all__"


class EquipmentBrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrands
        fields = "__all__"


class EquipmentModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentModels
        fields = "__all__"


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"


# ---------- Maintenance ----------
class MaintenanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceType
        fields = "__all__"


class MaintenanceSerializer(serializers.ModelSerializer):
    staff_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="staff", write_only=True, allow_null=True, required=False
    )
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(), source="equipment", write_only=True
    )
    work_type_id = serializers.PrimaryKeyRelatedField(
        queryset=MaintenanceType.objects.all(), source="work_type", write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = Maintenance
        fields = [
            "id",
            "maintenance_date",
            "work_type",
            "work_type_id",
            "status",
            "staff",
            "staff_id",
            "equipment",
            "equipment_id",
            "description",
        ]


# ---------- Rent ----------
class RentSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), source="client", write_only=True)
    staff_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="staff", write_only=True)

    class Meta:
        model = Rent
        fields = [
            "id",
            "client",
            "client_id",
            "staff",
            "staff_id",
            "rent_agreement_number",
            "rent_agreement_date",
            "start_date",
            "planned_end_date",
            "actual_end_date",
            "rent_status",
            "total_amount",
            "is_paid",
            "payment_date",
            "payment_method",
            "transaction_number",
        ]


class RentItemsSerializer(serializers.ModelSerializer):
    rent_id = serializers.PrimaryKeyRelatedField(queryset=Rent.objects.all(), source="rent", write_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(queryset=Equipment.objects.all(), source="equipment", write_only=True)

    class Meta:
        model = RentItems
        fields = ["id", "rent", "rent_id", "equipment", "equipment_id"]


# ---------- User preferences ----------
class UserPreferenceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserPreference
        fields = ["id", "user", "theme", "date_format", "number_format", "page_size", "saved_filters", "updated_at"]
        read_only_fields = ["updated_at"]
