from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime
from django.db import connection
from django.core.exceptions import ValidationError
import csv
from django.http import HttpResponse
from django.conf import settings
import os
from django.db.models import OuterRef, Subquery, Max, F, Q as DJ_Q
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from rental_system.metrics import update_custom_metrics

from rental_system.services import RentalService
from rental_system.forms import (
    UserPreferenceForm,
    EquipmentCountryForm,
    EquipmentBrandForm,
    EquipmentModelForm,
    EquipmentForm,
    ClientForm,
    IndividualClientForm,
    CompanyClientForm,
    UserForm,
    AddressForm,
    MaintenanceForm,
    RentCreateForm,
    RentUpdateForm,
    RentPaymentForm,
)
from rental_system.models import (
    UserPreference,
    EquipmentCountries,
    EquipmentBrands,
    EquipmentModels,
    Equipment,
    Client,
    IndClient,
    CompClient,
    Address,
    Log,
    Maintenance,
    Rent,
    RentItems,
)
from django.contrib.auth import get_user_model
User = get_user_model()

# Алиасы для имен групп (рус/англ)
GROUP_ALIASES = {
    "admin": ["admin", "администратор", "админ", "администратор системы"],
    "leader": ["leader", "руководитель"],
    "manager": ["manager", "менеджер"],
    "technician": ["technician", "техник", "технический специалист"],
}

def metrics(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


def app_metrics(request):
    """
    Экспорт кастомных бизнес-метрик (с multiprocess registry).
    """
    update_custom_metrics()
    output = generate_latest()
    return HttpResponse(output, content_type=CONTENT_TYPE_LATEST)

def _group_in(user, names):
    """Проверяет наличие пользователя хотя бы в одной группе из списка (с учетом алиасов и регистра)."""
    if not user or not user.is_authenticated:
        return False
    names_norm = set()
    for n in names:
        n = (n or "").strip().lower()
        if not n:
            continue
        names_norm.add(n)
        for key, aliases in GROUP_ALIASES.items():
            if n == key or n in aliases:
                names_norm.add(key)
                names_norm.update(a.lower() for a in aliases)
    user_groups = set(g.lower() for g in user.groups.values_list("name", flat=True))
    return bool(user_groups.intersection(names_norm))


def is_admin(user):
    return bool(user and (user.is_superuser or _group_in(user, ["admin"])))


def is_leader(user):
    return _group_in(user, ["leader"])


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = None  # None -> только админ; set -> админ или роль из списка

    def has_access(self, user):
        if not user.is_authenticated:
            return False
        if is_admin(user) or is_leader(user):
            return True
        if self.allowed_roles:
            return _group_in(user, self.allowed_roles)
        return False

    def _deny_leader_write(self):
        if is_leader(self.request.user):
            return self.handle_no_permission()
        return None

    def dispatch(self, request, *args, **kwargs):
        if not self.has_access(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"


class AccountSettingsView(LoginRequiredMixin, FormView):
    template_name = "account/settings.html"
    form_class = UserPreferenceForm
    success_url = reverse_lazy("account_settings")

    def get_initial(self):
        pref, _ = UserPreference.objects.get_or_create(user=self.request.user)
        return {
            "theme": pref.theme,
            "date_format": pref.date_format,
            "number_format": pref.number_format,
            "page_size": pref.page_size,
        }

    def form_valid(self, form):
        pref, _ = UserPreference.objects.get_or_create(user=self.request.user)
        for field, value in form.cleaned_data.items():
            setattr(pref, field, value)
        pref.save()
        return super().form_valid(form)


class EquipmentHomeView(RoleRequiredMixin, TemplateView):
    allowed_roles = {"manager"}
    template_name = "equipment/home.html"


class EquipmentCountryView(RoleRequiredMixin, FormView):
    allowed_roles = None  # только админ
    template_name = "equipment/countries.html"
    form_class = EquipmentCountryForm
    success_url = reverse_lazy("equipment_countries")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["countries"] = EquipmentCountries.objects.all()
        ctx["edit_id"] = self.request.GET.get("edit_id")
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        edit_id = self.request.GET.get("edit_id")
        if edit_id:
            try:
                kwargs["instance"] = EquipmentCountries.objects.get(id=edit_id)
            except EquipmentCountries.DoesNotExist:
                pass
        return kwargs

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            EquipmentCountries.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        guard = self._deny_leader_write()
        if guard:
            return guard
        form.save()
        return super().form_valid(form)


class ClientListView(RoleRequiredMixin, TemplateView):
    allowed_roles = {"manager"}
    template_name = "clients/list.html"

    def get_queryset(self):
        qs = Client.objects.select_related("indclient", "compclient")
        type_filter = self.request.GET.get("type")
        search = self.request.GET.get("q")
        sort = self.request.GET.get("sort", "recent")

        if type_filter in ("individual", "company"):
            qs = qs.filter(type=type_filter)
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(phone_number__icontains=search)
                | Q(indclient__last_name__icontains=search)
                | Q(indclient__first_name__icontains=search)
                | Q(compclient__company_name__icontains=search)
            )

        if sort == "name":
            qs = qs.order_by("type", "indclient__last_name", "compclient__company_name", "email")
        elif sort == "email":
            qs = qs.order_by("email")
        else:
            qs = qs.order_by("-id")
        return qs

    def get_forms(self, edit_client=None):
        base_form = ClientForm(instance=edit_client) if edit_client else ClientForm()
        if edit_client and edit_client.type == "company":
            company_form = CompanyClientForm(instance=getattr(edit_client, "compclient", None))
            individual_form = IndividualClientForm()
            detail_type = "company"
        elif edit_client and edit_client.type == "individual":
            individual_form = IndividualClientForm(instance=getattr(edit_client, "indclient", None))
            company_form = CompanyClientForm()
            detail_type = "individual"
        else:
            individual_form = IndividualClientForm()
            company_form = CompanyClientForm()
            detail_type = "individual"
        return base_form, individual_form, company_form, detail_type

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        edit_id = self.request.GET.get("edit_id")
        edit_client = None
        if edit_id:
            edit_client = Client.objects.filter(id=edit_id).first()
        base_form, indiv_form, comp_form, detail_type = self.get_forms(edit_client)
        ctx.update(
            {
                "clients": self.get_queryset(),
                "base_form": base_form,
                "individual_form": indiv_form,
                "company_form": comp_form,
                "detail_type": detail_type,
                "edit_id": edit_id,
                "filters": {
                    "q": self.request.GET.get("q", ""),
                    "type": self.request.GET.get("type", ""),
                    "sort": self.request.GET.get("sort", "recent"),
                },
            }
        )
        return ctx

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            if not is_admin(request.user):
                has_links = Rent.objects.filter(client_id=delete_id).exists()
                if has_links:
                    return self.handle_no_permission()
            Client.objects.filter(id=delete_id).delete()
            return redirect("clients")

        edit_id = request.POST.get("edit_id")
        client = Client.objects.filter(id=edit_id).first() if edit_id else None
        client_type = request.POST.get("type") or (client.type if client else "individual")

        base_form = ClientForm(request.POST, instance=client)
        indiv_instance = client.indclient if client and hasattr(client, "indclient") else None
        comp_instance = client.compclient if client and hasattr(client, "compclient") else None
        individual_form = IndividualClientForm(request.POST, instance=indiv_instance)
        company_form = CompanyClientForm(request.POST, instance=comp_instance)

        detail_form = company_form if client_type == "company" else individual_form

        if base_form.is_valid() and detail_form.is_valid():
            guard = self._deny_leader_write()
            if guard:
                return guard
            base = base_form.save(commit=False)
            base.type = client_type
            base.save()
            detail = detail_form.save(commit=False)
            detail.client = base
            detail.save()
            return redirect("clients")

        # invalid: re-render with forms and filters
        ctx = self.get_context_data()
        ctx["base_form"] = base_form
        ctx["individual_form"] = individual_form
        ctx["company_form"] = company_form
        ctx["detail_type"] = client_type
        ctx["edit_id"] = edit_id
        return self.render_to_response(ctx)


class UserListView(RoleRequiredMixin, TemplateView):
    template_name = "users/list.html"

    def get_queryset(self):
        qs = User.objects.all()
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))
        sort = self.request.GET.get("sort", "recent")
        if sort == "username":
            qs = qs.order_by("username")
        elif sort == "email":
            qs = qs.order_by("email")
        else:
            qs = qs.order_by("-id")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        edit_id = self.request.GET.get("edit_id")
        edit_user = User.objects.filter(id=edit_id).first() if edit_id else None
        form = UserForm(instance=edit_user)
        ctx.update(
            {
                "users": self.get_queryset(),
                "form": form,
                "edit_id": edit_id,
                "filters": {
                    "q": self.request.GET.get("q", ""),
                    "sort": self.request.GET.get("sort", "recent"),
                },
            }
        )
        return ctx

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            User.objects.filter(id=delete_id).delete()
            return redirect("users")

        edit_id = request.POST.get("edit_id")
        user_obj = User.objects.filter(id=edit_id).first() if edit_id else None
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            guard = self._deny_leader_write()
            if guard:
                return guard
            password = form.cleaned_data.get("password")
            user = form.save(commit=False)
            if password:
                user.set_password(password)
            user.save()
            group = form.cleaned_data.get("group")
            user.groups.clear()
            if group:
                user.groups.add(group)
            return redirect("users")

        ctx = self.get_context_data()
        ctx["form"] = form
        ctx["edit_id"] = edit_id
        return self.render_to_response(ctx)


class AddressListView(RoleRequiredMixin, TemplateView):
    allowed_roles = {"manager"}
    template_name = "addresses/list.html"

    def get_queryset(self):
        qs = Address.objects.all()
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(full_address__icontains=search)
        return qs.order_by("city", "street", "house")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        edit_id = self.request.GET.get("edit_id")
        instance = Address.objects.filter(id=edit_id).first() if edit_id else None
        form = AddressForm(instance=instance)
        ctx.update(
            {
                "addresses": self.get_queryset(),
                "form": form,
                "edit_id": edit_id,
                "filters": {"q": self.request.GET.get("q", "")},
            }
        )
        return ctx

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            if not is_admin(request.user):
                has_links = (
                    IndClient.objects.filter(registration_address_id=delete_id).exists()
                    or IndClient.objects.filter(actual_address_id=delete_id).exists()
                    or CompClient.objects.filter(address_id=delete_id).exists()
                )
                if has_links:
                    return self.handle_no_permission()
            Address.objects.filter(id=delete_id).delete()
            return redirect("addresses")

        edit_id = request.POST.get("edit_id")
        instance = Address.objects.filter(id=edit_id).first() if edit_id else None
        form = AddressForm(request.POST, instance=instance)
        if form.is_valid():
            guard = self._deny_leader_write()
            if guard:
                return guard
            form.save()
            return redirect("addresses")

        ctx = self.get_context_data()
        ctx["form"] = form
        ctx["edit_id"] = edit_id
        return self.render_to_response(ctx)


class MaintenanceListView(RoleRequiredMixin, FormView):
    allowed_roles = {"technician"}
    template_name = "maintenance/list.html"
    form_class = MaintenanceForm
    success_url = reverse_lazy("maintenance")

    def dispatch(self, request, *args, **kwargs):
        # запоминаем, редактируем ли запись
        self.edit_id = request.GET.get("edit_id") or request.POST.get("edit_id")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        queryset = Equipment.objects.filter(status="available")
        if getattr(form.instance, "equipment_id", None):
            queryset = Equipment.objects.filter(id=form.instance.equipment_id) | queryset
        form.fields["equipment"].queryset = queryset.distinct()
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.edit_id:
            instance = Maintenance.objects.filter(id=self.edit_id).first()
            if instance:
                kwargs["instance"] = instance
        return kwargs

    def get_queryset(self):
        with connection.cursor() as cursor:
            if is_admin(self.request.user):
                cursor.execute(
                    """
                    SELECT maintenance_id,
                           maintenance_date,
                           equipment_id,
                           equipment_name,
                           staff_id,
                           first_name,
                           last_name,
                           description,
                           status
                    FROM maintenance_schedule_view
                    ORDER BY maintenance_date DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT maintenance_id,
                           maintenance_date,
                           equipment_id,
                           equipment_name,
                           staff_id,
                           first_name,
                           last_name,
                           description,
                           status
                    FROM maintenance_schedule_view
                    WHERE staff_id = %s
                    ORDER BY maintenance_date DESC
                    """,
                    [self.request.user.id],
                )

            cols = [col[0] for col in cursor.description]
            items = []
            for row in cursor.fetchall():
                data = dict(zip(cols, row))
                full_name = f"{data.get('last_name') or ''} {data.get('first_name') or ''}".strip()
                data["staff_full_name"] = full_name or None
                items.append(data)
            return items

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.get_queryset()
        ctx["edit_id"] = self.edit_id
        return ctx

    def form_valid(self, form):
        guard = self._deny_leader_write()
        if guard:
            return guard
        obj = form.save(commit=False)
        obj.staff = self.request.user
        obj.save()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            if not is_admin(request.user):
                has_links = False  # сейчас расписание ТО не используется в других связях
                if has_links:
                    return self.handle_no_permission()
            Maintenance.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


class RentCreateView(RoleRequiredMixin, FormView):
    allowed_roles = {"manager"}
    template_name = "rents/create.html"
    form_class = RentCreateForm
    success_url = reverse_lazy("rent_list")

    def form_valid(self, form):
        guard = self._deny_leader_write()
        if guard:
            return guard
        cleaned = form.cleaned_data
        try:
            rent = RentalService.create_rent_transaction(
                client_id=cleaned["client"].id,
                staff_id=self.request.user.id,
                equipment_ids=[eq.id for eq in cleaned["equipments"]],
                start_date=cleaned["start_date"],
                planned_end_date=cleaned["planned_end_date"],
                total_amount=cleaned["total_amount"],
                rent_agreement_date=cleaned.get("start_date"),
            )
            # Проставляем статус/оплату из формы, если нужно
            rent.rent_status = cleaned.get("rent_status", rent.rent_status)
            rent.is_paid = cleaned.get("is_paid", rent.is_paid)
            rent.save(update_fields=["rent_status", "is_paid"])
        except ValidationError as exc:
            form.add_error(None, exc.message if hasattr(exc, "message") else exc)
            return self.form_invalid(form)
        return super().form_valid(form)


class RentListView(RoleRequiredMixin, TemplateView):
    allowed_roles = {"admin", "manager"}
    template_name = "rents/list.html"

    def get_queryset(self):
        qs = Rent.objects.select_related("client", "staff").order_by("-start_date")
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        paid = self.request.GET.get("paid")
        if q:
            qs = qs.filter(rent_agreement_number__icontains=q)
        if status:
            qs = qs.filter(rent_status=status)
        if paid in ("yes", "no"):
            qs = qs.filter(is_paid=(paid == "yes"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        edit_id = self.request.GET.get("edit_id")
        is_admin_user = is_admin(self.request.user)
        if not is_admin_user:
            edit_id = None
        instance = Rent.objects.filter(id=edit_id).first() if edit_id else None
        form = RentUpdateForm(instance=instance) if is_admin_user else None
        ctx.update({"rents": self.get_queryset(), "form": form, "edit_id": edit_id})
        return ctx

    def post(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return self.handle_no_permission()
        delete_id = request.POST.get("delete_id")
        if delete_id:
            rent = Rent.objects.filter(id=delete_id).first()
            if rent:
                eq_ids = list(RentItems.objects.filter(rent=rent).values_list("equipment_id", flat=True))
                RentItems.objects.filter(rent=rent).delete()
                Equipment.objects.filter(id__in=eq_ids).update(status="available")
                rent.delete()
            return redirect("rent_list")

        edit_id = request.POST.get("edit_id")
        rent = Rent.objects.filter(id=edit_id).first() if edit_id else None
        form = RentUpdateForm(request.POST, instance=rent)
        if form.is_valid():
            rent = form.save(commit=False)
            rent.staff = request.user
            rent.save()
            equipments = form.cleaned_data["equipments"]
            RentItems.objects.filter(rent=rent).delete()
            Equipment.objects.filter(rentitems__rent=rent).update(status="available")
            for eq in equipments:
                RentItems.objects.create(rent=rent, equipment=eq)
                eq.status = "rented"
                eq.save(update_fields=["status"])
            return redirect("rent_list")

        ctx = self.get_context_data()
        ctx["form"] = form
        ctx["edit_id"] = edit_id
        return self.render_to_response(ctx)


# ---------- Error handlers ----------
ERROR_RESOLUTIONS = {
    "ValidationError": "Проверьте заполнение формы и исправьте отмеченные поля.",
    "PermissionDenied": "У вас недостаточно прав. Обратитесь к администратору или войдите под другой учетной записью.",
    404: "Проверьте правильность адреса или вернитесь на главную страницу.",
    500: "Попробуйте позже или обратитесь к администратору.",
    403: "Нет доступа к запрошенному ресурсу. Свяжитесь с администратором для выдачи прав.",
}


def render_error(request, exception=None, status_code=500):
    code = getattr(exception, "code", None) or status_code
    message = getattr(exception, "message", None) or str(exception) if exception else "Внутренняя ошибка сервера"
    resolution = ERROR_RESOLUTIONS.get(code) or ERROR_RESOLUTIONS.get(getattr(exception, "__class__", type).__name__) or "Обратитесь к администратору или попробуйте повторить позже."
    context = {
        "error_code": code,
        "error_message": message,
        "resolution": resolution,
    }
    return render(request, "errors/error.html", context=context, status=status_code)


def error_404(request, exception):
    return render_error(request, exception, status_code=404)


def error_500(request):
    return render_error(request, None, status_code=500)


def error_403(request, exception):
    return render_error(request, exception, status_code=403)


class RentPaymentView(RoleRequiredMixin, TemplateView):
    template_name = "rents/payments.html"

    def get_queryset(self):
        return Rent.objects.filter(is_paid=False).order_by("-start_date")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rents"] = self.get_queryset()
        ctx["form"] = RentPaymentForm()
        return ctx

    def post(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return self.handle_no_permission()
        rent_id = request.POST.get("rent_id")
        rent = Rent.objects.filter(id=rent_id, is_paid=False).first()
        if not rent:
            return redirect("rent_payments")
        form = RentPaymentForm(request.POST, instance=rent)
        if form.is_valid():
            rent = form.save(commit=False)
            rent.is_paid = True
            rent.save()
            return redirect("rent_payments")
        ctx = self.get_context_data()
        ctx["form"] = form
        return self.render_to_response(ctx)


class RequiredMaintenanceView(RoleRequiredMixin, TemplateView):
    allowed_roles = {"technician"}
    template_name = "maintenance/required.html"

    def get_queryset(self):
        latest_maintenance = Subquery(
            Maintenance.objects.filter(equipment=OuterRef("pk"))
            .order_by("-maintenance_date")
            .values("maintenance_date")[:1]
        )
        qs = (
            Equipment.objects.annotate(
                last_rent_end=Max("rentitems__rent__actual_end_date"),
                last_maintenance=latest_maintenance,
            )
            .filter(last_rent_end__isnull=False, status="available")
            .filter(
                DJ_Q(last_maintenance__isnull=True)
                | DJ_Q(last_maintenance__lt=F("last_rent_end"))
            )
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.get_queryset()
        return ctx


class ClientRentHistoryView(RoleRequiredMixin, TemplateView):
    allowed_roles = {"manager"}
    template_name = "clients/history.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        client_id = self.request.GET.get("client_id")
        history = []
        if client_id:
            try:
                history = RentalService.get_client_rental_history(int(client_id))
            except Exception:
                history = []
        ctx["clients"] = Client.objects.all()
        ctx["history"] = history
        ctx["selected_client_id"] = client_id
        return ctx


class MonetaryDebtView(RoleRequiredMixin, TemplateView):
    template_name = "debts/monetary.html"

    def get_queryset(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT client_id, email, phone_number, client_name, client_type,
                       rent_id, rent_agreement_number, total_amount, start_date,
                       planned_end_date, actual_end_date, rent_duration_days
                FROM monetary_debt_view
                ORDER BY planned_end_date ASC NULLS LAST
                """
            )
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.get_queryset()
        return ctx


class EquipmentDebtView(RoleRequiredMixin, TemplateView):
    template_name = "debts/equipment.html"

    def get_queryset(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT client_id, email, phone_number, client_name, client_type,
                       rent_id, rent_agreement_number, start_date, planned_end_date,
                       return_date, equipment_name, equipment_code, days_overdue, late_fee
                FROM equipment_return_debt_view
                ORDER BY days_overdue DESC
                """
            )
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.get_queryset()
        return ctx


class CsvImportExportView(RoleRequiredMixin, TemplateView):
    template_name = "csv/import_export.html"

    def export_csv(self, entity):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{entity}.csv"'
        # Добавляем BOM, чтобы корректно открывалось в Excel/Windows
        response.write("\ufeff")
        writer = csv.writer(response, delimiter=";")
        if entity == "equipment":
            writer.writerow(["id", "name", "code", "status"])
            for e in Equipment.objects.all():
                writer.writerow([e.id, e.equipment_name, e.equipment_code, e.status])
        elif entity == "clients":
            writer.writerow(["id", "email", "phone", "type"])
            for c in Client.objects.all():
                writer.writerow([c.id, c.email, c.phone_number, c.type])
        elif entity == "rents":
            writer.writerow(["id", "agreement", "client", "start_date", "planned_end_date", "status", "is_paid"])
            for r in Rent.objects.all():
                writer.writerow([r.id, r.rent_agreement_number, r.client_id, r.start_date, r.planned_end_date, r.rent_status, r.is_paid])
        else:
            writer.writerow(["unknown entity"])
        return response

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        entity = request.POST.get("entity")
        guard = self._deny_leader_write()
        if guard:
            return guard
        if action == "import":
            file = request.FILES.get("file")
            if not file:
                return redirect("csv_import_export")
            try:
                decoded = file.read().decode("utf-8").splitlines()
                reader = csv.DictReader(decoded)
                if entity == "equipment":
                    for row in reader:
                        Equipment.objects.update_or_create(
                            equipment_code=row.get("code"),
                            defaults={
                                "equipment_name": row.get("name", ""),
                                "status": row.get("status", "available"),
                            },
                        )
                elif entity == "clients":
                    for row in reader:
                        Client.objects.update_or_create(
                            email=row.get("email"),
                            defaults={
                                "phone_number": row.get("phone"),
                                "type": row.get("type", "individual"),
                            },
                        )
            except Exception:
                pass
            return redirect("csv_import_export")
        return redirect("csv_import_export")

    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        entity = request.GET.get("entity")
        if action == "export" and entity:
            return self.export_csv(entity)
        return super().get(request, *args, **kwargs)


class BackupListView(RoleRequiredMixin, TemplateView):
    template_name = "backups/list.html"

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        action = request.POST.get("action")
        backup_dir = getattr(settings, "BACKUP_DIR", None)
        if action == "create" and backup_dir:
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{ts}.bak"
            path = os.path.join(backup_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"Backup placeholder created at {ts}")
        return redirect("backup_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        backups = []
        backup_dir = getattr(settings, "BACKUP_DIR", None)
        if backup_dir and os.path.isdir(backup_dir):
            for name in os.listdir(backup_dir):
                if name.lower().endswith(".bak"):
                    backups.append(name)
        ctx["backups"] = backups
        return ctx


class LogListView(RoleRequiredMixin, TemplateView):
    template_name = "logs/list.html"

    def _parse_dt(self, value):
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
        except Exception:
            return None

    def get_queryset(self):
        qs = Log.objects.select_related("staff").order_by("-log_date")
        search = self.request.GET.get("q")
        action = self.request.GET.get("action")
        success = self.request.GET.get("success")
        date_from = self._parse_dt(self.request.GET.get("date_from"))
        date_to = self._parse_dt(self.request.GET.get("date_to"))

        if search:
            qs = qs.filter(
                Q(description_text__icontains=search)
                | Q(action_type__icontains=search)
                | Q(staff__username__icontains=search)
            )
        if action:
            qs = qs.filter(action_type=action)
        if success in ("true", "false"):
            qs = qs.filter(success_status=(success == "true"))
        if date_from:
            qs = qs.filter(log_date__gte=date_from)
        if date_to:
            qs = qs.filter(log_date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        paginator = Paginator(qs, 20)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        params = self.request.GET.copy()
        params.pop("page", True)
        ctx["logs"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["querystring"] = params.urlencode()
        ctx["filters"] = {
            "q": self.request.GET.get("q", ""),
            "action": self.request.GET.get("action", ""),
            "success": self.request.GET.get("success", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
        }
        ctx["actions"] = Log.ActionType.choices if hasattr(Log, "ActionType") else []
        return ctx


class EquipmentBrandView(RoleRequiredMixin, FormView):
    allowed_roles = None  # только админ
    template_name = "equipment/brands.html"
    form_class = EquipmentBrandForm
    success_url = reverse_lazy("equipment_brands")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["brands"] = EquipmentBrands.objects.all()
        ctx["edit_id"] = self.request.GET.get("edit_id")
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        edit_id = self.request.GET.get("edit_id")
        if edit_id:
            try:
                kwargs["instance"] = EquipmentBrands.objects.get(id=edit_id)
            except EquipmentBrands.DoesNotExist:
                pass
        return kwargs

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            EquipmentBrands.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        guard = self._deny_leader_write()
        if guard:
            return guard
        form.save()
        return super().form_valid(form)


class EquipmentModelView(RoleRequiredMixin, FormView):
    allowed_roles = None  # только админ
    template_name = "equipment/models.html"
    form_class = EquipmentModelForm
    success_url = reverse_lazy("equipment_models")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["models"] = EquipmentModels.objects.all()
        ctx["edit_id"] = self.request.GET.get("edit_id")
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        edit_id = self.request.GET.get("edit_id")
        if edit_id:
            try:
                kwargs["instance"] = EquipmentModels.objects.get(id=edit_id)
            except EquipmentModels.DoesNotExist:
                pass
        return kwargs

    def post(self, request, *args, **kwargs):
        guard = self._deny_leader_write()
        if guard:
            return guard
        delete_id = request.POST.get("delete_id")
        if delete_id:
            EquipmentModels.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        guard = self._deny_leader_write()
        if guard:
            return guard
        form.save()
        return super().form_valid(form)


class EquipmentListView(RoleRequiredMixin, FormView):
    allowed_roles = {"manager"}
    template_name = "equipment/list.html"
    form_class = EquipmentForm
    success_url = reverse_lazy("equipment_list")

    def get_queryset(self):
        qs = Equipment.objects.select_related("model", "brand", "country")
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        brand = self.request.GET.get("brand")
        country = self.request.GET.get("country")
        model_id = self.request.GET.get("model")
        if q:
            qs = qs.filter(equipment_name__icontains=q) | qs.filter(equipment_code__icontains=q)
        if status:
            qs = qs.filter(status=status)
        if brand:
            qs = qs.filter(brand_id=brand)
        if country:
            qs = qs.filter(country_id=country)
        if model_id:
            qs = qs.filter(model_id=model_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["equipments"] = self.get_queryset()
        ctx["brands"] = EquipmentBrands.objects.all()
        ctx["countries"] = EquipmentCountries.objects.all()
        ctx["models"] = EquipmentModels.objects.all()
        ctx["edit_id"] = self.request.GET.get("edit_id")
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        edit_id = self.request.GET.get("edit_id")
        if edit_id:
            try:
                kwargs["instance"] = Equipment.objects.get(id=edit_id)
            except Equipment.DoesNotExist:
                pass
        return kwargs

    def post(self, request, *args, **kwargs):
        delete_id = request.POST.get("delete_id")
        if delete_id:
            guard = self._deny_leader_write()
            if guard:
                return guard
            if not is_admin(request.user):
                has_links = (
                    RentItems.objects.filter(equipment_id=delete_id).exists()
                    or Maintenance.objects.filter(equipment_id=delete_id).exists()
                )
                if has_links:
                    return self.handle_no_permission()
            Equipment.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        guard = self._deny_leader_write()
        if guard:
            return guard
        form.save()
        return super().form_valid(form)
