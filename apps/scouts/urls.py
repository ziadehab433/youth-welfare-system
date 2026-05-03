from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.student import StudentScoutViewSet
from .views.faculty_admin import FacultyAdminScoutViewSet
from .views.dept_manager import DeptManagerScoutViewSet

router = DefaultRouter()
router.register(r'student', StudentScoutViewSet, basename='student-scout')
router.register(r'faculty', FacultyAdminScoutViewSet, basename='faculty-scout')
router.register(r'dept', DeptManagerScoutViewSet, basename='dept-scout')

urlpatterns = [
    path('', include(router.urls)),
]