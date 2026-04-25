# youth_welfare/settings/development.py

from .base import *

# ── Dev-specific overrides ────────────────────────────────────
ALLOWED_HOSTS = ['*']

FRONTEND_URL = 'http://localhost:3000' 

CORS_ALLOW_ALL_ORIGINS = True

USE_X_ACCEL_REDIRECT = False

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": (
        "'self'", "'unsafe-inline'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
    ),
    "style-src": (
        "'self'", "'unsafe-inline'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
    ),
    "img-src":  ("'self'", "data:", "https:"),
    "font-src": ("'self'", "https://cdn.jsdelivr.net"),
}

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

SPECTACULAR_SETTINGS['SERVERS'] = [
    {'url': 'http://localhost:8000',  'description': 'Local Dev'},
    {'url': 'http://127.0.0.1:8000', 'description': 'Local Dev (127)'},
]

# ── Override logging for dev (simple console only) ────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {name} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',  # ← FORCE stdout not stderr
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}