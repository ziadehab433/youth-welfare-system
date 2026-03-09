from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.solidarity.views.student import StudentSolidarityViewSet
from apps.solidarity.views.faculty import FacultyAdminSolidarityViewSet
from apps.solidarity.views.super_dept import SuperDeptSolidarityViewSet
from apps.solidarity.views.secure_files import SecureSolidarityFileViewSet, SecureProfileImageViewSet

from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'student', StudentSolidarityViewSet, basename='student-solidarity')
router.register(r'faculty', FacultyAdminSolidarityViewSet, basename='faculty-solidarity')
router.register(r'super_dept', SuperDeptSolidarityViewSet, basename='super-dept-solidarity')

# Secure file access routes
secure_router = DefaultRouter()
secure_router.register(r'solidarity', SecureSolidarityFileViewSet, basename='secure-solidarity-files')
secure_router.register(r'students', SecureProfileImageViewSet, basename='secure-profile-images')

urlpatterns = [
    path('solidarity/', include(router.urls)),
    path('files/', include(secure_router.urls)),
]

# In development, serve media files directly
# In production, Nginx will handle public files and X-Accel-Redirect for private files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)