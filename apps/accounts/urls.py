from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, StudentSignUpView, AdminManagementViewSet, StudentProfileViewSet 
from rest_framework_simplejwt.views import TokenRefreshView

# Create router for viewsets
router = DefaultRouter()
router.register(r'admin_management', AdminManagementViewSet, basename='admin_management')
router.register(r'profile', StudentProfileViewSet, basename='student-profile') 

urlpatterns = [
    path('login/', LoginView.as_view(), name='api_login'),
    path('signUp/', StudentSignUpView.as_view(), name='api_signUp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Include router URLs (This includes admin_management/ and profile/)
    path('', include(router.urls)),
]