from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import Students, AdminsUser

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if email exists in Students or AdminsUser (مشرف النظام only)"""
        student_exists = Students.objects.filter(email=value).exists()
        admin_exists = AdminsUser.objects.filter(
            email=value, 
            role='مشرف النظام'
        ).exists()
        
        if not student_exists and not admin_exists:
            raise serializers.ValidationError(
                "لا يوجد حساب مرتبط بهذا البريد الإلكتروني"
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset with token"""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password],
        help_text="كلمة المرور الجديدة"
    )
    confirm_password = serializers.CharField(
        required=True, 
        write_only=True,
        help_text="تأكيد كلمة المرور"
    )
    
    def validate(self, attrs):
        """Ensure passwords match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "كلمات المرور غير متطابقة"
            })
        return attrs
