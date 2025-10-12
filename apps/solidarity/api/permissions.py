from rest_framework.permissions import BasePermission

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'student_id')

class IsAnyAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'admin_id')

class IsFacultyAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'admin_role', None) == 'FACULTY_ADMIN'

class IsSuperOrDept(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'admin_role', None) in ['SUPER_ADMIN', 'DEPT_ADMIN']