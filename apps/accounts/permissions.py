# apps/accounts/permissions.py

from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from .models import AdminsUser


# ============================================================
# Helper — safely extract JWT payload from request.auth
# Works with both:
#   - New CookieJWTAuthentication (request.auth = dict)
#   - Old simplejwt (request.auth = token object with .payload)
# ============================================================

def _get_payload(request):
    """Extract JWT payload dict from request.auth regardless of format."""
    token = getattr(request, 'auth', None)
    if token is None:
        return {}
    if isinstance(token, dict):
        return token                          # New cookie-based auth
    if hasattr(token, 'payload'):
        return token.payload                  # Old simplejwt compat
    return {}


# ============================================================
# Role-based Permission
# ============================================================

class IsRole(BasePermission):
    """
    Checks if the user has one of the allowed roles (for Admins or Students).
    Works with custom Admins model and JWT authentication.
    """
    def has_permission(self, request, view):
        user = request.user
        allowed_roles = getattr(view, 'allowed_roles', [])

        # Extract from JWT payload
        payload = _get_payload(request)
        user_type = payload.get('user_type')
        role = payload.get('role')

        # If student and 'student' or 'طالب' is allowed
        if user_type == 'student' and ('طالب' in allowed_roles or 'student' in allowed_roles):
            return True

        # If admin role matches allowed roles
        if role and (not allowed_roles or role in allowed_roles):
            return True

        # Fallback: check request.user directly
        if hasattr(user, 'role') and (not allowed_roles or user.role in allowed_roles):
            return True

        raise PermissionDenied("ليس لديك صلاحية الوصول لهذا المورد")


# ============================================================
# CRUD Permission Classes
# ============================================================

class HasCreatePermission(BasePermission):
    message = "ليس لديك صلاحية الإنشاء"

    def has_permission(self, request, view):
        return (request.user and
                request.user.is_authenticated and
                hasattr(request.user, 'has_create_permission') and
                request.user.has_create_permission())


class HasReadPermission(BasePermission):
    message = "ليس لديك صلاحية القراءة"

    def has_permission(self, request, view):
        return (request.user and
                request.user.is_authenticated and
                hasattr(request.user, 'has_read_permission') and
                request.user.has_read_permission())


class HasUpdatePermission(BasePermission):
    message = "ليس لديك صلاحية التعديل"

    def has_permission(self, request, view):
        return (request.user and
                request.user.is_authenticated and
                hasattr(request.user, 'has_update_permission') and
                request.user.has_update_permission())


class HasDeletePermission(BasePermission):
    message = "ليس لديك صلاحية الحذف"

    def has_permission(self, request, view):
        return (request.user and
                request.user.is_authenticated and
                hasattr(request.user, 'has_delete_permission') and
                request.user.has_delete_permission())


# ============================================================
# Decorator Functions
# ============================================================

def require_permission(permission_type):
    """
    Decorator to check if admin has specific permission.

    Usage:
        @require_permission('create')
        def my_action(self, request, pk=None):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            if hasattr(self_or_request, 'user'):
                request = self_or_request
                admin = request.user
            else:
                request = args[0] if args else kwargs.get('request')
                admin = request.user if request else None

            if not admin or not admin.is_authenticated:
                return Response({
                    "error": "غير مصرح لك بالدخول"
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not isinstance(admin, AdminsUser):
                return Response({
                    "error": "هذه الصلاحية متاحة للمسؤولين فقط"
                }, status=status.HTTP_403_FORBIDDEN)

            if not admin.has_permission(permission_type):
                permission_names = {
                    'create': 'الإنشاء',
                    'read': 'القراءة',
                    'update': 'التعديل',
                    'delete': 'الحذف'
                }
                return Response({
                    "error": f"ليس لديك صلاحية {permission_names.get(permission_type, permission_type)}"
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(self_or_request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_types):
    """
    Decorator to check if admin has any of the specified permissions.

    Usage:
        @require_any_permission('create', 'update')
        def my_action(self, request, pk=None):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            if hasattr(self_or_request, 'user'):
                request = self_or_request
                admin = request.user
            else:
                request = args[0] if args else kwargs.get('request')
                admin = request.user if request else None

            if not admin or not admin.is_authenticated:
                return Response({
                    "error": "غير مصرح لك بالدخول"
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not isinstance(admin, AdminsUser):
                return Response({
                    "error": "هذه الصلاحية متاحة للمسؤولين فقط"
                }, status=status.HTTP_403_FORBIDDEN)

            has_perm = any(admin.has_permission(perm) for perm in permission_types)

            if not has_perm:
                return Response({
                    "error": "ليس لديك أي من الصلاحيات المطلوبة"
                }, status=status.HTTP_403_FORBIDDEN)

            return view_func(self_or_request, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# Department Access Permission
# ============================================================

class HasDepartmentAccess(BasePermission):
    """
    Checks if the admin has access to the requested department.
    """
    message = "ليس لديك صلاحية الوصول لهذا القسم"

    def has_permission(self, request, view):
        payload = _get_payload(request)

        if not payload:
            return False

        user_type = payload.get('user_type')
        role = payload.get('role')

        # Students don't have department access
        if user_type == 'student':
            return False

        # Super admin has access to everything
        if role == 'مشرف النظام':
            return True

        # Get dept_ids from token
        token_dept_ids = payload.get('dept_ids', [])

        if not token_dept_ids:
            return False

        # Try to get requested dept_id from various sources
        requested_dept_id = (
            view.kwargs.get('dept_id') or
            view.kwargs.get('pk') or
            request.data.get('dept_id') or
            request.query_params.get('dept_id')
        )

        if not requested_dept_id:
            return True

        try:
            requested_dept_id = int(requested_dept_id)
        except (ValueError, TypeError):
            return False

        return requested_dept_id in token_dept_ids