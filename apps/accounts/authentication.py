from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from apps.solidarity.models import Admins
from apps.accounts.models import Students

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_type = validated_token.get("user_type")

        if user_type == "admin":
            admin_id = validated_token.get("admin_id")  # <-- use this
            return Admins.objects.get(admin_id=admin_id)
        elif user_type == "student":
            student_id = validated_token.get("student_id")
            return Students.objects.get(student_id=student_id)
        else:
            raise InvalidToken("Unknown user type in token")
