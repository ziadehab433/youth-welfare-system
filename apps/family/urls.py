from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.family.views.faculty import (
    FamilyFacultyAdminViewSet,
    FacultyEventApprovalViewSet,
    FamilyMembersViewSet,
)
from apps.family.views.super_dept import SuperDeptFamilyViewSet
from apps.family.views.student import StudentFamilyViewSet

router = DefaultRouter()

router.register(r'faculty', FamilyFacultyAdminViewSet, basename='family_admin')
router.register(r'faculty_events', FacultyEventApprovalViewSet, basename='faculty_events')
router.register(r'faculty_members', FamilyMembersViewSet, basename='faculty_members')

router.register(r'student', StudentFamilyViewSet, basename='student')
router.register(r'super_dept', SuperDeptFamilyViewSet, basename='family_super_dept')

urlpatterns = [
    path('family/', include(router.urls)),
]
