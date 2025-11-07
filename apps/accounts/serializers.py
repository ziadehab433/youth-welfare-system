# apps/accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate



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
