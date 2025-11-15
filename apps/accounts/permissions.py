# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import AdminsUser



class IsStudent(BasePermission):
    """Allow only authenticated students."""
    def has_permission(self, request, view):
        token = request.auth
        if not token:
            return False

        # Try to get from the token payload (this always works for JWT)
        user_type = None
        if hasattr(token, 'payload'):
            user_type = token.payload.get('user_type')

        # Fallback if you ever attach user_type to request.user manually
        if not user_type:
            user_type = getattr(request.user, 'user_type', None)

        if user_type == 'student':
            return True

        raise PermissionDenied("هذا المورد مخصص للطلاب فقط")



class IsFacultyAdmin(BasePermission):
    """Allow only authenticated faculty admins."""
    def has_permission(self, request, view):
        token = request.auth
        if not token:
            return False
        user_type = getattr(request.user, 'user_type', None)
        if user_type == 'admin':
            return True
        if hasattr(token, 'payload') and token.payload.get('user_type') == 'admin':
            return True
        raise PermissionDenied("هذا المورد مخصص لمشرفي الكليات فقط")


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




class IsSuperAdmin(BasePermission):
    """Allow only super admins (مشرف النظام)."""
    
    def has_permission(self, request, view):
        user = request.user
        token = getattr(request, 'auth', None)
        
        if not user or not user.is_authenticated:
            return False
            
        role = None
        if token and hasattr(token, 'payload'):
            role = token.payload.get('role')
            
        if not role and hasattr(user, 'role'):
            role = user.role
            
        if role == 'مشرف النظام':
            return True
            
        raise PermissionDenied("هذا المورد مخصص لمشرف النظام فقط")