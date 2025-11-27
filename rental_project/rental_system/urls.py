from django.urls import path
from rental_system import views

urlpatterns = [
    path('equipment/', views.EquipmentHomeView.as_view(), name='equipment_home'),
    path('equipment/countries/', views.EquipmentCountryView.as_view(), name='equipment_countries'),
    path('equipment/brands/', views.EquipmentBrandView.as_view(), name='equipment_brands'),
    path('equipment/models/', views.EquipmentModelView.as_view(), name='equipment_models'),
    path('equipment/list/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('clients/', views.ClientListView.as_view(), name='clients'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('addresses/', views.AddressListView.as_view(), name='addresses'),
    path('logs/', views.LogListView.as_view(), name='logs'),
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance'),
    path('maintenance/required/', views.RequiredMaintenanceView.as_view(), name='maintenance_required'),
    path('debts/monetary/', views.MonetaryDebtView.as_view(), name='monetary_debts'),
    path('debts/equipment/', views.EquipmentDebtView.as_view(), name='equipment_debts'),
    path('rents/create/', views.RentCreateView.as_view(), name='rent_create'),
    path('rents/', views.RentListView.as_view(), name='rent_list'),
    path('rents/payments/', views.RentPaymentView.as_view(), name='rent_payments'),
    path('clients/history/', views.ClientRentHistoryView.as_view(), name='client_rent_history'),
    path('csv/', views.CsvImportExportView.as_view(), name='csv_import_export'),
    path('backups/', views.BackupListView.as_view(), name='backup_list'),
    path("metrics/", views.metrics, name="metrics"),
    path("app-metrics/", views.app_metrics, name="app_metrics"),
]
