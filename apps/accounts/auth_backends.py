# apps/accounts/auth_backends.py
from django.contrib.auth.backends import BaseBackend
from apps.accounts.models import AdminsUser
import bcrypt

class AdminsBackend(BaseBackend):
    """
    Custom authentication backend for AdminsUser model (DB-first)
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        try:
            user = AdminsUser.objects.filter(email=username).first()
        except AdminsUser.DoesNotExist:
            return None
        if not user or not user.password:
            return None

        stored_hash = user.password.encode() if isinstance(user.password, str) else user.password
        if bcrypt.checkpw(password.encode(), stored_hash):
            return user
        return None

    def get_user(self, user_id):
        try:
            return AdminsUser.objects.get(pk=user_id)
        except AdminsUser.DoesNotExist:
            return None
