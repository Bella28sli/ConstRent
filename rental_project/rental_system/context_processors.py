from rental_system.models import UserPreference
from django.conf import settings
import os


def user_preferences(request):
    if request.user.is_authenticated:
        pref = UserPreference.objects.filter(user=request.user).first()
    else:
        pref = None
    return {"user_pref": pref}


def monitoring_links(request):
    # URL дашборда Grafana можно задать через env или settings
    url = os.environ.get("GRAFANA_DASHBOARD_URL", getattr(settings, "GRAFANA_DASHBOARD_URL", None))
    return {"grafana_dashboard_url": url}
