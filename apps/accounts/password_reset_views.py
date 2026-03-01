from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from drf_spectacular.utils import extend_schema
import bcrypt
import logging

from apps.accounts.models import Students, AdminsUser
from apps.accounts.password_reset_serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from apps.accounts.tokens import password_reset_token

logger = logging.getLogger(__name__)


class PasswordResetRequestView(APIView):
    """
    Request password reset - sends email with reset link.
    Works for Students and Admins with role 'مشرف النظام'.
    """
    permission_classes = []
    
    @extend_schema(
        tags=["Password Reset"],
        description="Request password reset by providing email address",
        request=PasswordResetRequestSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        }
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        # Try to find user (student or admin)
        user = None
        user_type = None
        
        # Check if student
        student = Students.objects.filter(email=email).first()
        if student:
            user = student
            user_type = 'student'
        else:
            # Check if admin with role 'مشرف النظام'
            admin = AdminsUser.objects.filter(
                email=email, 
                role='مشرف النظام'
            ).first()
            if admin:
                user = admin
                user_type = 'admin'
        
        if user:
            try:
                # Generate token
                user_id = user.student_id if user_type == 'student' else user.admin_id
                uid = urlsafe_base64_encode(force_bytes(f"{user_type}:{user_id}"))
                token = password_reset_token.make_token(user)
                

                # in production we must use a real dmain URL, for now we will use the API endpoint directly

                # Build reset URL
                reset_url = request.build_absolute_uri(
                    f'/api/auth/password-reset/confirm/?uid={uid}&token={token}'
                )
                
                # Prepare email context
                context = {
                    'user_name': user.name,
                    'reset_url': reset_url,
                    'expiry_minutes': 20,
                }
                
                # Render email templates
                subject = render_to_string(
                    'password_reset/email_subject.txt', 
                    context
                ).strip()
                
                html_message = render_to_string(
                    'password_reset/email_body.html', 
                    context
                )
                
                plain_message = render_to_string(
                    'password_reset/email_body.txt', 
                    context
                )
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Password reset email sent to {email}")
                
            except Exception as e:
                logger.error(f"Failed to send password reset email: {str(e)}")
                # Don't reveal the error to the user for security
        
        # Always return success (security best practice - no user enumeration)
        return Response({
            "message": "إذا كان البريد الإلكتروني موجودًا، سيتم إرسال رابط إعادة تعيين كلمة المرور"
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token and set new password.
    """
    permission_classes = []
    
    @extend_schema(
        tags=["Password Reset"],
        description="Confirm password reset using uid and token from email",
        request=PasswordResetConfirmSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            },
            400: {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            }
        }
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Decode uid
            decoded = force_str(urlsafe_base64_decode(uid))
            user_type, user_id = decoded.split(':')
            
            # Get user based on type
            if user_type == 'student':
                user = Students.objects.get(student_id=int(user_id))
            elif user_type == 'admin':
                user = AdminsUser.objects.get(admin_id=int(user_id))
            else:
                raise ValueError("Invalid user type")
            
            # Verify token
            if not password_reset_token.check_token(user, token):
                logger.warning(f"Invalid or expired token for {user_type} {user_id}")
                return Response({
                    "error": "رابط إعادة التعيين غير صالح أو منتهي الصلاحية"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update password based on user type
            if user_type == 'student':
                # Students use bcrypt
                hashed_pw = bcrypt.hashpw(
                    new_password.encode(), 
                    bcrypt.gensalt()
                ).decode()
                user.password = hashed_pw
            else:
                # Admins use Django's set_password
                user.set_password(new_password)
            
            user.save()
            
            logger.info(f"Password reset successful for {user_type} {user_id}")
            
            return Response({
                "message": "تم تغيير كلمة المرور بنجاح"
            }, status=status.HTTP_200_OK)
            
        except (ValueError, Students.DoesNotExist, AdminsUser.DoesNotExist) as e:
            logger.error(f"Password reset error: {str(e)}")
            return Response({
                "error": "رابط إعادة التعيين غير صالح"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            return Response({
                "error": "حدث خطأ أثناء إعادة تعيين كلمة المرور"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
