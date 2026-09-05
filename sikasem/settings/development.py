"""sikasem/settings/development.py"""
import sys

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Django's test runner cannot load Debug Toolbar, so keep it development-only.
if 'test' not in sys.argv:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']

# Use SQLite for quick dev setup (no Postgres required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# No Redis needed in dev - use memory cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery - run tasks synchronously in dev
CELERY_TASK_ALWAYS_EAGER = True

# Console email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'apps': {'handlers': ['console'], 'level': 'DEBUG'},
        'django': {'handlers': ['console'], 'level': 'INFO'},
    },
}
