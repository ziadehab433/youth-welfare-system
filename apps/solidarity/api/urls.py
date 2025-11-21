from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.solidarity.api.views.student import StudentSolidarityViewSet
from apps.solidarity.api.views.faculty import FacultyAdminSolidarityViewSet
from apps.solidarity.api.views.super_dept import SuperDeptSolidarityViewSet

from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'student', StudentSolidarityViewSet, basename='student-solidarity')
router.register(r'faculty', FacultyAdminSolidarityViewSet, basename='faculty-solidarity')
router.register(r'super_dept', SuperDeptSolidarityViewSet, basename='super-dept-solidarity')

urlpatterns = [
    path('solidarity/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
