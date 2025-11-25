"""
URL configuration for rental_project project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rental_system.views import HomeView, AccountSettingsView

from rental_system.views_backup import download_backup
from rest_framework.permissions import AllowAny
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import OpenAPIRenderer

try:
    from rest_framework.renderers import SwaggerUIRenderer
    _schema_renderers = [OpenAPIRenderer, SwaggerUIRenderer]
except ImportError:  # pragma: no cover
    SwaggerUIRenderer = None
    _schema_renderers = [OpenAPIRenderer]

schema_view = get_schema_view(
    title="ConstRent API",
    description="OpenAPI спецификация API аренды оборудования.",
    version="1.0.0",
    public=True,
    permission_classes=[AllowAny],
    renderer_classes=_schema_renderers,
)
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('account/settings/', AccountSettingsView.as_view(), name='account_settings'),
    path('admin/backups/<str:filename>/', download_backup, name='download_backup'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('rental_system.urls')),
    path('api/', include('api.urls')),
    path('api/schema/', schema_view, name='openapi-schema'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
