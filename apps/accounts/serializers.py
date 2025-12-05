# apps/accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate

from rest_framework import serializers
from apps.accounts.models import Students
import bcrypt

import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from apps.solidarity.models import Departments, Faculties

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    
class UnifiedTokenObtainSerializer(TokenObtainPairSerializer):
    """
    This serializer is not tied to a single user model — we will call authenticate() manually
    in the view and then generate tokens. But keeping this allows for claims customization.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # add claims that are useful
        token['role'] = getattr(user, 'role', None)
        token['user_type'] = getattr(user, 'user_type', None) if hasattr(user, 'user_type') else 'admin'
        token['name'] = getattr(user, 'name', None)
        return token




class StudentSignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile_image = serializers.FileField(write_only=True, required=False, allow_null=True)  # Add this

    class Meta:
        model = Students
        fields = [
            'name', 'email', 'password', 'faculty', 'gender',
            'nid', 'uid', 'phone_number', 'address',
            'acd_year', 'grade', 'major', 'profile_image'  # Add profile_image
        ]

    def create(self, validated_data):
        # Extract image if exists
        profile_image = validated_data.pop('profile_image', None)
        
        # Hash password
        raw_password = validated_data.pop("password")
        hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
        validated_data["password"] = hashed

        # Create student
        student = Students.objects.create(**validated_data)

        # Handle image upload after student is created (so we have student_id)
        if profile_image:
            # Get file extension
            ext = os.path.splitext(profile_image.name)[1]
            # Create path: uploads/students/{student_id}/image{ext}
            file_path = f'uploads/students/{student.student_id}/image{ext}'
            
            # Save file to media directory
            saved_path = default_storage.save(file_path, ContentFile(profile_image.read()))
            
            # Update student's profile_photo field with the path
            student.profile_photo = saved_path
            student.save()

        return student
    



    # to retrive std details 


# serializers.py
class StudentDetailSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Students
        fields = [
            'student_id', 'name', 'email', 'faculty', 'gender',
            'nid', 'uid', 'phone_number', 'address',
            'acd_year', 'grade', 'major', 'profile_photo_url'
        ]
    def get_profile_photo_url(self, obj) -> str:
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(f'/media/{obj.profile_photo}')
        return None
    

    # register admis

from rest_framework import serializers
from .models import AdminsUser

class AdminsUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True)
    
    faculty = serializers.PrimaryKeyRelatedField(
    queryset=Faculties.objects.all(),
    required=False,
    allow_null=True
    )
    dept = serializers.PrimaryKeyRelatedField(
        queryset=Departments.objects.all(),
        required=False,
        allow_null=True
    )    
    dept_fac_ls = serializers.ListField(
    child=serializers.CharField(),
    required=False,
    allow_null=True
)


    
    class Meta:
        model = AdminsUser
        fields = [
            'admin_id', 'name', 'email', 'password', 'faculty', 'faculty_name',
            'dept', 'dept_name', 'role', 'acc_status', 'can_create', 
            'can_update', 'can_read', 'can_delete', 'created_at',
            "dept_fac_ls"
        ]
        read_only_fields = ['admin_id', 'created_at']
        
    def validate(self, data):
        # Validate role-specific requirements
        role = data.get('role')
        faculty = data.get('faculty')
        dept = data.get('dept')
        
        # Faculty is REQUIRED only for faculty-related roles
        if role in ['مدير كلية', 'مسؤول كلية']:
            if not faculty:
                raise serializers.ValidationError("يجب تحديد الكلية لدور مدير الكلية أو مسؤول الكلية")
            # These roles shouldn't have department
            if dept:
                data['dept'] = None  # Clear department if provided
        
        # Department admin needs department but not faculty
        elif role == 'مدير ادارة':
            if not dept:
                raise serializers.ValidationError("يجب تحديد القسم لدور مدير الإدارة")
            # Clear faculty if provided for department admin
            if faculty:
                data['faculty'] = None
        
        # System admin and general manager don't need faculty or department
        elif role in ['مشرف النظام', 'مدير عام']:
            # Clear both faculty and department for these roles
            data['faculty'] = None
            data['dept'] = None
            
        return data
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        # Set default status if not provided
        validated_data['acc_status'] = validated_data.get('acc_status', 'active')
        
        admin = AdminsUser(**validated_data)
        admin.set_password(password)
        admin.save()
        return admin
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Apply same role-based logic on update
        role = validated_data.get('role', instance.role)
        
        if role in ['مشرف النظام', 'مدير عام']:
            validated_data['faculty'] = None
            validated_data['dept'] = None
        elif role == 'مدير ادارة':
            validated_data['faculty'] = None
        elif role in ['مدير كلية', 'مسؤول كلية']:
            validated_data['dept'] = None
            
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
        
class StudentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating student profile details with file upload support."""
    
    profile_photo = serializers.FileField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Students
        fields = [
            'email', 'faculty', 'phone_number', 'address',
            'acd_year', 'grade', 'major', 'profile_photo',
        ]
        read_only_fields = ['email']

    def update(self, instance, validated_data):
        from django.core.files.storage import default_storage
        import os
        
        profile_photo_file = validated_data.pop('profile_photo', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if profile_photo_file is not None:
            
            if instance.profile_photo and default_storage.exists(instance.profile_photo):
                default_storage.delete(instance.profile_photo)
            ext = os.path.splitext(profile_photo_file.name)[1]
            file_path = f'uploads/students/{instance.student_id}/image{ext}'
            saved_path = default_storage.save(file_path, profile_photo_file)
            instance.profile_photo = saved_path
        

        elif 'profile_photo' in self.initial_data and self.initial_data['profile_photo'] is None:
            if instance.profile_photo and default_storage.exists(instance.profile_photo):
                default_storage.delete(instance.profile_photo)
            instance.profile_photo = None
            
        instance.save()
        return instance