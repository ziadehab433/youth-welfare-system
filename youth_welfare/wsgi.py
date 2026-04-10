import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'youth_welfare.settings.production'   # ← points to production
)

application = get_wsgi_application()