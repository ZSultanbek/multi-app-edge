"""
Django settings for an app that lives under a path prefix (/alpha/).

The prefix handling is the interesting part. Three settings do the work:

  FORCE_SCRIPT_NAME     - tells Django it is mounted at /alpha, so every URL
                          it generates (redirects, {% url %}, static files)
                          carries the prefix.
  CSRF_TRUSTED_ORIGINS  - without this, POSTs behind a proxy fail CSRF checks
                          with a misleading "origin does not match" error.
  SECURE_PROXY_SSL_HEADER - lets Django see the real scheme when TLS is
                          terminated at the edge, instead of redirecting
                          https requests back to http forever.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-not-a-real-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# --- path prefix ------------------------------------------------------------
SCRIPT_NAME = os.environ.get("DJANGO_SCRIPT_NAME", "")
FORCE_SCRIPT_NAME = SCRIPT_NAME or None
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

STATIC_URL = f"{SCRIPT_NAME}/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "config.middleware.CloseStaleConnectionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "postgres://alpha:alpha@postgres:5432/alpha"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# --- celery -----------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_ACKS_LATE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "plain"},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
