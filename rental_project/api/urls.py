from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'roles', views.RoleViewSet)
router.register(r'addresses', views.AddressViewSet)
router.register(r'staff', views.StaffViewSet)
router.register(r'logs', views.LogViewSet)
router.register(r'clients', views.ClientViewSet)
router.register(r'indclients', views.IndClientViewSet)
router.register(r'compclients', views.CompClientViewSet)
router.register(r'equipment_countries', views.EquipmentCountriesViewSet)
router.register(r'equipment_brands', views.EquipmentBrandsViewSet)
router.register(r'equipment_models', views.EquipmentModelsViewSet)
router.register(r'equipment', views.EquipmentViewSet)
router.register(r'maintenance_types', views.MaintenanceTypeViewSet)
router.register(r'maintenance', views.MaintenanceViewSet)
router.register(r'rent', views.RentViewSet)
router.register(r'rent_items', views.RentItemsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
