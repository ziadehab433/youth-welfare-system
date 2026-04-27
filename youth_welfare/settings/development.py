# youth_welfare/settings/development.py

from .base import *

ALLOWED_HOSTS = ['*']

FRONTEND_URL = 'http://localhost:3000'

# ── CORS ──────────────────────────────────────────────
# In dev, you CANNOT use CORS_ALLOW_ALL_ORIGINS=True with credentials.
# You must whitelist origins explicitly.
CORS_ALLOW_ALL_ORIGINS   = False                        # ← CHANGED
CORS_ALLOWED_ORIGINS     = [
    'http://localhost:3000',       # Next.js frontend
    'http://localhost:8000',       # Swagger UI (localhost)
    'http://127.0.0.1:8000',      # Swagger UI (127.0.0.1)  ← THIS FIXES IT
]
CORS_ALLOW_CREDENTIALS   = True                         # ← CRITICAL for cookies

# ── Cookie Auth ───────────────────────────────────────
AUTH_COOKIE_SECURE = False   # HTTP in dev — no SSL

# ── CSRF ──────────────────────────────────────────────
CSRF_COOKIE_SECURE  = False
SESSION_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

USE_X_ACCEL_REDIRECT = False

# ... keep the rest of your development.py as-is ...

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