"""
Base settings shared between development and production.
"""

import os
from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

AUTH_USER_MODEL = 'accounts.AdminsUser'

AUTHENTICATION_BACKENDS = [
    'apps.accounts.auth_backends.AdminsBackend',
    'django.contrib.auth.backends.ModelBackend',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework_simplejwt',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework',
    'drf_spectacular',
    'youth_welfare',
    'apps.event',
    'corsheaders',
    'apps.solidarity',
    'apps.family',
    'apps.accounts',
    'apps.accounts.schema',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'apps.accounts.middleware.EnsureCsrfCookieMiddleware',   # ← NEW
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.SecurityHeadersMiddleware',
    'apps.accounts.middleware.AuditLoggingMiddleware',
    'apps.accounts.middleware.RateLimitMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'youth-welfare-cache',
        'OPTIONS': {'MAX_ENTRIES': 100000000}
    }
}

ROOT_URLCONF = 'youth_welfare.urls'
WSGI_APPLICATION = 'youth_welfare.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.debug',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT', cast=int),
    }
}

ENCRYPTION_KEY = config('ENCRYPTION_KEY', default=None)
if not ENCRYPTION_KEY:
    raise ValueError(
        "ENCRYPTION_KEY not found. Generate: "
        "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

ENCRYPTED_FIELDS = {
    'Students': ['nid', 'uid', 'phone_number', 'address'],
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.CookieJWTAuthentication",   # ← CHANGED
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=150),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
#     "ROTATE_REFRESH_TOKENS": False,
#     "BLACKLIST_AFTER_ROTATION": True,
#     "ALGORITHM": "HS256",
#     "SIGNING_KEY": config('SECRET_KEY'),
#     "AUTH_HEADER_TYPES": ("Bearer",),
#     "USER_ID_FIELD": "admin_id",
#     "USER_ID_CLAIM": "admin_id",
# }

# ── HttpOnly Cookie Auth Settings ──────────────────────────────
# These are overridden per-environment in development.py / production.py
AUTH_COOKIE_SECURE    = False    # overridden in production.py → True after SSL
AUTH_COOKIE_SAMESITE  = 'Lax'
AUTH_COOKIE_HTTPONLY   = True


# 4. CSRF — ensure these are set:
CSRF_COOKIE_HTTPONLY  = False    # ← CHANGED to False! 
#   The frontend needs to READ the csrftoken cookie via JS 
#   to send it in the X-CSRFToken header.
#   This is safe — CSRF token is not a secret, it's a double-submit check.

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SAMESITE = 'Lax'


# 5. CORS — add credentials support (needed for cookies to work cross-origin):
CORS_ALLOW_CREDENTIALS = True    # ← ADD THIS

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, 'media', 'private')
PRIVATE_MEDIA_URL = '/protected/'
PUBLIC_MEDIA_ROOT = os.path.join(BASE_DIR, 'media', 'public')

os.makedirs(PRIVATE_MEDIA_ROOT, exist_ok=True)
os.makedirs(PUBLIC_MEDIA_ROOT, exist_ok=True)

RATE_LIMIT_CONFIG = {
    'auth': {
        'max_requests': 20,
        'window_seconds': 3600,
        'endpoints': [
            '/api/accounts/login/',
            '/api/accounts/auth/google/login/',
        ]
    },
    'signup': {
        'max_requests': 10,
        'window_seconds': 3600,
        'endpoints': [
            '/api/accounts/signup/',
            '/api/accounts/auth/google/signup/',
        ]
    },
    'read': {
        'max_requests': 200,
        'window_seconds': 3600,
        'endpoints': [
            '/api/accounts/profile/',
            '/api/accounts/admins/',
            '/api/solidarity/student/status/',
        ]
    },
    'write': {
        'max_requests': 30,
        'window_seconds': 3600,
        'endpoints': [
            '/api/accounts/profile/update_profile/',
        ]
    },
    'default': {
        'max_requests': 100,
        'window_seconds': 3600,
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',  # ← writes to stderr
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'audit_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'audit.log'),
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024 * 1024 * 20,
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

SPECTACULAR_SETTINGS = {
    'TITLE': 'Youth Welfare API',
    'DESCRIPTION': 'API documentation for the Solidarity Subsystem',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SECURITY_SCHEMES': {
        'Bearer': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        },
    },
    "SCHEMA_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.CustomJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayRequestDuration': True,
    },
}

GOOGLE_CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID', default=None)
GOOGLE_CLIENT_SECRET = config('GOOGLE_OAUTH_CLIENT_SECRET', default=None)
GOOGLE_REDIRECT_URI = config(
    'GOOGLE_OAUTH_REDIRECT_URI',
    default='http://localhost:8000/api/auth/google/callback/'
)

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Google OAuth credentials not fully configured")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
PASSWORD_RESET_TIMEOUT = 1200

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIGRATION_MODULES = {
    'event': None,
    'family': None,
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

FONTS_DIR = os.path.join(BASE_DIR, 'static', 'fonts')
if not os.path.exists(FONTS_DIR):
    os.makedirs(FONTS_DIR, exist_ok=True)

# SECURE_BROWSER_XSS_FILTER = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'



import sentry_sdk

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=None),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)