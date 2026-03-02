from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, StudentSignUpView, AdminManagementViewSet, StudentProfileViewSet 
from rest_framework_simplejwt.views import TokenRefreshView
from . import google_auth_views
from . import views
from . import password_reset_views

# Create router for viewsets
router = DefaultRouter()
router.register(r'admin_management', AdminManagementViewSet, basename='admin_management')
router.register(r'profile', StudentProfileViewSet, basename='student-profile') 

urlpatterns = [
    path('login/', LoginView.as_view(), name='api_login'),
    path('signUp/', StudentSignUpView.as_view(), name='api_signUp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    

    path('google/init/', google_auth_views.GoogleOAuthInitiateView.as_view(), name='google_init'),
    path('google/login/', google_auth_views.GoogleOAuthLoginView.as_view(), name='google_login'),
    path('google/signup/', google_auth_views.GoogleOAuthSignUpView.as_view(), name='google_signup'),
    path('google/callback/', google_auth_views.GoogleOAuthCallbackView.as_view(), name='google_callback'),
    
    # Password Reset URLs
    path('password-reset/', password_reset_views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', password_reset_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Include router URLs (This includes admin_management/ and profile/)
    path('', include(router.urls)),
]