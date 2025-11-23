from django.shortcuts import render
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rental_system.models import *
from .serializers import RoleSerializer, AddressSerializer, StaffSerializer, LogSerializer, ClientSerializer, IndClientSerializer, CompClientSerializer, EquipmentBrandsSerializer, EquipmentCountriesSerializer, EquipmentModelsSerializer, EquipmentSerializer, MaintenanceTypeSerializer, MaintenanceSerializer, RentItemsSerializer, RentSerializer, UserPreferenceSerializer
from .permissions import (
    IsAdminOrReadOnly,
    AdminOnly,
    AdminOrManagersWrite,
    AdminOrTechniciansWrite,
    AdminOnlyWrite,
)
from .theme import THEME_PALETTES

User = get_user_model()

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, AdminOnly]
    schema_tags = ["Roles"]
    schema_description = "Управление ролями персонала."
    schema_component_name = "Role"

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Addresses"]
    schema_description = "Адреса для клиентов (регистрации/проживания/юридические)."
    schema_component_name = "Address"

class StaffViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    schema_tags = ["Staff"]
    schema_description = "Пользователи (учетные записи)."
    schema_component_name = "Staff"

class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.select_related('staff')
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated, AdminOnly]
    schema_tags = ["Logs"]
    schema_description = "Аудит действий пользователей."
    schema_component_name = "Log"

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Clients"]
    schema_description = "Клиенты (физические/юридические)."
    schema_component_name = "Client"

class IndClientViewSet(viewsets.ModelViewSet):
    queryset = IndClient.objects.select_related('client', 'registration_address', 'actual_address')
    serializer_class = IndClientSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Clients"]
    schema_description = "Детали физических лиц."
    schema_component_name = "IndividualClient"

class CompClientViewSet(viewsets.ModelViewSet):
    queryset = CompClient.objects.select_related('client', 'address')
    serializer_class = CompClientSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Clients"]
    schema_description = "Детали юридических лиц."
    schema_component_name = "CompanyClient"

class EquipmentCountriesViewSet(viewsets.ModelViewSet):
    queryset = EquipmentCountries.objects.all()
    serializer_class = EquipmentCountriesSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Equipment Dictionaries"]
    schema_description = "Страны производители оборудования."
    schema_component_name = "EquipmentCountry"

class EquipmentBrandsViewSet(viewsets.ModelViewSet):
    queryset = EquipmentBrands.objects.all()
    serializer_class = EquipmentBrandsSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Equipment Dictionaries"]
    schema_description = "Бренды оборудования."
    schema_component_name = "EquipmentBrand"

class EquipmentModelsViewSet(viewsets.ModelViewSet):
    queryset = EquipmentModels.objects.all()
    serializer_class = EquipmentModelsSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Equipment Dictionaries"]
    schema_description = "Модели оборудования."
    schema_component_name = "EquipmentModel"

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.select_related('model', 'country', 'brand')
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Equipment"]
    schema_description = "Оборудование, его характеристики и статус."
    schema_component_name = "Equipment"

class MaintenanceTypeViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceType.objects.all()
    serializer_class = MaintenanceTypeSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Maintenance"]
    schema_description = "Справочник типов обслуживания."
    schema_component_name = "MaintenanceType"

class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related('work_type', 'staff', 'equipment')
    serializer_class = MaintenanceSerializer
    permission_classes = [IsAuthenticated, AdminOrTechniciansWrite]
    schema_tags = ["Maintenance"]
    schema_description = "Работы по обслуживанию оборудования."
    schema_component_name = "Maintenance"

class RentViewSet(viewsets.ModelViewSet):
    queryset = Rent.objects.select_related('client', 'staff')
    serializer_class = RentSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Rent"]
    schema_description = "Арендные договоры и их статусы."
    schema_component_name = "Rent"

class RentItemsViewSet(viewsets.ModelViewSet):
    queryset = RentItems.objects.select_related('rent', 'equipment')
    serializer_class = RentItemsSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Rent"]
    schema_description = "Связи аренды и оборудования."
    schema_component_name = "RentItem"


class UserPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsAuthenticated]
    schema_tags = ["User preferences"]
    schema_description = "Настройки пользователя (тема, форматы, размер страницы, сохраненные фильтры)."
    schema_component_name = "UserPreference"

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


class ThemePaletteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Возвращает доступные палитры тем, чтобы фронтенд не хардкодил цвета.
        """
        return Response(THEME_PALETTES)
