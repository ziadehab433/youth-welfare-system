from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.family.views.faculty import FamilyFacultyAdminViewSet

router = DefaultRouter()
router.register(r'family', FamilyFacultyAdminViewSet, basename='family-admin')

urlpatterns = [
    path('family/', include(router.urls)),
]