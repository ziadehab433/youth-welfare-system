# apps/accounts/views.py
from argparse import Action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
# from apps.solidarity.models import Students
import bcrypt
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from drf_spectacular.utils import extend_schema

from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from apps.accounts import serializers
from apps.accounts.models import Students
from apps.accounts.serializers import StudentSignUpSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import os
from django.core.files.storage import default_storage


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AdminsUser
from .serializers import AdminsUserSerializer
from .permissions import IsSuperAdmin

# --- Existing imports ---
from rest_framework.viewsets import ViewSet, GenericViewSet # ADD GenericViewSet
# --- New/Modified Imports ---
from apps.accounts.serializers import StudentDetailSerializer # ADD StudentDetailSerializer
from .permissions import IsStudent # ADD IsStudent permission

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





@extend_schema(
    tags=["Authentication"],
    description="Register a new student account with optional profile image.",
    request={'multipart/form-data': StudentSignUpSerializer},  
    responses={201: StudentSignUpSerializer}
)



class StudentSignUpView(APIView):
    permission_classes = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]  

    def post(self, request):
        serializer = StudentSignUpSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student = serializer.save()

        # JWT tokens
        refresh = RefreshToken()
        refresh['user_type'] = 'student'
        refresh['student_id'] = student.student_id
        refresh['name'] = student.name

        access = refresh.access_token
        access['user_type'] = 'student'
        access['student_id'] = student.student_id
        access['name'] = student.name

        # Build full URL for profile photo if exists
        profile_photo_url = None
        if student.profile_photo:
            profile_photo_url = request.build_absolute_uri(f'/media/{student.profile_photo}')

        return Response({
            "message": "Account created successfully",
            "student_id": student.student_id,
            "name": student.name,
            "profile_photo": profile_photo_url,  
            "refresh": str(refresh),
            "access": str(access),
        }, status=201)
    


# for profile photo update 


# # serializers.py
# class StudentDetailSerializer(serializers.ModelSerializer):
#     profile_photo_url = serializers.SerializerMethodField()

#     class Meta:
#         model = Students
#         fields = [
#             'student_id', 'name', 'email', 'faculty', 'gender',
#             'nid', 'uid', 'phone_number', 'address',
#             'acd_year', 'grade', 'major', 'profile_photo', 'profile_photo_url'
#         ]

#     def get_profile_photo_url(self, obj):
#         request = self.context.get('request')
#         if obj.profile_photo and request:
#             return request.build_absolute_uri(f'/media/{obj.profile_photo}')
#         return None









## Admin Users creation


class AdminManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Super Admin to manage other admins
    """
    queryset = AdminsUser.objects.all()
    serializer_class = AdminsUserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    # @action(detail=False, methods=['post'], url_path='create_admin')
    def create(self, request, *args, **kwargs):
        """Create new admin - Super admin assigns all permissions manually"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        
        return Response({
            'message': 'تم إنشاء المشرف بنجاح',
            'admin': AdminsUserSerializer(admin).data
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Delete admin"""
        instance = self.get_object()
        
        # Prevent deleting super admin
        if instance.role == 'مشرف النظام':
            return Response({
                'error': 'لا يمكن حذف مشرف النظام'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Prevent self-deletion
        if instance.admin_id == request.user.admin_id:
            return Response({
                'error': 'لا يمكنك حذف حسابك الخاص'
            }, status=status.HTTP_403_FORBIDDEN)
        
        self.perform_destroy(instance)
        return Response({
            'message': 'تم حذف المشرف بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)
    
    # @action(detail=True, methods=['post'])
    # def toggle_status(self, request, pk=None):
    #     """Toggle admin account status"""
    #     admin = self.get_object()
        
    #     if admin.role == 'مشرف النظام':
    #         return Response({
    #             'error': 'لا يمكن تغيير حالة مشرف النظام'
    #         }, status=status.HTTP_403_FORBIDDEN)
        
    #     admin.acc_status = 'inactive' if admin.acc_status == 'active' else 'active'
    #     admin.save()
        
    #     return Response({
    #         'message': f'تم {"تفعيل" if admin.acc_status == "active" else "تعطيل"} الحساب',
    #         'status': admin.acc_status
    #     })
    
    @action(detail=True, methods=['patch'])
    def update_permissions(self, request, pk=None):
        """Update only admin permissions"""
        admin = self.get_object()
        
        if admin.role == 'مشرف النظام':
            return Response({
                'error': 'لا يمكن تغيير صلاحيات مشرف النظام'
            }, status=status.HTTP_403_FORBIDDEN)
        
        admin.can_create = request.data.get('can_create', admin.can_create)
        admin.can_update = request.data.get('can_update', admin.can_update)
        admin.can_read = request.data.get('can_read', admin.can_read)
        admin.can_delete = request.data.get('can_delete', admin.can_delete)
        admin.save()
        
        return Response({
            'message': 'تم تحديث الصلاحيات بنجاح',
            'permissions': {
                'can_create': admin.can_create,
                'can_update': admin.can_update,
                'can_read': admin.can_read,
                'can_delete': admin.can_delete
            }
        })


class StudentProfileViewSet(GenericViewSet):
    """
    ViewSet for students to view and update their own profile details.
    Uses the student_id from the JWT token payload.
    """
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get_object(self):
        """Custom method to get the currently authenticated student."""
        try:
            student_id = self.request.auth.payload.get('student_id')
            if not student_id:
                 raise Students.DoesNotExist # Treat as not found
            
            return Students.objects.get(student_id=student_id)
        except Students.DoesNotExist:
            raise AuthenticationFailed("User not found or token missing 'student_id'")


    @extend_schema(
        tags=["Student Profile"],
        description="Retrieve the authenticated student's profile details.",
        responses={200: StudentDetailSerializer}
    )
    def list(self, request, *args, **kwargs):
        """Handles GET /accounts/profile/ to retrieve the current user's details."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)