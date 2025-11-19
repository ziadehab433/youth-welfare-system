# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import AdminsUser


# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied



class IsRole(BasePermission):
    """
    Checks if the user has one of the allowed roles (for Admins or Students).
    Works with custom Admins model and JWT authentication.
    """
    def has_permission(self, request, view):
        user = request.user
        token = getattr(request, 'auth', None)
        allowed_roles = getattr(view, 'allowed_roles', [])

        # 🔹 Extract info from token (JWT)
        payload = getattr(token, 'payload', {}) if token else {}
        user_type = payload.get('user_type')
        role = payload.get('role')

        #  If student and 'طالب' allowed
        if user_type == 'student' and ('طالب' in allowed_roles or 'student' in allowed_roles):
            return True

        #  If admin role matches allowed roles
        if role and (not allowed_roles or role in allowed_roles):
            return True

        # fallback: check request.user directly
        if hasattr(user, 'role') and (not allowed_roles or user.role in allowed_roles):
            return True

        raise PermissionDenied("ليس لديك صلاحية الوصول لهذا المورد")




