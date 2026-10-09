"""
Django settings for campus_placement project.
Phase-1: Basic Authentication and Dashboard System
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env FIRST so all os.getenv() calls below can use it
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────
_SECRET_KEY_ENV = os.getenv('SECRET_KEY', '')
DEBUG = os.getenv('DEBUG', 'True').strip().lower() in ('true', '1', 'yes')

# Fail-fast: never run production without a real SECRET_KEY
if not DEBUG and (not _SECRET_KEY_ENV or 'insecure' in _SECRET_KEY_ENV.lower()):
    print(
        "FATAL: SECRET_KEY environment variable is missing or insecure in production. "
        "Set a strong random value and restart.",
        file=sys.stderr,
    )
    sys.exit(1)

# In dev, fall back to a clearly-marked insecure key so the app still starts.
SECRET_KEY = _SECRET_KEY_ENV or 'django-insecure-dev-only-change-me-in-production'

# Explicit ALLOWED_HOSTS — never default to '*' in production
_raw_hosts = os.getenv('ALLOWED_HOSTS', '')
if DEBUG:
    ALLOWED_HOSTS = _raw_hosts.split(',') if _raw_hosts else ['localhost', '127.0.0.1', '[::1]']
else:
    if not _raw_hosts or _raw_hosts.strip() == '*':
        print(
            "FATAL: ALLOWED_HOSTS must be set explicitly in production (not '*').",
            file=sys.stderr,
        )
        sys.exit(1)
    ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'core',
    'resumes',
    'attendance',
    'group_discussion',
    'aptitude_test',
    'mock_interviews',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',          # <-- serves static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'campus_placement.urls'

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
                'core.context_processors.coordinator_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'campus_placement.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────
# Local default: PostgreSQL on localhost (all params configurable via env)
import dj_database_url as _dj_db

_db_url = os.getenv('DATABASE_URL')
_db_password = os.getenv('DB_PASSWORD', '')

if _db_url:
    # Cloud deployments: DATABASE_URL takes priority
    DATABASES = {
        'default': _dj_db.config(default=_db_url, conn_max_age=600, ssl_require=True)
    }
else:
    if not DEBUG and not _db_password:
        print(
            "FATAL: DB_PASSWORD environment variable is not set in production.",
            file=sys.stderr,
        )
        sys.exit(1)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'campus_placement'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': _db_password or '1234',  # '1234' only safe for local dev
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static files (CSS, JavaScript, Images) ────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'        # collectstatic output

# Storage backends for static files and uploaded media
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": BASE_DIR / 'media',
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Login redirect
LOGIN_URL = '/'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Allow iframes for PDF viewing
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Performance: Caching configuration (Local Memory)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Resume settings
MAX_RESUME_SIZE_MB = 5
ALLOWED_RESUME_EXTENSIONS = ['pdf']

# ── ATS Microservice URL ──────────────────────────────────────────────────
ATS_SERVICE_URL = os.getenv('ATS_SERVICE_URL', 'http://127.0.0.1:8001')

# ── Email Configuration (SMTP via Gmail) ──────────────────────────────────
EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = 'smtp.gmail.com'
EMAIL_PORT         = 587
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'Campus Placement Training System <{EMAIL_HOST_USER}>')

# ── Production security hardening (only when DEBUG is off) ────────────────
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HSTS: tell browsers to only use HTTPS for 1 year (opt-in for subdomains)
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Redirect all HTTP → HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Strict referrer for privacy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CSRF trusted origins (set via env for production deployments)
_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

# Session hardening — use DB-backed sessions and expire on browser close in dev
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # set True in high-security deployments

# ── OTP Security Settings ─────────────────────────────────────────────────
OTP_EXPIRY_SECONDS = int(os.getenv('OTP_EXPIRY_SECONDS', '600'))   # 10 minutes
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', '5'))          # lock after 5 wrong attempts
OTP_RESEND_COOLDOWN = int(os.getenv('OTP_RESEND_COOLDOWN', '60'))   # 60 s between resends
