# apps/accounts/urls.py
from django.urls import path
from .views import LoginView , StudentSignUpView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', LoginView.as_view(), name='api_login'),

    path('signUp/', StudentSignUpView.as_view(), name='api_signUp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
