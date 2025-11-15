from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, StudentSignUpView, AdminManagementViewSet
from rest_framework_simplejwt.views import TokenRefreshView

# Create router for viewsets
router = DefaultRouter()
router.register(r'admin_management', AdminManagementViewSet, basename='admin_management')

urlpatterns = [
    path('login/', LoginView.as_view(), name='api_login'),
    path('signUp/', StudentSignUpView.as_view(), name='api_signUp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Include router URLs
    path('', include(router.urls)),
]