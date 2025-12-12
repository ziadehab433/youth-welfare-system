# apps/accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import Students, AdminsUser
from apps.solidarity.models import Departments, Faculties

import bcrypt
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


# ===========================
# General Login
# ===========================

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UnifiedTokenObtainSerializer(TokenObtainPairSerializer):
    """Add custom claims."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = getattr(user, 'role', None)
        token['user_type'] = getattr(user, 'user_type', None) or 'admin'
        token['name'] = getattr(user, 'name', None)
        return token


# ===========================
# Student Registration
# ===========================

class StudentSignUpSerializer(serializers.ModelSerializer):
    """
    Local signup (email/password) with validation.
    No encryption.
    """
    password = serializers.CharField(write_only=True)
    profile_image = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Students
        fields = [
            'name', 'email', 'password', 'faculty', 'gender',
            'nid', 'uid', 'phone_number', 'address',
            'acd_year', 'grade', 'major', 'profile_image'
        ]

    # -------- Validation --------

    def validate_nid(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("National ID must contain only digits.")
        if len(value) != 14:
            raise serializers.ValidationError("National ID must be exactly 14 digits.")
        return value

    def validate_uid(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("University ID must be at least 5 characters.")
        return value

    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits.")
        return value

    # -------- Create --------

    def create(self, validated_data):
        profile_image = validated_data.pop("profile_image", None)

        raw_password = validated_data.pop("password")
        hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
        validated_data["password"] = hashed_pw

        student = Students.objects.create(**validated_data)

        # Handle file upload
        if profile_image:
            ext = os.path.splitext(profile_image.name)[1]
            file_path = f"uploads/students/{student.student_id}/image{ext}"

            saved_path = default_storage.save(file_path, ContentFile(profile_image.read()))
            student.profile_photo = saved_path
            student.save()

        return student


# ===========================
# Student Detail
# ===========================

class StudentDetailSerializer(serializers.ModelSerializer):
    profile_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Students
        fields = [
            'student_id', 'name', 'email', 'faculty', 'gender',
            'nid', 'uid', 'phone_number', 'address',
            'acd_year', 'grade', 'major',
            'profile_photo_url',
            'google_picture', 'is_google_auth', 'auth_method', 'last_google_login'
        ]

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(f'/media/{obj.profile_photo}')
        return None


# ===========================
# Student Update
# ===========================

class StudentUpdateSerializer(serializers.ModelSerializer):
    profile_photo = serializers.FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Students
        fields = [
            'faculty', 'phone_number', 'address',
            'acd_year', 'grade', 'major', 'profile_photo'
        ]

    def update(self, instance, validated_data):
        profile_photo_file = validated_data.pop('profile_photo', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle profile photo upload
        if profile_photo_file:
            # Delete old file
            if instance.profile_photo and default_storage.exists(instance.profile_photo):
                default_storage.delete(instance.profile_photo)

            ext = os.path.splitext(profile_photo_file.name)[1]
            file_path = f'uploads/students/{instance.student_id}/image{ext}'
            saved_path = default_storage.save(file_path, profile_photo_file)
            instance.profile_photo = saved_path

        # Remove photo
        elif 'profile_photo' in self.initial_data and self.initial_data['profile_photo'] is None:
            if instance.profile_photo and default_storage.exists(instance.profile_photo):
                default_storage.delete(instance.profile_photo)
            instance.profile_photo = None

        instance.save()
        return instance


# ===========================
# Admin User
# ===========================

class AdminsUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    dept_name = serializers.CharField(source='dept.name', read_only=True)

    faculty = serializers.PrimaryKeyRelatedField(
        queryset=Faculties.objects.all(), required=False, allow_null=True
    )
    dept = serializers.PrimaryKeyRelatedField(
        queryset=Departments.objects.all(), required=False, allow_null=True
    )

    dept_fac_ls = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )

    class Meta:
        model = AdminsUser
        fields = [
            'admin_id', 'name', 'email', 'password',
            'faculty', 'faculty_name', 'dept', 'dept_name',
            'role', 'acc_status',
            'can_create', 'can_update', 'can_read', 'can_delete',
            'created_at', 'dept_fac_ls', 'nid', 'phone_number'
        ]
        read_only_fields = ['admin_id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')

        admin = AdminsUser(**validated_data)
        admin.set_password(password)
        admin.acc_status = validated_data.get('acc_status', 'active')
        admin.save()
        return admin

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


# ===========================
# GOOGLE OAUTH
# ===========================

class GoogleOAuthLoginSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True, required=True)


class GoogleOAuthTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    picture = serializers.URLField(allow_null=True, allow_blank=True)
    auth_method = serializers.CharField()


class GoogleStudentSerializer(serializers.ModelSerializer):
    picture_url = serializers.SerializerMethodField()

    class Meta:
        model = Students
        fields = [
            'student_id', 'name', 'email', 'faculty', 'gender',
            'acd_year', 'major', 'google_picture',
            'picture_url',
            'is_google_auth', 'auth_method', 'last_google_login'
        ]
        read_only_fields = [
            'student_id', 'google_picture',
            'is_google_auth', 'auth_method', 'last_google_login'
        ]

    def get_picture_url(self, obj):
        return obj.google_picture


class GoogleOAuthSignUpSerializer(serializers.Serializer):
    """
    Google OAuth signup data + sensitive validation (no encryption).
    """
    code = serializers.CharField(write_only=True, required=True)

    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    faculty = serializers.IntegerField(required=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'Other'], default='M')
    acd_year = serializers.CharField(required=True)
    nid = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    major = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=True)
    address = serializers.CharField(required=False, allow_blank=True)

    # -------- Validation --------

    def validate_nid(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("National ID must contain only digits.")
        if len(value) < 10:
            raise serializers.ValidationError("National ID must be at least 10 digits.")
        return value

    def validate_faculty(self, value):
        if not Faculties.objects.filter(faculty_id=value).exists():
            raise serializers.ValidationError("Faculty does not exist.")
        return value

