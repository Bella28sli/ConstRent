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
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

User = get_user_model()

@extend_schema_view(
    list=extend_schema(description="Список ролей"),
    retrieve=extend_schema(description="Получить роль"),
    create=extend_schema(description="Создать роль"),
    update=extend_schema(description="Обновить роль"),
    partial_update=extend_schema(description="Частично обновить роль"),
    destroy=extend_schema(description="Удалить роль"),
)
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, AdminOnly]
    schema_tags = ["Roles"]
    schema_description = "Управление ролями персонала."
    schema_component_name = "Role"

@extend_schema_view(
    list=extend_schema(description="Список адресов"),
    retrieve=extend_schema(description="Получить адрес"),
    create=extend_schema(description="Создать адрес"),
    update=extend_schema(description="Обновить адрес"),
    partial_update=extend_schema(description="Частично обновить адрес"),
    destroy=extend_schema(description="Удалить адрес"),
)
class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Addresses"]
    schema_description = "Адреса для клиентов (регистрации/проживания/юридические)."
    schema_component_name = "Address"

@extend_schema_view(
    list=extend_schema(description="Список сотрудников"),
    retrieve=extend_schema(description="Получить данные сотрудника"),
    create=extend_schema(description="Создать сотрудника"),
    update=extend_schema(description="Обновить сотрудника"),
    partial_update=extend_schema(description="Частично обновить сотрудника"),
    destroy=extend_schema(description="Удалить сотрудника"),
)
class StaffViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    schema_tags = ["Staff"]
    schema_description = "Пользователи (учетные записи)."
    schema_component_name = "Staff"

@extend_schema_view(
    list=extend_schema(description="Список логов"),
    retrieve=extend_schema(description="Получить запись лога"),
    create=extend_schema(description="Создать запись лога"),
    update=extend_schema(description="Обновить запись лога"),
    partial_update=extend_schema(description="Частично обновить запись лога"),
    destroy=extend_schema(description="Удалить запись лога"),
)
class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.select_related('staff')
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated, AdminOnly]
    schema_tags = ["Logs"]
    schema_description = "Аудит действий пользователей."
    schema_component_name = "Log"

@extend_schema_view(
    list=extend_schema(description="Список клиентов"),
    retrieve=extend_schema(description="Получить клиента"),
    create=extend_schema(description="Создать клиента"),
    update=extend_schema(description="Обновить клиента"),
    partial_update=extend_schema(description="Частично обновить клиента"),
    destroy=extend_schema(description="Удалить клиента"),
)
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Clients"]
    schema_description = "Клиенты (физические/юридические)."
    schema_component_name = "Client"

@extend_schema_view(
    list=extend_schema(description="Список физлиц"),
    retrieve=extend_schema(description="Получить физлицо"),
    create=extend_schema(description="Создать физлицо"),
    update=extend_schema(description="Обновить физлицо"),
    partial_update=extend_schema(description="Частично обновить физлицо"),
    destroy=extend_schema(description="Удалить физлицо"),
)
class IndClientViewSet(viewsets.ModelViewSet):
    queryset = IndClient.objects.select_related('client', 'registration_address', 'actual_address')
    serializer_class = IndClientSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Clients"]
    schema_description = "Детали физических лиц."
    schema_component_name = "IndividualClient"

@extend_schema_view(
    list=extend_schema(description="Список компаний"),
    retrieve=extend_schema(description="Получить компанию"),
    create=extend_schema(description="Создать компанию"),
    update=extend_schema(description="Обновить компанию"),
    partial_update=extend_schema(description="Частично обновить компанию"),
    destroy=extend_schema(description="Удалить компанию"),
)
class CompClientViewSet(viewsets.ModelViewSet):
    queryset = CompClient.objects.select_related('client', 'address')
    serializer_class = CompClientSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Clients"]
    schema_description = "Детали юридических лиц."
    schema_component_name = "CompanyClient"

@extend_schema_view(
    list=extend_schema(description="Список стран производителей техники"),
    retrieve=extend_schema(description="Получить страну производителя"),
    create=extend_schema(description="Создать страну производителя"),
    update=extend_schema(description="Обновить страну производителя"),
    partial_update=extend_schema(description="Частично обновить страну производителя"),
    destroy=extend_schema(description="Удалить страну производителя"),
)
class EquipmentCountriesViewSet(viewsets.ModelViewSet):
    queryset = EquipmentCountries.objects.all()
    serializer_class = EquipmentCountriesSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Equipment Dictionaries"]
    schema_description = "Страны производители оборудования."
    schema_component_name = "EquipmentCountry"

@extend_schema_view(
    list=extend_schema(description="Список брендов техники"),
    retrieve=extend_schema(description="Получить бренд"),
    create=extend_schema(description="Создать бренд"),
    update=extend_schema(description="Обновить бренд"),
    partial_update=extend_schema(description="Частично обновить бренд"),
    destroy=extend_schema(description="Удалить бренд"),
)
class EquipmentBrandsViewSet(viewsets.ModelViewSet):
    queryset = EquipmentBrands.objects.all()
    serializer_class = EquipmentBrandsSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Equipment Dictionaries"]
    schema_description = "Бренды оборудования."
    schema_component_name = "EquipmentBrand"

@extend_schema_view(
    list=extend_schema(description="Список моделей техники"),
    retrieve=extend_schema(description="Получить модель"),
    create=extend_schema(description="Создать модель"),
    update=extend_schema(description="Обновить модель"),
    partial_update=extend_schema(description="Частично обновить модель"),
    destroy=extend_schema(description="Удалить модель"),
)
class EquipmentModelsViewSet(viewsets.ModelViewSet):
    queryset = EquipmentModels.objects.all()
    serializer_class = EquipmentModelsSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Equipment Dictionaries"]
    schema_description = "Модели оборудования."
    schema_component_name = "EquipmentModel"

@extend_schema_view(
    list=extend_schema(description="Список техники"),
    retrieve=extend_schema(description="Получить технику"),
    create=extend_schema(description="Создать технику"),
    update=extend_schema(description="Обновить технику"),
    partial_update=extend_schema(description="Частично обновить технику"),
    destroy=extend_schema(description="Удалить технику"),
)
class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.select_related('model', 'country', 'brand')
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Equipment"]
    schema_description = "Оборудование, его характеристики и статус."
    schema_component_name = "Equipment"

@extend_schema_view(
    list=extend_schema(description="Список типов обслуживания"),
    retrieve=extend_schema(description="Получить тип обслуживания"),
    create=extend_schema(description="Создать тип обслуживания"),
    update=extend_schema(description="Обновить тип обслуживания"),
    partial_update=extend_schema(description="Частично обновить тип обслуживания"),
    destroy=extend_schema(description="Удалить тип обслуживания"),
)
class MaintenanceTypeViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceType.objects.all()
    serializer_class = MaintenanceTypeSerializer
    permission_classes = [IsAuthenticated, AdminOnlyWrite]
    schema_tags = ["Maintenance"]
    schema_description = "Справочник типов обслуживания."
    schema_component_name = "MaintenanceType"

@extend_schema_view(
    list=extend_schema(description="Список заявок на обслуживание"),
    retrieve=extend_schema(description="Получить заявку на обслуживание"),
    create=extend_schema(description="Создать заявку на обслуживание"),
    update=extend_schema(description="Обновить заявку на обслуживание"),
    partial_update=extend_schema(description="Частично обновить заявку на обслуживание"),
    destroy=extend_schema(description="Удалить заявку на обслуживание"),
)
class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.select_related('work_type', 'staff', 'equipment')
    serializer_class = MaintenanceSerializer
    permission_classes = [IsAuthenticated, AdminOrTechniciansWrite]
    schema_tags = ["Maintenance"]
    schema_description = "Работы по обслуживанию оборудования."
    schema_component_name = "Maintenance"

@extend_schema_view(
    list=extend_schema(description="Список договоров аренды"),
    retrieve=extend_schema(description="Получить договор аренды"),
    create=extend_schema(description="Создать договор аренды"),
    update=extend_schema(description="Обновить договор аренды"),
    partial_update=extend_schema(description="Частично обновить договор аренды"),
    destroy=extend_schema(description="Удалить договор аренды"),
)
class RentViewSet(viewsets.ModelViewSet):
    queryset = Rent.objects.select_related('client', 'staff')
    serializer_class = RentSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Rent"]
    schema_description = "Арендные договоры и их статусы."
    schema_component_name = "Rent"

@extend_schema_view(
    list=extend_schema(description="Список техники в арендах"),
    retrieve=extend_schema(description="Получить позицию аренды"),
    create=extend_schema(description="Создать позицию аренды"),
    update=extend_schema(description="Обновить позицию аренды"),
    partial_update=extend_schema(description="Частично обновить позицию аренды"),
    destroy=extend_schema(description="Удалить позицию аренды"),
)
class RentItemsViewSet(viewsets.ModelViewSet):
    queryset = RentItems.objects.select_related('rent', 'equipment')
    serializer_class = RentItemsSerializer
    permission_classes = [IsAuthenticated, AdminOrManagersWrite]
    schema_tags = ["Rent"]
    schema_description = "Связи аренды и оборудования."
    schema_component_name = "RentItem"


@extend_schema_view(
    list=extend_schema(description="Список предпочтений пользователя"),
    retrieve=extend_schema(description="Получить предпочтения пользователя"),
    create=extend_schema(description="Создать предпочтения пользователя"),
    update=extend_schema(description="Обновить предпочтения пользователя"),
    partial_update=extend_schema(description="Частично обновить предпочтения пользователя"),
    destroy=extend_schema(description="Удалить предпочтения пользователя"),
)
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

    @extend_schema(description="Получить доступные палитры тем приложения")
    def get(self, request):
        """
        Возвращает доступные палитры тем, чтобы фронтенд не хардкодил цвета.
        """
        return Response(THEME_PALETTES)
