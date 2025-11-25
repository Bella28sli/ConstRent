from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime

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
    )
from django.contrib.auth import get_user_model
User = get_user_model()


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


class StaffRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        allowed_groups = {"admin", "leader", "manager", "technician"}
        in_allowed_group = request.user.groups.filter(name__in=allowed_groups).exists()
        if (
            not request.user.is_authenticated
            or not (request.user.is_staff or request.user.is_superuser or in_allowed_group)
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class EquipmentHomeView(LoginRequiredMixin, TemplateView):
    template_name = "equipment/home.html"


class EquipmentCountryView(StaffRequiredMixin, FormView):
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
        delete_id = request.POST.get("delete_id")
        if delete_id:
            EquipmentCountries.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ClientListView(StaffRequiredMixin, TemplateView):
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
        delete_id = request.POST.get("delete_id")
        if delete_id:
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


class UserListView(StaffRequiredMixin, TemplateView):
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
        delete_id = request.POST.get("delete_id")
        if delete_id:
            User.objects.filter(id=delete_id).delete()
            return redirect("users")

        edit_id = request.POST.get("edit_id")
        user_obj = User.objects.filter(id=edit_id).first() if edit_id else None
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
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


class AddressListView(StaffRequiredMixin, TemplateView):
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
        delete_id = request.POST.get("delete_id")
        if delete_id:
            Address.objects.filter(id=delete_id).delete()
            return redirect("addresses")

        edit_id = request.POST.get("edit_id")
        instance = Address.objects.filter(id=edit_id).first() if edit_id else None
        form = AddressForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("addresses")

        ctx = self.get_context_data()
        ctx["form"] = form
        ctx["edit_id"] = edit_id
        return self.render_to_response(ctx)


class LogListView(StaffRequiredMixin, TemplateView):
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


class EquipmentBrandView(StaffRequiredMixin, FormView):
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
        delete_id = request.POST.get("delete_id")
        if delete_id:
            EquipmentBrands.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class EquipmentModelView(StaffRequiredMixin, FormView):
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
        delete_id = request.POST.get("delete_id")
        if delete_id:
            EquipmentModels.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class EquipmentListView(StaffRequiredMixin, FormView):
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
            Equipment.objects.filter(id=delete_id).delete()
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
