from django.shortcuts import render

from rest_framework import viewsets
from rental_system.models import *
from .serializers import RoleSerializer, AddressSerializer, StaffSerializer, LogSerializer, ClientSerializer, IndClientSerializer, CompClientSerializer, EquipmentBrandsSerializer, EquipmentCountriesSerializer, EquipmentModelsSerializer, EquipmentSerializer, MaintenanceTypeSerializer, MaintenanceSerializer, RentItemsSerializer, RentSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class IndClientViewSet(viewsets.ModelViewSet):
    queryset = IndClient.objects.all()
    serializer_class = IndClientSerializer

class CompClientViewSet(viewsets.ModelViewSet):
    queryset = CompClient.objects.all()
    serializer_class = CompClientSerializer

class EquipmentCountriesViewSet(viewsets.ModelViewSet):
    queryset = EquipmentCountries.objects.all()
    serializer_class = EquipmentCountriesSerializer

class EquipmentBrandsViewSet(viewsets.ModelViewSet):
    queryset = EquipmentBrands.objects.all()
    serializer_class = EquipmentBrandsSerializer

class EquipmentModelsViewSet(viewsets.ModelViewSet):
    queryset = EquipmentModels.objects.all()
    serializer_class = EquipmentModelsSerializer

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer

class MaintenanceTypeViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceType.objects.all()
    serializer_class = MaintenanceTypeSerializer

class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = Maintenance.objects.all()
    serializer_class = MaintenanceSerializer

class RentViewSet(viewsets.ModelViewSet):
    queryset = Rent.objects.all()
    serializer_class = RentSerializer

class RentItemsViewSet(viewsets.ModelViewSet):
    queryset = RentItems.objects.all()
    serializer_class = RentItemsSerializer
