"""
URL configuration for rental_project project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rental_system.views import HomeView, AccountSettingsView
import rental_system.views as rs_views

from rental_system.views_backup import download_backup
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('account/settings/', AccountSettingsView.as_view(), name='account_settings'),
    path('admin/backups/<str:filename>/', download_backup, name='download_backup'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('rental_system.urls')),
    path('api/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(api_version='1.0.0'), name='openapi-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='openapi-schema'), name='swagger-ui'),
    path('prometheus/', include('django_prometheus.urls')),
]

handler404 = "rental_system.views.error_404"
handler500 = "rental_system.views.error_500"
handler403 = "rental_system.views.error_403"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
