from rest_framework import serializers
from rental_system.models import *

# ---------- Базовые ----------
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


# ---------- Сотрудники ----------
class StaffSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = Staff
        fields = '__all__'


# ---------- Логи ----------
class LogSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)

    class Meta:
        model = Log
        fields = '__all__'


# ---------- Клиенты ----------
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class IndClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndClient
        fields = '__all__'


class CompClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompClient
        fields = '__all__'


# ---------- Оборудование ----------
class EquipmentCountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCountries
        fields = '__all__'


class EquipmentBrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrands
        fields = '__all__'


class EquipmentModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentModels
        fields = '__all__'


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'


# ---------- Обслуживание ----------
class MaintenanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceType
        fields = '__all__'


class MaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maintenance
        fields = '__all__'


# ---------- Аренда ----------
class RentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rent
        fields = '__all__'


class RentItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentItems
        fields = '__all__'
