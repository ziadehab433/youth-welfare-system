"""
Authentication Views — Secure HttpOnly Cookie Flow
===================================================
POST /api/accounts/login/          → authenticate + set cookies
POST /api/accounts/token/refresh/  → rotate refresh token + set cookies
POST /api/accounts/logout/         → revoke token + clear cookies
GET  /api/accounts/csrf/           → deliver CSRF token
POST /api/accounts/signUp/         → student registration + set cookies
"""

import hashlib
import logging
import secrets
import uuid
from datetime import timedelta

import bcrypt
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.viewsets import ViewSet, GenericViewSet # ADD GenericViewSet
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import AdminsUser, RefreshToken, Students
from apps.accounts.serializers import (
    AdminsUserSerializer,
    StudentDetailSerializer,
    StudentSignUpSerializer,
    StudentUpdateSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    RefreshResponseSerializer,
    LogoutResponseSerializer,
    CSRFResponseSerializer,
)
from apps.solidarity.models import Departments, Faculties
from .encryption import encryption_service
from .permissions import IsRole
from .security import get_client_ip

logger = logging.getLogger(__name__)


# ================================================================
#  CONSTANTS
# ================================================================

ACCESS_TOKEN_LIFETIME  = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

# Cookie names
ACCESS_COOKIE_NAME  = 'access_token'
REFRESH_COOKIE_NAME = 'refresh_token'


# ================================================================
#  HELPER FUNCTIONS
# ================================================================

def _generate_access_token(payload: dict) -> str:
    """
    Generate a short-lived HS256 JWT access token.
    Payload must include at least: user_id, user_type.
    """
    now = timezone.now()
    payload.update({
        'iat': int(now.timestamp()),
        'exp': int((now + ACCESS_TOKEN_LIFETIME).timestamp()),
        'jti': uuid.uuid4().hex,   # unique token ID
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def _generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token.
    This is NOT a JWT — just a random opaque string.
    """
    return secrets.token_urlsafe(64)


def _hash_token(raw_token: str) -> str:
    """
    SHA-256 hash of the raw refresh token for DB storage.
    We never store the raw token.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _save_refresh_token(user_id, user_type, raw_token, request):
    """
    Hash the raw refresh token and persist to the refresh_tokens table.
    Returns the DB record.
    """
    token_hash = _hash_token(raw_token)
    ip_address = get_client_ip(request)
    device_info = request.META.get('HTTP_USER_AGENT', '')[:255]

    return RefreshToken.objects.create(
        user_id     = user_id,
        user_type   = user_type,
        token_hash  = token_hash,
        expires_at  = timezone.now() + REFRESH_TOKEN_LIFETIME,
        ip_address  = ip_address,
        device_info = device_info,
    )


def _set_auth_cookies(response, access_token, raw_refresh_token):
    """
    Set HttpOnly cookies for both tokens on the response object.
    Cookie flags adapt via settings (Secure=False on HTTP, True on HTTPS).
    """
    secure = getattr(settings, 'AUTH_COOKIE_SECURE', False)

    # Access cookie — sent with every request
    response.set_cookie(
        key      = ACCESS_COOKIE_NAME,
        value    = access_token,
        max_age  = int(ACCESS_TOKEN_LIFETIME.total_seconds()),
        httponly = True,
        secure   = secure,
        samesite = 'Lax',
        path     = '/',
    )

    # Refresh cookie — ONLY sent to the refresh endpoint
    response.set_cookie(
        key      = REFRESH_COOKIE_NAME,
        value    = raw_refresh_token,
        max_age  = int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        httponly = True,
        secure   = secure,
        samesite = 'Lax',
        path     = '/api/accounts/token/refresh/',
    )

    return response


def _clear_auth_cookies(response):
    """
    Delete both auth cookies from the browser.
    """
    response.delete_cookie(ACCESS_COOKIE_NAME, path='/')
    response.delete_cookie(REFRESH_COOKIE_NAME, path='/api/accounts/token/refresh/')
    return response


def _build_access_payload(user_type, user_id, extra_claims=None):
    """
    Build a consistent JWT payload for access tokens.
    """
    payload = {
        'user_id':   user_id,
        'user_type': user_type,
    }
    if extra_claims:
        payload.update(extra_claims)
    return payload


def _get_faculty_info(faculty_id):
    """Helper method to get faculty information."""
    if not faculty_id:
        return None, None
    try:
        faculty = Faculties.objects.get(faculty_id=faculty_id)
        return faculty_id, faculty.name
    except Faculties.DoesNotExist:
        return faculty_id, None


def _get_dept_ids_for_admin(user):
    """
    Returns a list of dept_ids the admin has access to.
    - مدير ادارة → single dept from FK
    - مسؤول كلية → multiple depts resolved from dept_fac_ls
    - مشرف النظام → empty list (has access to everything)
    """
    dept_ids = []
    dept_names_map = {}

    if user.role == 'مدير ادارة':
        if user.dept_id:
            dept_ids = [user.dept_id]
            try:
                dept = Departments.objects.get(dept_id=user.dept_id)
                dept_names_map[user.dept_id] = dept.name
            except Departments.DoesNotExist:
                dept_names_map[user.dept_id] = None

    elif user.role == 'مسؤول كلية':
        if user.dept_fac_ls:
            raw_ids = [int(x) for x in user.dept_fac_ls]
            departments = Departments.objects.filter(dept_id__in=raw_ids)
            for dept in departments:
                dept_ids.append(dept.dept_id)
                dept_names_map[dept.dept_id] = dept.name

    elif user.role == 'مشرف النظام':
        pass  # Super admin — no dept restriction

    return dept_ids, dept_names_map


# ================================================================
#  CSRF ENDPOINT
# ================================================================

@extend_schema(
    tags=["Authentication"],
    description="Get CSRF cookie set on the response. Call this once on app load.",
    responses={200: CSRFResponseSerializer},
)
class CSRFTokenView(APIView):
    """
    GET /api/accounts/csrf/
    
    Forces Django to set the 'csrftoken' cookie on the response.
    The frontend calls this once (e.g. on app load) and then reads
    the CSRF token from the cookie for subsequent POST/PUT/DELETE requests.
    """
    permission_classes = []
    authentication_classes = []   # no auth needed

    def get(self, request):
        csrf_token = get_token(request)   # forces Django to set the cookie
        return Response({'detail': 'CSRF cookie set.'}, status=200)


# ================================================================
#  LOGIN VIEW
# ================================================================

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(
    tags=["Authentication"],
    description="Login and receive HttpOnly cookie tokens. No tokens in response body.",
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        400: {"description": "Missing email or password"},
        401: {"description": "Invalid credentials or inactive account"},
    },
)
class LoginView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        identifier = request.data.get('email') or request.data.get('username')
        password   = request.data.get('password')

        if not identifier or not password:
            return Response(
                {'detail': 'email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =========================
        # Try ADMIN authentication
        # =========================
        user = authenticate(request, username=identifier, password=password)

        if user and isinstance(user, AdminsUser):
            # Check active status
            if hasattr(user, 'acc_status') and user.acc_status != 'active':
                return Response(
                    {
                        'detail': f'حسابك غير مفعل. الحالة الحالية: {user.acc_status}',
                        'status': user.acc_status,
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            dept_ids, dept_names_map = _get_dept_ids_for_admin(user)
            dept_info = [
                {"dept_id": did, "dept_name": dept_names_map.get(did)}
                for did in dept_ids
            ]

            # Build extra JWT claims
            extra = {
                'role':     user.role,
                'name':     user.name,
                'dept_ids': dept_ids,
            }

            # Faculty info for certain roles
            if user.role in ['مسؤول كلية', 'مدير كلية']:
                fac_id, fac_name = _get_faculty_info(user.faculty_id)
                extra['faculty_id']   = fac_id
                extra['faculty_name'] = fac_name

            # Generate tokens
            access_payload = _build_access_payload('admin', user.admin_id, extra)
            access_token   = _generate_access_token(access_payload)
            raw_refresh    = _generate_refresh_token()

            # Save hashed refresh token to DB
            _save_refresh_token(user.admin_id, 'admin', raw_refresh, request)

            # Build response body (NO tokens in body!)
            response_data = {
                'detail':      'Login successful.',
                'user_type':   'admin',
                'admin_id':    user.admin_id,
                'role':        user.role,
                'name':        user.name,
                'dept_ids':    dept_ids,
                'departments': dept_info,
            }

            if user.role in ['مسؤول كلية', 'مدير كلية']:
                response_data['faculty_id']   = extra.get('faculty_id')
                response_data['faculty_name'] = extra.get('faculty_name')

            response = Response(response_data, status=status.HTTP_200_OK)
            _set_auth_cookies(response, access_token, raw_refresh)
            return response

        # =========================
        # Fallback: Try STUDENT
        # =========================
        student = Students.objects.filter(email=identifier).first()

        if student and bcrypt.checkpw(password.encode(), student.password.encode()):
            fac_id, fac_name = _get_faculty_info(student.faculty_id)

            extra = {
                'name':         student.name,
                'faculty_id':   fac_id,
                'faculty_name': fac_name,
            }

            access_payload = _build_access_payload('student', student.student_id, extra)
            access_token   = _generate_access_token(access_payload)
            raw_refresh    = _generate_refresh_token()

            _save_refresh_token(student.student_id, 'student', raw_refresh, request)

            response_data = {
                'detail':       'Login successful.',
                'user_type':    'student',
                'student_id':   student.student_id,
                'name':         student.name,
                'faculty_id':   fac_id,
                'faculty_name': fac_name,
            }

            response = Response(response_data, status=status.HTTP_200_OK)
            _set_auth_cookies(response, access_token, raw_refresh)
            return response

        # =========================
        # Both failed
        # =========================
        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )


# ================================================================
#  REFRESH TOKEN VIEW
# ================================================================

@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(
    tags=["Authentication"],
    description="Rotate refresh token (from HttpOnly cookie) and set new cookies. No request body needed.",
    request=None,
    responses={
        200: RefreshResponseSerializer,
        401: {"description": "Missing, invalid, or expired refresh token"},
    },
)
class RefreshTokenView(APIView):
    """
    POST /api/accounts/token/refresh/

    1. Read refresh token from HttpOnly cookie
    2. Hash it → look up in DB
    3. Validate (not revoked, not expired)
    4. Revoke old token (rotation)
    5. Generate new access + refresh tokens
    6. Save new hashed refresh → DB
    7. Set new HttpOnly cookies
    """
    permission_classes  = []
    authentication_classes = []   # can't use access token auth here

    def post(self, request):
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)

        if not raw_refresh:
            return Response(
                {'detail': 'Refresh token cookie missing.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Look up by hash
        token_hash = _hash_token(raw_refresh)

        try:
            stored_token = RefreshToken.objects.get(
                token_hash = token_hash,
                is_revoked = False,
            )
        except RefreshToken.DoesNotExist:
            # Possible token reuse attack — revoke ALL tokens for this user
            # (We can't know the user_id from the raw token, so just reject.)
            return Response(
                {'detail': 'Invalid or revoked refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check expiration
        if stored_token.expires_at < timezone.now():
            stored_token.is_revoked = True
            stored_token.save(update_fields=['is_revoked'])
            response = Response(
                {'detail': 'Refresh token has expired. Please log in again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_auth_cookies(response)
            return response

        # ---- Token is valid → ROTATE ----

        # 1. Revoke old token
        stored_token.is_revoked = True
        stored_token.save(update_fields=['is_revoked'])

        # 2. Determine the user and rebuild access token claims
        user_type = stored_token.user_type
        user_id   = stored_token.user_id

        try:
            if user_type == 'admin':
                user = AdminsUser.objects.get(admin_id=user_id)
                if not user.is_active:
                    response = Response(
                        {'detail': 'Admin account is inactive.'},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                    _clear_auth_cookies(response)
                    return response

                dept_ids, _ = _get_dept_ids_for_admin(user)
                extra = {
                    'role':     user.role,
                    'name':     user.name,
                    'dept_ids': dept_ids,
                }
                if user.role in ['مسؤول كلية', 'مدير كلية']:
                    fac_id, fac_name = _get_faculty_info(user.faculty_id)
                    extra['faculty_id']   = fac_id
                    extra['faculty_name'] = fac_name

            elif user_type == 'student':
                user = Students.objects.get(student_id=user_id)
                fac_id, fac_name = _get_faculty_info(user.faculty_id)
                extra = {
                    'name':         user.name,
                    'faculty_id':   fac_id,
                    'faculty_name': fac_name,
                }
            else:
                return Response(
                    {'detail': 'Invalid user type in refresh token.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except (AdminsUser.DoesNotExist, Students.DoesNotExist):
            response = Response(
                {'detail': 'User no longer exists.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_auth_cookies(response)
            return response

        # 3. Generate new pair
        access_payload = _build_access_payload(user_type, user_id, extra)
        new_access     = _generate_access_token(access_payload)
        new_raw_refresh = _generate_refresh_token()

        # 4. Store new refresh hash
        _save_refresh_token(user_id, user_type, new_raw_refresh, request)

        # 5. Respond
        response = Response({'detail': 'Token refreshed.'}, status=status.HTTP_200_OK)
        _set_auth_cookies(response, new_access, new_raw_refresh)
        return response


# ================================================================
#  LOGOUT VIEW
# ================================================================

@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(
    tags=["Authentication"],
    description="Logout — revoke refresh token and clear HttpOnly cookies. No request body needed.",
    request=None,
    responses={200: LogoutResponseSerializer},
)
class LogoutView(APIView):
    """
    POST /api/accounts/logout/

    1. Read refresh token from cookie
    2. Hash it → find in DB → revoke
    3. Clear both cookies
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)

        if raw_refresh:
            token_hash = _hash_token(raw_refresh)
            # Revoke the specific token (if it exists)
            RefreshToken.objects.filter(
                token_hash=token_hash,
                is_revoked=False,
            ).update(is_revoked=True)

        response = Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        _clear_auth_cookies(response)
        return response


# ================================================================
#  LOGOUT ALL DEVICES VIEW
# ================================================================

@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(
    tags=["Authentication"],
    description="Logout from all devices — revoke all refresh tokens for current user.",
    request=None,
    responses={200: LogoutResponseSerializer},
)
class LogoutAllDevicesView(APIView):
    """
    POST /api/accounts/logout/all/

    Requires authentication (access token cookie).
    Revokes ALL refresh tokens for the current user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if hasattr(user, 'admin_id'):
            user_type = 'admin'
            user_id   = user.admin_id
        elif hasattr(user, 'student_id'):
            user_type = 'student'
            user_id   = user.student_id
        else:
            return Response({'detail': 'Unknown user type.'}, status=400)

        count = RefreshToken.objects.filter(
            user_id    = user_id,
            user_type  = user_type,
            is_revoked = False,
        ).update(is_revoked=True)

        response = Response(
            {'detail': f'Logged out from all devices. {count} session(s) revoked.'},
            status=status.HTTP_200_OK,
        )
        _clear_auth_cookies(response)
        return response


# ================================================================
#  STUDENT SIGN-UP VIEW (Updated for cookies)
# ================================================================

@extend_schema(
    tags=["Authentication"],
    description="Register a new student account with optional profile image.",
    request={'multipart/form-data': StudentSignUpSerializer},
    responses={201: StudentSignUpSerializer},
)
class StudentSignUpView(APIView):
    permission_classes = []
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = StudentSignUpSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student = serializer.save()

        fac_id, fac_name = _get_faculty_info(student.faculty_id)

        extra = {
            'name':         student.name,
            'faculty_id':   fac_id,
            'faculty_name': fac_name,
        }

        access_payload = _build_access_payload('student', student.student_id, extra)
        access_token   = _generate_access_token(access_payload)
        raw_refresh    = _generate_refresh_token()

        _save_refresh_token(student.student_id, 'student', raw_refresh, request)

        # Build profile photo URL
        profile_photo_url = None
        if student.profile_photo:
            profile_photo_url = request.build_absolute_uri(
                f'/api/files/students/{student.student_id}/image/'
            )

        response_data = {
            'message':       'Account created successfully',
            'student_id':    student.student_id,
            'name':          student.name,
            'profile_photo': profile_photo_url,
        }

        response = Response(response_data, status=status.HTTP_201_CREATED)
        _set_auth_cookies(response, access_token, raw_refresh)
        return response


# ================================================================
#  ADMIN MANAGEMENT VIEWSET (unchanged — just re-import)
# ================================================================
# Keep your existing AdminManagementViewSet and StudentProfileViewSet
# exactly as they are. They don't need changes because:
#   - CookieJWTAuthentication sets request.user automatically
#   - permission_classes still work the same way

# Re-paste or import your existing ViewSets below this line.
# I'm not modifying them — they work as-is.

# class AdminManagementViewSet(viewsets.ViewSet):
#     ... keep your existing code ...

# class StudentProfileViewSet(ViewSet):
#     ... keep your existing code ...







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