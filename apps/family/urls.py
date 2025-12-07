from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.family.views.faculty import FamilyFacultyAdminViewSet
from apps.family.views.super_dept import SuperDeptFamilyViewSet
from apps.family.views.student import StudentFamilyViewSet

router = DefaultRouter()
router.register(r'faculty', FamilyFacultyAdminViewSet, basename='family-admin')
router.register(r'student', StudentFamilyViewSet, basename='student')
router.register(r'super_dept', SuperDeptFamilyViewSet, basename='family-super-dept')
urlpatterns = [
    path('family/', include(router.urls)),
]