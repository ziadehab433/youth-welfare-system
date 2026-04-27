"""
Production settings - extends base.py
"""
from .base import *   # noqa: F401, F403

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://193.227.34.82')

# ── CORS ──────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://172.1.50.81,http://193.227.34.82',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
CORS_ALLOW_CREDENTIALS = True    # ← CRITICAL for cookies

# ── Cookie Auth ───────────────────────────────────────
# Set to True AFTER you add SSL certificate
AUTH_COOKIE_SECURE = False   # ← Change to True when HTTPS is ready

# ── CSRF ──────────────────────────────────────────────
# Also change to True AFTER SSL
CSRF_COOKIE_SECURE  = False   # ← Change to True when HTTPS is ready
SESSION_COOKIE_SECURE = False # ← Change to True when HTTPS is ready

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://172.1.50.81,http://193.227.34.82',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

USE_X_ACCEL_REDIRECT = True

# Strict CSP for production
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'",),
    "style-src":  ("'self'", "'unsafe-inline'"),
}

# Production Swagger servers
SPECTACULAR_SETTINGS['SERVERS'] = [
    {'url': 'http://172.1.50.81',    'description': 'Production (LAN)'},
    {'url': 'http://193.227.34.82',  'description': 'Production (Public)'},
    {'url': 'http://localhost:8000', 'description': 'Local Dev'},
]