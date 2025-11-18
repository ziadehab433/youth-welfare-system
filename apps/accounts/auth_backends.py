# apps/accounts/auth_backends.py
from django.contrib.auth.backends import BaseBackend
from apps.accounts.models import AdminsUser
import bcrypt
from django.contrib.auth.hashers import check_password , make_password


class AdminsBackend(BaseBackend):
    """
    Custom authentication backend for AdminsUser model (DB-first)
    """
    def authenticate(self, request, username=None, password=None, **kwargs):

        user = AdminsUser.objects.filter(email=username).first()
        if not user:
            return None

        stored = user.password

        # New Django-hashed passwords
        if stored.startswith("pbkdf2_"):
            if check_password(password, stored):
                return user
            return None

        #  OLD bcrypt passwords
        try:
            if bcrypt.checkpw(password.encode(), stored.encode()):
                # Migrate old password into Django format
                user.password = make_password(password)
                user.save()
                return user
        except:
            pass

        return None

    def get_user(self, user_id):
        try:
            return AdminsUser.objects.get(pk=user_id)
        except AdminsUser.DoesNotExist:
            return None
