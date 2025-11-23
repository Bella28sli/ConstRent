from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from rental_system import models as rm


def perms_for_models(models, kinds):
    """
    kinds: iterable with any of "view", "add", "change", "delete"
    returns queryset of Permission objects for given models and actions.
    """
    cts = ContentType.objects.get_for_models(*models).values()
    return Permission.objects.filter(
        content_type__in=cts,
        codename__regex=f"^({'|'.join(kinds)})_",
    )


class Command(BaseCommand):
    help = "Создаёт группы (Администратор, Руководитель, Менеджер, Техник) и назначает права."

    def handle(self, *args, **options):
        # Группы
        admin_group, _ = Group.objects.get_or_create(name="Администратор")
        leader_group, _ = Group.objects.get_or_create(name="Руководитель")
        manager_group, _ = Group.objects.get_or_create(name="Менеджер")
        technician_group, _ = Group.objects.get_or_create(name="Техник")

        # Полный список моделей
        all_models = [
            rm.Role,
            rm.Address,
            rm.Log,
            rm.Client,
            rm.IndClient,
            rm.CompClient,
            rm.EquipmentCountries,
            rm.EquipmentBrands,
            rm.EquipmentModels,
            rm.Equipment,
            rm.MaintenanceType,
            rm.Maintenance,
            rm.Rent,
            rm.RentItems,
            rm.UserPreference,
        ]

        # Руководитель: только просмотр всего
        leader_perms = perms_for_models(all_models, ["view"])
        leader_group.permissions.set(leader_perms)

        # Менеджер: CRUD для оборудования, клиентов, адресов, аренды; просмотр остального
        manager_write_models = [
            rm.Address,
            rm.Client,
            rm.IndClient,
            rm.CompClient,
            rm.Equipment,
            rm.Rent,
            rm.RentItems,
        ]
        manager_read_only_models = [m for m in all_models if m not in manager_write_models]
        manager_perms = list(perms_for_models(manager_write_models, ["view", "add", "change", "delete"])) + list(
            perms_for_models(manager_read_only_models, ["view"])
        )
        manager_group.permissions.set(manager_perms)

        # Техник: CRUD только для Maintenance; просмотр остального
        tech_write_models = [rm.Maintenance]
        tech_read_only_models = [m for m in all_models if m not in tech_write_models]
        tech_perms = list(perms_for_models(tech_write_models, ["view", "add", "change", "delete"])) + list(
            perms_for_models(tech_read_only_models, ["view"])
        )
        technician_group.permissions.set(tech_perms)

        # Администратор: даст полный доступ через superuser/is_staff; группу чистим/не используем
        admin_group.permissions.clear()

        self.stdout.write(self.style.SUCCESS("Группы и права обновлены: Администратор, Руководитель, Менеджер, Техник."))
