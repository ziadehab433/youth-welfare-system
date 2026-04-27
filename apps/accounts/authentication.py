"""
Custom JWT Authentication — reads access token from HttpOnly cookie.

BEFORE: reads from Authorization: Bearer <token> header
AFTER:  reads from 'access_token' HttpOnly cookie

All existing APIs continue to work without changes because
request.user is still set to the correct Student or AdminsUser.
"""

import logging
import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from apps.accounts.models import AdminsUser, Students

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class.
    1. Reads 'access_token' from HttpOnly cookie
    2. Decodes & validates JWT
    3. Resolves user from correct table based on user_type
    4. Attaches user to request
    
    Fallback: Also checks Authorization header for backward compatibility
              (useful for Swagger/testing during transition).
    """

    COOKIE_NAME = 'access_token'

    def authenticate(self, request):
        """
        Entry point called by DRF on every request.
        Returns (user, validated_token) or None.
        """
        raw_token = self._get_token(request)

        if raw_token is None:
            return None  # No token → anonymous request (DRF moves to next auth class)

        # Decode the JWT
        try:
            payload = jwt.decode(
                raw_token,
                settings.SECRET_KEY,
                algorithms=['HS256'],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Access token has expired.')
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT: {e}")
            raise AuthenticationFailed('Invalid access token.')

        # Resolve the user from the correct table
        user = self._resolve_user(payload)
        return (user, payload)

    def _get_token(self, request):
        """
        Extract token from:
          1. HttpOnly cookie (primary — production)
          2. Authorization header (fallback — Swagger / dev tools)
        """
        # 1. Try cookie first
        token = request.COOKIES.get(self.COOKIE_NAME)
        if token:
            return token

        # 2. Fallback: Authorization header (Bearer <token>)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]

        return None

    def _resolve_user(self, payload):
        """
        Look up the user from the correct table based on user_type claim.
        """
        user_type = payload.get('user_type')
        user_id   = payload.get('user_id')

        if not user_type or user_id is None:
            raise AuthenticationFailed('Token payload missing user_type or user_id.')

        try:
            if user_type == 'admin':
                user = AdminsUser.objects.get(admin_id=user_id)
                # Check if admin account is still active
                if not user.is_active:
                    raise AuthenticationFailed('Admin account is inactive.')
                # Attach extra info for permission checks
                user.token_payload = payload
                return user

            elif user_type == 'student':
                user = Students.objects.get(student_id=user_id)
                user.token_payload = payload
                return user

            else:
                raise AuthenticationFailed(f'Unknown user_type: {user_type}')

        except AdminsUser.DoesNotExist:
            raise AuthenticationFailed('Admin user not found.')
        except Students.DoesNotExist:
            raise AuthenticationFailed('Student user not found.')

    def authenticate_header(self, request):
        """
        Return string for WWW-Authenticate header on 401 responses.
        """
        return 'Cookie realm="access_token"'