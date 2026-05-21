"""
Django settings for campus_placement project.
Phase-1: Basic Authentication and Dashboard System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env FIRST so all os.getenv() calls below can use it
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-campus-placement-2024-change-in-production'
)

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

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
# Local default: PostgreSQL on localhost (matches your current .env)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'campus_placement',
        'USER': 'postgres',
        'PASSWORD': os.getenv('DB_PASSWORD', '1234'),
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# If a DATABASE_URL env-var is set (Render, Railway, etc.) override the above
import dj_database_url
_db_url = os.getenv('DATABASE_URL')
if _db_url:
    DATABASES['default'] = dj_database_url.config(
        default=_db_url, conn_max_age=600, ssl_require=True
    )

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

# WhiteNoise compressed + cached storage for production
STORAGES = {
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
