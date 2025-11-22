from argparse import Action
from asyncio.log import logger
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
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

from apps.solidarity.models import Faculties
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AdminsUser
from .serializers import AdminsUserSerializer
from .permissions import IsRole
# --- Existing imports ---
from rest_framework.viewsets import ViewSet, GenericViewSet # ADD GenericViewSet
# --- New/Modified Imports ---
from apps.accounts.serializers import StudentDetailSerializer, StudentSignUpSerializer, StudentUpdateSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
@extend_schema(
    tags=["Authentication"],
    description="Login and get JWT tokens",
    request=TokenObtainPairSerializer,
    responses={200: TokenObtainPairSerializer}
)
class LoginView(APIView):
    permission_classes = []
    
    def get_faculty_info(self, faculty_id):
        """Helper method to get faculty information"""
        if not faculty_id:
            return None, None
            
        try:
            faculty = Faculties.objects.get(faculty_id=faculty_id)
            return faculty_id, faculty.name  
        except Faculties.DoesNotExist:
            return faculty_id, None

    def post(self, request):
        identifier = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')
        if not identifier or not password:
            return Response({'detail': 'email and password required'}, status=400)

        # 1) Try to authenticate admin via custom backend
        user = authenticate(request, username=identifier, password=password)
        if user:
            # CHECK: Prevent inactive admins from logging in
            if hasattr(user, 'acc_status') and user.acc_status != 'active':
                logger.warning(f"Login attempt by inactive admin: {user.admin_id}")
                #  Return Response and STOP execution here
                return Response(
                    {
                        'detail': f'حسابك غير مفعل. الحالة الحالية: {user.acc_status}',
                        'status': user.acc_status
                    }, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Only reach here if account_status is 'active'
            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = 'admin'
            refresh['admin_id'] = user.admin_id
            refresh['role'] = user.role
            refresh['name'] = user.name
            
            # Get the access token from refresh token
            access_token = refresh.access_token
            access_token['user_type'] = 'admin'
            access_token['admin_id'] = user.admin_id
            access_token['role'] = user.role
            access_token['name'] = user.name
            
            response_data = {
                'refresh': str(refresh),
                'access': str(access_token),
                'user_type': 'admin',
                'admin_id': user.admin_id,
                'role': user.role,
                'name': user.name,
            }
            
            # Add faculty_id and faculty_name for specific admin roles
            if user.role in ['مسؤول كلية', 'مدير كلية']:
                faculty_id, faculty_name = self.get_faculty_info(user.faculty_id)
                
                # Add to refresh token payload
                refresh['faculty_id'] = faculty_id
                refresh['faculty_name'] = faculty_name
                
                # Add to access token payload
                access_token['faculty_id'] = faculty_id
                access_token['faculty_name'] = faculty_name
                
                # Add to response
                response_data['faculty_id'] = faculty_id
                response_data['faculty_name'] = faculty_name
                
            # Update tokens in response after modifications
            response_data['refresh'] = str(refresh)
            response_data['access'] = str(access_token)
                
            return Response(response_data, status=status.HTTP_200_OK)

        # 2) Fallback: try student manually
        student = Students.objects.filter(email=identifier).first()
        
        if student and bcrypt.checkpw(password.encode(), student.password.encode()):
            # Get faculty info for student
            faculty_id, faculty_name = self.get_faculty_info(student.faculty_id)
            
            # Create a token manually
            refresh = RefreshToken()
            refresh['user_type'] = 'student'
            refresh['student_id'] = student.student_id
            refresh['name'] = student.name
            refresh['faculty_id'] = faculty_id
            refresh['faculty_name'] = faculty_name

            access_token = refresh.access_token
            access_token['user_type'] = 'student'
            access_token['student_id'] = student.student_id
            access_token['name'] = student.name
            access_token['faculty_id'] = faculty_id
            access_token['faculty_name'] = faculty_name
            
            return Response({
                'refresh': str(refresh),
                'access': str(access_token),         
                'user_type': 'student',
                'student_id': student.student_id,
                'name': student.name,
                'faculty_id': faculty_id,
                'faculty_name': faculty_name,
            }, status=status.HTTP_200_OK)
        
        #  If no user or student found, return invalid credentials
        return Response(
            {'detail': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


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
    permission_classes = [ IsAuthenticated,IsRole]
    allowed_roles = ['مشرف النظام']
    # ----------- CREATE ADMIN -----------
    def create(self, request, *args, **kwargs):
        """
        Create a new admin, including receiving array of strings in dept_fac_ls
        Example JSON:
        {
            "name": "Omar",
            "email": "...",
            "password": "...",
            "role": "مدير ادارة",
            "dept": 3,
            "dept_fac_ls": ["نشاط رياضي", "نشاط علمي"]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()

        return Response({
            'message': 'تم إنشاء المشرف بنجاح',
            'admin': AdminsUserSerializer(admin).data
        }, status=status.HTTP_201_CREATED)

    # ----------- UPDATE ADMIN -----------
    def update(self, request, *args, **kwargs):
        """
        Full update admin, including updating dept_fac_ls (array of strings)
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()

        return Response({
            "message": "تم تحديث بيانات المشرف بنجاح",
            "admin": AdminsUserSerializer(admin).data
        })

    # ----------- PARTIAL UPDATE (PATCH) -----------
    def partial_update(self, request, *args, **kwargs):
        """
        Handles updating only specific fields (e.g. dept_fac_ls alone)
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ----------- DELETE ADMIN -----------
    def destroy(self, request, *args, **kwargs):
        """Delete admin safely"""
        instance = self.get_object()

        if instance.role == 'مشرف النظام':
            return Response(
                {"error": "لا يمكن حذف مشرف النظام"},
                status=status.HTTP_403_FORBIDDEN
            )

        if instance.admin_id == request.user.admin_id:
            return Response(
                {"error": "لا يمكنك حذف حسابك الخاص"},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(instance)
        return Response({"message": "تم حذف المشرف بنجاح"}, status=status.HTTP_204_NO_CONTENT)

    # ----------- UPDATE PERMISSIONS ONLY -----------
    @action(detail=True, methods=['patch'])
    def update_permissions(self, request, pk=None):
        """Update only admin permissions"""
        admin = self.get_object()

        if admin.role == 'مشرف النظام':
            return Response(
                {"error": "لا يمكن تغيير صلاحيات مشرف النظام"},
                status=status.HTTP_403_FORBIDDEN
            )

        admin.can_create = request.data.get('can_create', admin.can_create)
        admin.can_update = request.data.get('can_update', admin.can_update)
        admin.can_read = request.data.get('can_read', admin.can_read)
        admin.can_delete = request.data.get('can_delete', admin.can_delete)
        admin.save()

        return Response({
            "message": "تم تحديث الصلاحيات بنجاح",
            "permissions": {
                "can_create": admin.can_create,
                "can_update": admin.can_update,
                "can_read": admin.can_read,
                "can_delete": admin.can_delete
            }
        })


class StudentProfileViewSet(GenericViewSet):
    """
    ViewSet for students to view and update their own profile details.
    Uses the student_id from the JWT token payload.
    """
    serializer_class = StudentDetailSerializer
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ['student']
    parser_classes = [MultiPartParser, FormParser] 
    
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
    
    def get_object(self):
        try:
            student_id = self.request.auth.payload.get('student_id')
            if not student_id:
                    raise Students.DoesNotExist
            
            return Students.objects.get(student_id=student_id)
        except Students.DoesNotExist:
            raise AuthenticationFailed("User not found or token missing 'student_id'")

    @extend_schema(
        tags=["Student Profile"],
        description="Update the authenticated student's profile details.",
        request=StudentUpdateSerializer,
        responses={200: StudentDetailSerializer}
    )
   
    @action(detail=False, methods=['patch'])
    def update_profile(self, request, *args, **kwargs):
        """Handles PATCH /accounts/profile/update_profile/ to update the current user's details."""
        instance = self.get_object()
        serializer = StudentUpdateSerializer(
            instance, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        
        detail_serializer = self.get_serializer(updated_instance, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)