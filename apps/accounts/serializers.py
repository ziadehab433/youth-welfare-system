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
            'acd_year', 'grade', 'major', 'profile_photo', 'profile_photo_url'
        ]

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(f'/media/{obj.profile_photo}')
        return None