"""
Sikasem Payroll System - Base Django Settings
by Sikaba Systems
"""
import os
from pathlib import Path
from datetime import timedelta
import environ
# from rest_framework.views import exception_handler

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, '.env.example'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'phonenumber_field',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.companies',
    'apps.employees',
    'apps.payroll',
    'apps.attendance',
    'apps.leaves',
    'apps.loans',
    'apps.reports',
    'apps.notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.companies.middleware.CompanyContextMiddleware',
    'apps.accounts.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'sikasem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sikasem.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('DEFAULT_TIMEZONE', default='Africa/Accra')
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── REST FRAMEWORK ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'sikasem.pagination.StandardResultsPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '2000/hour',
    },
}

# ─── JWT ──────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:5173',
    'http://localhost:3000',
])
CORS_ALLOW_CREDENTIALS = True

# ─── CELERY ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ─── CACHES ───────────────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
    }
}

# ─── EMAIL ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Sikasem <noreply@sikasem.com>')

# ─── EXTERNAL SERVICES ────────────────────────────────────────────────────────
PAYSTACK_SECRET_KEY = env('PAYSTACK_SECRET_KEY', default='sk_live_13325ceed55912d9836b31220f942065a3ae3d4e')
PAYSTACK_PUBLIC_KEY = env('PAYSTACK_PUBLIC_KEY', default='pk_live_4691b598f3bd08a80bacd0713bfb45b977b24778')
PAYSTACK_BASE_URL = env('PAYSTACK_BASE_URL', default='https://api.paystack.co')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173')

# ─── SYSTEM DEFAULTS ──────────────────────────────────────────────────────────
DEFAULT_CURRENCY = env('DEFAULT_CURRENCY', default='GHS')
DEFAULT_COUNTRY = env('DEFAULT_COUNTRY', default='GH')

# ─── GHANA TAX CONSTANTS ──────────────────────────────────────────────────────
GHANA_PAYE_BANDS = [
    {'min': 0,       'max': 365,     'rate': 0.00,  'relief': 0},
    {'min': 365,     'max': 465,     'rate': 0.05,  'relief': 18.25},
    {'min': 465,     'max': 565,     'rate': 0.10,  'relief': 23.25},
    {'min': 565,     'max': 3565,    'rate': 0.175, 'relief': 65.50},
    {'min': 3565,    'max': 20000,   'rate': 0.25,  'relief': 316.00},
    {'min': 20000,   'max': float('inf'), 'rate': 0.30, 'relief': 1316.00},
]

SSNIT_EMPLOYEE_RATE = 0.055   # 5.5%
SSNIT_EMPLOYER_RATE = 0.13    # 13% (10% SSNIT + 2.5% Tier 2)
SSNIT_TIER1_RATE = 0.105      # 10.5% of employer contribution goes to SSNIT
SSNIT_TIER2_RATE = 0.025      # 2.5% goes to Tier 2 trustee

# Personal relief per year
PERSONAL_RELIEF_ANNUAL = 756.00  # GHS 756 per year = GHS 63/month
