from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    RefreshTokenView,
    LogoutView,
    LogoutAllDevicesView,
    StudentSignUpView,
    CSRFTokenView,
    AdminManagementViewSet,
    StudentProfileViewSet,
)
from . import google_auth_views
from . import password_reset_views

# Router for viewsets
router = DefaultRouter()
router.register(r'admin_management', AdminManagementViewSet, basename='admin_management')
router.register(r'profile', StudentProfileViewSet, basename='student-profile')

urlpatterns = [
    # ── Auth (cookie-based) ─────────────────────────────────
    path('login/',          LoginView.as_view(),           name='api_login'),
    path('token/refresh/',  RefreshTokenView.as_view(),    name='token_refresh'),
    path('logout/',         LogoutView.as_view(),          name='api_logout'),
    path('logout/all/',     LogoutAllDevicesView.as_view(),name='api_logout_all'),
    path('csrf/',           CSRFTokenView.as_view(),       name='api_csrf'),

    # ── Registration ────────────────────────────────────────
    path('signUp/',         StudentSignUpView.as_view(),   name='api_signUp'),

    # ── Google OAuth ────────────────────────────────────────
    path('google/init/',     google_auth_views.GoogleOAuthInitiateView.as_view(),  name='google_init'),
    path('google/login/',    google_auth_views.GoogleOAuthLoginView.as_view(),     name='google_login'),
    path('google/signup/',   google_auth_views.GoogleOAuthSignUpView.as_view(),    name='google_signup'),
    path('google/callback/', google_auth_views.GoogleOAuthCallbackView.as_view(),  name='google_callback'),

    # ── Password Reset ──────────────────────────────────────
    path('password-reset/',         password_reset_views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', password_reset_views.PasswordResetConfirmView.as_view(),  name='password_reset_confirm'),

    # ── Viewsets (admin management, profile) ────────────────
    path('', include(router.urls)),
]