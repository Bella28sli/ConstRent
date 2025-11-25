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
]
