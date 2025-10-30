# apps/accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from apps.solidarity.models import Students
import bcrypt
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=["Authentication"],
    description="Login and get JWT tokens",
    request=TokenObtainPairSerializer,
    responses={200: TokenObtainPairSerializer}
)
class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        identifier = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')
        if not identifier or not password:
            return Response({'detail': 'email and password required'}, status=400)

        # 1) Try to authenticate admin via custom backend
        user = authenticate(request, username=identifier, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = 'admin'
            refresh['admin_id'] = user.admin_id

            refresh['role'] = user.role
            refresh['name'] = user.name
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_type': 'admin',
                'admin_id': user.admin_id,

                'role': user.role,
                'name': user.name,
            })

  
        # 2) Fallback: try student manually
        student = Students.objects.filter(email=identifier).first()
        
        if student and bcrypt.checkpw(password.encode(), student.password.encode()):
            # Create a token manually instead of for_user()
            refresh = RefreshToken()
            refresh['user_type'] = 'student'
            refresh['student_id'] = student.student_id
            refresh['name'] = student.name

            access_token = refresh.access_token
            access_token['user_type'] = 'student'
            access_token['student_id'] = student.student_id
            access_token['name'] = student.name
            
            return Response({
                'refresh': str(refresh),
                'access': str(access_token),         
                'user_type': 'student',
                'student_id': student.student_id,
                'name': student.name,
            })
        raise AuthenticationFailed('Invalid credentials')




@extend_schema(
    tags=["Authentication"],
    description="Use refresh token to get a new access token",
    request=TokenRefreshSerializer,
    responses={200: TokenRefreshSerializer}
)
class RefreshTokenView(TokenRefreshView):
    """Handles refreshing JWT access token using a refresh token."""
    pass