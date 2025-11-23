from django.contrib import admin

from .models import (
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


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_name")
    search_fields = ("role_name",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "full_address", "region", "city", "street")
    search_fields = ("full_address", "city", "street", "region")


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("id", "log_date", "staff", "action_type", "success_status")
    list_filter = ("action_type", "success_status")
    search_fields = ("description_text",)
    readonly_fields = ("log_date",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "phone_number", "type")
    search_fields = ("email", "phone_number")
    list_filter = ("type",)


@admin.register(IndClient)
class IndClientAdmin(admin.ModelAdmin):
    list_display = ("client", "last_name", "first_name", "passport_number")
    search_fields = ("last_name", "first_name", "passport_number")


@admin.register(CompClient)
class CompClientAdmin(admin.ModelAdmin):
    list_display = ("client", "company_name", "inn", "kpp")
    search_fields = ("company_name", "inn", "kpp")


@admin.register(EquipmentCountries)
class EquipmentCountriesAdmin(admin.ModelAdmin):
    list_display = ("id", "country")
    search_fields = ("country",)


@admin.register(EquipmentBrands)
class EquipmentBrandsAdmin(admin.ModelAdmin):
    list_display = ("id", "brand")
    search_fields = ("brand",)


@admin.register(EquipmentModels)
class EquipmentModelsAdmin(admin.ModelAdmin):
    list_display = ("id", "model_name")
    search_fields = ("model_name",)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "equipment_name", "equipment_code", "status", "rental_price_day")
    search_fields = ("equipment_name", "equipment_code")
    list_filter = ("status", "fuel_type")


@admin.register(MaintenanceType)
class MaintenanceTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "type_name")
    search_fields = ("type_name",)


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ("id", "maintenance_date", "equipment", "status", "work_type", "staff")
    list_filter = ("status", "work_type")
    search_fields = ("description",)


class RentItemsInline(admin.TabularInline):
    model = RentItems
    extra = 0


@admin.register(Rent)
class RentAdmin(admin.ModelAdmin):
    list_display = ("id", "rent_agreement_number", "client", "staff", "rent_status", "total_amount", "is_paid")
    list_filter = ("rent_status", "is_paid")
    search_fields = ("rent_agreement_number",)
    inlines = [RentItemsInline]


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "date_format", "number_format", "page_size", "updated_at")
    list_filter = ("theme", "date_format", "number_format")
