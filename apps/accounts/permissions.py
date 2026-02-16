# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from .models import AdminsUser


# apps/accounts/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from .models import AdminsUser


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



##########

class HasCreatePermission(BasePermission):
    """Permission class to check create permission"""
    
    message = "ليس لديك صلاحية الإنشاء"
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'has_create_permission') and
                request.user.has_create_permission())


class HasReadPermission(BasePermission):
    """Permission class to check read permission"""
    
    message = "ليس لديك صلاحية القراءة"
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'has_read_permission') and
                request.user.has_read_permission())


class HasUpdatePermission(BasePermission):
    """Permission class to check update permission"""
    
    message = "ليس لديك صلاحية التعديل"
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'has_update_permission') and
                request.user.has_update_permission())


class HasDeletePermission(BasePermission):
    """Permission class to check delete permission"""
    
    message = "ليس لديك صلاحية الحذف"
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'has_delete_permission') and
                request.user.has_delete_permission())


# ============ Decorator Functions ============

def require_permission(permission_type):
    """
    Decorator to check if admin has specific permission
    
    Usage:
        @require_permission('create')
        def my_action(self, request, pk=None):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            # Handle both function views and class-based views
            if hasattr(self_or_request, 'user'):
                # Function-based view
                request = self_or_request
                admin = request.user
            else:
                # Class-based view (ViewSet)
                request = args[0] if args else kwargs.get('request')
                admin = request.user if request else None
            
            if not admin or not admin.is_authenticated:
                return Response({
                    "error": "غير مصرح لك بالدخول"
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user is AdminsUser (not student)
            if not isinstance(admin, AdminsUser):
                return Response({
                    "error": "هذه الصلاحية متاحة للمسؤولين فقط"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check specific permission
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
    Decorator to check if admin has any of the specified permissions
    
    Usage:
        @require_any_permission('create', 'update')
        def my_action(self, request, pk=None):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            # Handle both function views and class-based views
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
            
            has_permission = any(admin.has_permission(perm) for perm in permission_types)
            
            if not has_permission:
                return Response({
                    "error": "ليس لديك أي من الصلاحيات المطلوبة"
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(self_or_request, *args, **kwargs)
        return wrapper
    return decorator


class HasDepartmentAccess(BasePermission):
    """
    Checks if the admin has access to the requested department.
    
    Usage in views:
        permission_classes = [IsAuthenticated, HasDepartmentAccess]
        
    The view must provide dept_id via:
        - URL kwargs (e.g., /departments/<dept_id>/...)
        - request.data['dept_id']
        - request.query_params['dept_id']
    """
    message = "ليس لديك صلاحية الوصول لهذا القسم"

    def has_permission(self, request, view):
        token = getattr(request, 'auth', None)
        if not token:
            return False

        payload = getattr(token, 'payload', {})
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
            # No specific department requested — 
            # let view handle filtering
            return True

        try:
            requested_dept_id = int(requested_dept_id)
        except (ValueError, TypeError):
            return False

        return requested_dept_id in token_dept_ids