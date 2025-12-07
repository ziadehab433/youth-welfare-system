
from rest_framework import serializers
from .models import Students, AdminsUser
from .encryption import encryption_service
import bcrypt
from django.utils import timezone

class StudentSignUpSerializer(serializers.ModelSerializer):
    """
    Serializer for student registration with encrypted sensitive fields
    """
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Students
        fields = [
            'name', 'email', 'password', 'password_confirm',
            'faculty', 'gender', 'nid', 'uid', 'phone_number',
            'address', 'acd_year', 'major'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'nid': {'write_only': True},  # Don't return encrypted nid
            'uid': {'write_only': True},
            'phone_number': {'write_only': True},
            'address': {'write_only': True},
        }

    def validate(self, data):
        """Validate passwords match and nid/uid are valid"""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError("Passwords do not match")
        
        # Validate NID (example: should be 14 digits for Egyptian ID)
        nid = data.get('nid', '')
        if nid and not nid.isdigit():
            raise serializers.ValidationError("National ID must contain only digits")
        
        # Validate UID format
        uid = data.get('uid', '')
        if uid and len(uid) < 5:
            raise serializers.ValidationError("University ID must be at least 5 characters")
        
        return data

    def create(self, validated_data):
        """Create student with hashed password"""
        password = validated_data.pop('password')
        
        # Hash password using bcrypt
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        validated_data['password'] = hashed_password
        
        # The encrypted fields (nid, uid, phone_number, address) 
        # are automatically encrypted by EncryptedTextField
        student = Students.objects.create(**validated_data)
        return student


class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for reading student profile.
    Shows encrypted data as decrypted (automatic via model field)
    """
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Students
        fields = [
            'student_id', 'name', 'email', 'faculty', 'gender',
            'nid', 'uid', 'phone_number', 'address',
            'acd_year', 'grade', 'major', 'join_date',
            'profile_photo', 'profile_photo_url'
        ]
        read_only_fields = [
            'student_id', 'join_date', 'email'  # Email shouldn't be changed
        ]
    def get_profile_photo_url(self, obj) -> str:
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(f'/media/{obj.profile_photo}')
        return None


class StudentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating student profile.
    Encrypted fields are handled automatically by the model.
    """
    
    class Meta:
        model = Students
        fields = [
            'name', 'gender', 'nid', 'uid', 'phone_number',
            'address', 'major'
        ]
        extra_kwargs = {
            'nid': {'required': False},
            'uid': {'required': False},
            'phone_number': {'required': False},
            'address': {'required': False},
        }

    def validate_nid(self, value):
        """Validate NID if provided"""
        if value and not value.isdigit():
            raise serializers.ValidationError("National ID must contain only digits")
        return value

    def update(self, instance, validated_data):
        """Update student - encrypted fields are handled by model"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AdminsUserSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin Users
    """
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AdminsUser
        fields = [
            'admin_id', 'name', 'email', 'password', 'faculty',
            'dept', 'role', 'can_create', 'can_read', 'can_update',
            'can_delete', 'acc_status', 'created_at', 'dept_fac_ls'
        ]
        read_only_fields = ['admin_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Create admin with hashed password"""
        password = validated_data.pop('password', None)
        admin = AdminsUser(**validated_data)
        
        if password:
            admin.set_password(password)
        
        admin.save()
        return admin

    def update(self, instance, validated_data):
        """Update admin"""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
    

###################################


class GoogleOAuthLoginSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth login
    Expects 'code' from frontend after user authorizes
    """
    code = serializers.CharField(required=True, write_only=True)
    
    class Meta:
        fields = ['code']


class GoogleOAuthTokenSerializer(serializers.Serializer):
    """
    Serializer for returning tokens and user info after Google OAuth
    """
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    picture = serializers.URLField(allow_null=True, allow_blank=True)
    auth_method = serializers.CharField()
    
    class Meta:
        fields = [
            'access_token', 'refresh_token', 'user_id',
            'name', 'email', 'picture', 'auth_method'
        ]


class GoogleStudentSerializer(serializers.ModelSerializer):
    """
    Serializer for students authenticated via Google OAuth
    Doesn't require traditional password fields
    """
    picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Students
        fields = [
            'student_id', 'name', 'email', 'faculty', 'gender',
            'acd_year', 'major', 'google_picture', 'picture_url',
            'is_google_auth', 'auth_method', 'last_google_login'
        ]
        read_only_fields = [
            'student_id', 'is_google_auth', 'auth_method',
            'last_google_login', 'google_picture'
        ]
    
    def get_picture_url(self, obj):
        return obj.google_picture

from apps.solidarity.models import Faculties
from apps.accounts.models import Students

class GoogleOAuthSignUpSerializer(serializers.Serializer):
    """
    Serializer for Google OAuth signup
    """
    code = serializers.CharField(required=True, write_only=True, help_text="Google authorization code")
    name = serializers.CharField(required=True, max_length=255)
    email = serializers.EmailField(required=True)
    faculty = serializers.IntegerField(required=True, help_text="Faculty ID")
    gender = serializers.ChoiceField(choices=['M', 'F', 'Other'], required=False, default='M')
    acd_year = serializers.CharField(required=True, max_length=10)
    nid = serializers.CharField(required=True, max_length=20)
    uid = serializers.CharField(required=True, max_length=50)
    major = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone_number = serializers.CharField(required=True, max_length=50)
    address = serializers.CharField(required=False, allow_blank=True, max_length=500)  # ← ADD THIS TOO

    
    def validate_nid(self, value):
        """Validate NID"""
        if not value.isdigit():
            raise serializers.ValidationError("National ID must contain only digits")
        if len(value) < 10:
            raise serializers.ValidationError("National ID must be at least 10 digits")
        return value
    
    def validate_faculty(self, value):
        """Validate faculty exists"""
        if not Faculties.objects.filter(faculty_id=value).exists():
            raise serializers.ValidationError("Faculty does not exist")
        return value