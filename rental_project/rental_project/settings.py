"""
Django settings for rental_project project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

PROMETHEUS_METRICS_DIR = BASE_DIR / 'prometheus_multiproc_dir'
os.makedirs(PROMETHEUS_METRICS_DIR, exist_ok=True)

os.environ['PROMETHEUS_MULTIPROC_DIR'] = str(PROMETHEUS_METRICS_DIR)

# Security (временно без вынесения в env)
SECRET_KEY = 'django-insecure-h)=g1)3cy9e&&6a-!#-zk@rl^dpp@*@1k$uua!l7=)ov1@q!v&'
DEBUG = True
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_prometheus',
    'rental_system',
    'rest_framework',
    'api',
    'backups',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'rental_system.middleware.CurrentUserToDBMiddleware',
    'rental_system.middleware.HttpErrorMetricsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'rental_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'rental_system.context_processors.user_preferences',
                'rental_system.context_processors.monitoring_links',
            ],
        },
    },
]

WSGI_APPLICATION = 'rental_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rental_system_db',
        'USER': 'postgres',
        'PASSWORD': '1',
        # В контейнере обращаемся по имени сервиса docker-compose
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': '5432',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'api.schema.TaggedAutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'api.exception_handler.custom_exception_handler',
}

# Internationalization
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static/media files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Directory for DB backups (used by backup download view/command)
BACKUP_DIR = BASE_DIR / "backups"

# Auth redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Email backend (для восстановления пароля отправляем в консоль)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# SMTP через Gmail (используйте пароль приложения, а не основной пароль аккаунта)
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = "re_dQV8rEv9_6N95q8aNRvQQWZJxAQjYg9BD"  # пароль приложения Gmail (без пробелов)
DEFAULT_FROM_EMAIL = "isabellaslivina@gmail.com"
