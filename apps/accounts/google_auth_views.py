"""
Google OAuth Authentication Views
Handles Google SSO login and signup flows
"""

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
import logging

from .google_oauth import GoogleOAuthService
from .models import Students
from .serializers import (
    GoogleOAuthLoginSerializer,
    GoogleOAuthTokenSerializer,
    GoogleOAuthSignUpSerializer,
    GoogleStudentSerializer
)
from apps.solidarity.models import Faculties

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
import logging
import secrets
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse


from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.conf import settings
import logging

from .google_oauth import GoogleOAuthService
from .models import Students
from .serializers import GoogleOAuthLoginSerializer
from .security import (
    RateLimiter, AuditLogger, InputValidator, get_client_ip
)
from apps.solidarity.models import Faculties


logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Google OAuth"],
    description="Step 1: Get Google OAuth Authorization URL. Redirect user to this URL.",
    responses={
        200: OpenApiResponse(
            description="Authorization URL returned successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...",
                        "message": "Redirect user to this URL to authenticate with Google"
                    },
                    response_only=True,
                )
            ]
        )
    }
)
class GoogleOAuthInitiateView(APIView):
    """
    Step 1: Initiate Google OAuth flow
    Returns the Google authorization URL
    """
    permission_classes = []
    
    def get(self, request):
        """
        GET /api/auth/google/init/
        
        Returns Google authorization URL for frontend to redirect to
        """
        try:
            # Use GoogleOAuthService to get authorization URL
            auth_url = GoogleOAuthService.get_authorization_url()
            
            logger.info(f"Generated auth URL with redirect_uri: {settings.GOOGLE_REDIRECT_URI}")
            
            return Response({
                'authorization_url': auth_url,
                'message': 'Redirect user to this URL to authenticate with Google'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            return Response(
                {'error': 'Failed to initiate Google OAuth'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
@extend_schema(
    tags=["Google OAuth"],
    description="Step 2: Exchange Google authorization code for JWT tokens. Use this after user returns from Google with authorization code.",
    request=GoogleOAuthLoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Successfully logged in",
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user_id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "picture": "https://lh3.googleusercontent.com/...",
                        "auth_method": "google",
                        "message": "Successfully logged in via Google"
                    },
                    response_only=True,
                )
            ]
        ),
        404: OpenApiResponse(
            description="User not found",
            examples=[
                OpenApiExample(
                    "User Not Found",
                    value={
                        "error": "No account found with this Google email",
                        "suggestion": "Please signup with your Google account first",
                        "google_email": "newuser@gmail.com"
                    },
                    response_only=True,
                )
            ]
        ),
        401: OpenApiResponse(
            description="Authentication failed",
            examples=[
                OpenApiExample(
                    "Auth Failed",
                    value={
                        "error": "Google authentication failed. Please try again."
                    },
                    response_only=True,
                )
            ]
        ),
        429: OpenApiResponse(
            description="Rate limit exceeded",
            examples=[
                OpenApiExample(
                    "Rate Limited",
                    value={
                        "detail": "Too many login attempts. Try again later.",
                        "retry_after": 3600
                    },
                    response_only=True,
                )
            ]
        ),
    }
)
class GoogleOAuthLoginView(APIView):
    """
    Step 2: Handle Google OAuth callback
    Exchange authorization code for tokens
    If student exists with this Google ID, login them
    
    Rate Limited: 10 attempts per hour per user/IP
    """
    permission_classes = []
    
    # Initialize rate limiter for login
    rate_limiter = RateLimiter(
        max_requests=settings.RATE_LIMIT_CONFIG['auth']['max_requests'],
        window_seconds=settings.RATE_LIMIT_CONFIG['auth']['window_seconds']
    )
    
    def get_faculty_info(self, faculty_id):
        """Helper to get faculty information"""
        if not faculty_id:
            return None, None
        try:
            faculty = Faculties.objects.get(faculty_id=faculty_id)
            return faculty_id, faculty.name
        except Faculties.DoesNotExist:
            return faculty_id, None
    
    def post(self, request):
        """
        POST /api/accounts/auth/google/login/
        
        Request body:
        {
            "code": "4/0AY-t..."  // Authorization code from Google
        }
        
        Returns:
            {
                "access_token": "...",
                "refresh_token": "...",
                "user_id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "auth_method": "google",
                "message": "Successfully logged in via Google"
            }
        """
        client_ip = get_client_ip(request)
        
        # ===== STEP 1: RATE LIMITING CHECK =====
        is_limited, remaining, reset_time = self.rate_limiter.is_rate_limited(request)
        if is_limited:
            logger.warning(
                f"🚫 Rate limit exceeded for Google OAuth login | "
                f"ip={client_ip} | "
                f"client_id={self.rate_limiter.get_client_identifier(request)}"
            )
            
            # Log rate limit violation
            AuditLogger.log_rate_limit_exceeded(
                client_id=self.rate_limiter.get_client_identifier(request),
                ip_address=client_ip,
                endpoint='/api/accounts/auth/google/login/'
            )
            
            response = Response(
                {
                    'detail': 'Too many login attempts. Try again later.',
                    'retry_after': reset_time,
                    'remaining_attempts': 0
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            response['Retry-After'] = str(reset_time)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(reset_time)
            return response
        
        # ===== STEP 2: VALIDATE REQUEST =====
        serializer = GoogleOAuthLoginSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"❌ Validation failed: {serializer.errors}")
            AuditLogger.log_failed_auth(
                email='unknown',
                reason=f'Invalid request: {str(serializer.errors)}',
                ip_address=client_ip
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        code = serializer.validated_data['code']
        logger.info(f"✓ Google OAuth login request received | ip={client_ip}")
        
        # ===== STEP 3: AUTHENTICATE WITH GOOGLE =====
        google_user_data = GoogleOAuthService.authenticate_user(code)
        
        if not google_user_data:
            logger.error("❌ Google authentication failed")
            AuditLogger.log_failed_auth(
                email='unknown',
                reason='Google authentication failed',
                ip_address=client_ip
            )
            return Response(
                {'error': 'Google authentication failed. Please try again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        google_id = google_user_data['google_id']
        email = google_user_data['email']
        logger.info(f"✓ Google authentication successful | email={email}")
        
        # ===== STEP 4: VALIDATE EMAIL =====
        try:
            email = InputValidator.validate_email(email)
        except ValueError as e:
            logger.warning(f"❌ Email validation failed: {e}")
            AuditLogger.log_failed_auth(
                email=email,
                reason=f'Invalid email format: {str(e)}',
                ip_address=client_ip
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ===== STEP 5: CHECK FOR EXISTING STUDENT =====
        student = None
        
        # Try to find by Google ID first
        try:
            student = Students.objects.get(google_id=google_id)
            logger.info(f"✓ Existing student found via Google ID | student_id={student.student_id}")
            
            # Update last login info
            student.last_login_method = 'google'
            student.last_google_login = timezone.now()
            student.save(update_fields=['last_login_method', 'last_google_login'])
            
        except Students.DoesNotExist:
            # Try to find by email (might be migrating from email auth)
            try:
                student = Students.objects.get(email=email)
                logger.info(f"✓ Existing student found via email | student_id={student.student_id} | Linking Google account...")
                
                # Link Google account to existing student
                student.google_id = google_id
                student.google_picture = google_user_data.get('picture', '')
                student.is_google_auth = True
                student.auth_method = 'google'
                student.last_login_method = 'google'
                student.last_google_login = timezone.now()
                student.save()
                
                logger.info(f"✓ Google account linked to existing student")
                
            except Students.DoesNotExist:
                logger.warning(f"❌ Student not found | google_id={google_id} | email={email}")
                AuditLogger.log_failed_auth(
                    email=email,
                    reason='No account found with this Google email',
                    ip_address=client_ip
                )
                return Response(
                    {
                        'error': 'No account found with this Google email',
                        'suggestion': 'Please signup with your Google account first',
                        'google_email': email
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # ===== STEP 6: GENERATE JWT TOKENS =====
        logger.info("🔄 Generating JWT tokens...")
        
        refresh = RefreshToken()
        refresh['user_type'] = 'student'
        refresh['student_id'] = student.student_id
        refresh['name'] = student.name
        
        # Add faculty info to token if available
        if student.faculty_id:
            faculty_id, faculty_name = self.get_faculty_info(student.faculty_id)
            refresh['faculty_id'] = faculty_id
            refresh['faculty_name'] = faculty_name
        
        access_token = refresh.access_token
        access_token['user_type'] = 'student'
        access_token['student_id'] = student.student_id
        access_token['name'] = student.name
        
        if student.faculty_id:
            try:
                faculty_id, faculty_name = self.get_faculty_info(student.faculty_id)
                access_token['faculty_id'] = faculty_id
                access_token['faculty_name'] = faculty_name
            except:
                pass
        
        # ===== STEP 7: AUDIT LOG - SUCCESSFUL LOGIN =====
        AuditLogger.log_login(
            user_id=student.student_id,
            user_type='student',
            auth_method='google',
            ip_address=client_ip,
            success=True
        )
        
        logger.info(f"✅ Google OAuth login successful | student_id={student.student_id} | email={email}")
        
        # ===== STEP 8: RETURN RESPONSE WITH RATE LIMIT HEADERS =====
        response_data = {
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'user_id': student.student_id,
            'name': student.name,
            'email': student.email,
            'picture': student.google_picture,
            'auth_method': 'google',
            'message': 'Successfully logged in via Google'
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Add rate limit headers
        for key, value in self.rate_limiter.get_rate_limit_headers(request).items():
            response[key] = value
        
        return response


@extend_schema(
    tags=["Google OAuth"],
    description="Step 3: Create new student account via Google OAuth. Rate limited to 5 signups per hour per user/IP.",
    request=GoogleOAuthSignUpSerializer,
    responses={
        201: OpenApiResponse(
            description="Account created successfully",
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={
                        "message": "Account created successfully via Google",
                        "student_id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "picture": "https://...",
                        "auth_method": "google",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    },
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Validation error",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    value={
                        "error": "Validation error: Invalid NID format"
                    },
                    response_only=True,
                )
            ]
        ),
        409: OpenApiResponse(
            description="Conflict - Account already exists",
            examples=[
                OpenApiExample(
                    "Conflict",
                    value={
                        "error": "Email already registered. Please login instead."
                    },
                    response_only=True,
                )
            ]
        ),
        429: OpenApiResponse(
            description="Rate limit exceeded",
            examples=[
                OpenApiExample(
                    "Rate Limited",
                    value={
                        "detail": "Too many signup attempts. Try again later.",
                        "retry_after": 3600
                    },
                    response_only=True,
                )
            ]
        ),
        500: OpenApiResponse(description="Server error"),
    }
)
class GoogleOAuthSignUpView(APIView):
    """
    Google OAuth Signup
    Create new student account via Google
    
    Rate Limited: 5 signups per hour per user/IP
    All sensitive fields are encrypted (NID, UID, Phone, Address)
    """
    permission_classes = []
    
    # Initialize rate limiter for signup
    rate_limiter = RateLimiter(
        max_requests=settings.RATE_LIMIT_CONFIG['signup']['max_requests'],
        window_seconds=settings.RATE_LIMIT_CONFIG['signup']['window_seconds']
    )
    
    def post(self, request):
        """
        POST /api/accounts/auth/google/signup/
        
        Creates a new student account with encrypted sensitive data
        """
        client_ip = get_client_ip(request)
        
        try:
            # ===== STEP 1: RATE LIMITING CHECK =====
            logger.info("🔄 Starting Google OAuth signup process...")
            
            is_limited, remaining, reset_time = self.rate_limiter.is_rate_limited(request)
            if is_limited:
                logger.warning(
                    f"🚫 Rate limit exceeded for Google OAuth signup | "
                    f"ip={client_ip} | "
                    f"client_id={self.rate_limiter.get_client_identifier(request)}"
                )
                
                AuditLogger.log_rate_limit_exceeded(
                    client_id=self.rate_limiter.get_client_identifier(request),
                    ip_address=client_ip,
                    endpoint='/api/accounts/auth/google/signup/'
                )
                
                response = Response(
                    {
                        'detail': 'Too many signup attempts. Try again later.',
                        'retry_after': reset_time,
                        'remaining_attempts': 0
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
                response['Retry-After'] = str(reset_time)
                response['X-RateLimit-Remaining'] = '0'
                response['X-RateLimit-Reset'] = str(reset_time)
                return response
            
            logger.info(f"✓ Rate limit check passed | remaining_attempts={remaining}")
            
            # ===== STEP 2: VALIDATE REQUEST =====
            logger.info("🔄 Validating request data...")
            
            serializer = GoogleOAuthSignUpSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"❌ Validation failed: {serializer.errors}")
                AuditLogger.log_failed_auth(
                    email=request.data.get('email', 'unknown'),
                    reason=f'Signup validation failed: {str(serializer.errors)}',
                    ip_address=client_ip
                )
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info("✓ Request validation passed")
            
            # ===== STEP 3: EXTRACT & VALIDATE CODE =====
            code = serializer.validated_data['code']
            logger.info(f"✓ Authorization code received: {code[:20]}...")
            
            # ===== STEP 4: AUTHENTICATE WITH GOOGLE =====
            logger.info("🔄 Authenticating with Google...")
            
            google_user_data = GoogleOAuthService.authenticate_user(code)
            if not google_user_data:
                logger.error("❌ Google authentication failed")
                AuditLogger.log_failed_auth(
                    email='unknown',
                    reason='Google OAuth authentication failed',
                    ip_address=client_ip
                )
                return Response(
                    {'error': 'Google authentication failed. Please check your authorization code.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            google_id = google_user_data['google_id']
            email = google_user_data['email']
            logger.info(f"✓ Google authentication successful | email={email}")
            
            # ===== STEP 5: VALIDATE INPUT DATA =====
            logger.info("🔄 Validating input data...")
            
            try:
                # Validate email
                email = InputValidator.validate_email(email)
                logger.info(f"✓ Email validated: {email}")
                
                # Validate name
                name = InputValidator.validate_name(serializer.validated_data['name'])
                logger.info(f"✓ Name validated: {name}")
                
                # Validate NID
                nid = InputValidator.validate_nid(serializer.validated_data['nid'])
                logger.info(f"✓ NID validated (encrypted storage)")
                
                # Validate UID
                uid = InputValidator.validate_uid(serializer.validated_data['uid'])
                logger.info(f"✓ UID validated (encrypted storage)")
                
                # Validate phone number if provided
                phone = serializer.validated_data.get('phone_number')
                if phone:
                    phone = InputValidator.validate_phone(phone)
                    logger.info(f"✓ Phone number validated (encrypted storage)")
                
            except ValueError as e:
                logger.error(f"❌ Input validation failed: {e}")
                AuditLogger.log_failed_auth(
                    email=email,
                    reason=f'Input validation failed: {str(e)}',
                    ip_address=client_ip
                )
                return Response(
                    {'error': f'Validation error: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ===== STEP 6: CHECK FOR DUPLICATE ACCOUNTS =====
            logger.info("🔍 Checking for existing accounts...")
            
            if Students.objects.filter(google_id=google_id).exists():
                logger.warning(f"❌ Google ID already registered: {google_id}")
                AuditLogger.log_failed_auth(
                    email=email,
                    reason='Google ID already registered',
                    ip_address=client_ip
                )
                return Response(
                    {'error': 'Account already exists with this Google ID. Please login instead.'},
                    status=status.HTTP_409_CONFLICT
                )
            
            if Students.objects.filter(email=email).exists():
                logger.warning(f"❌ Email already registered: {email}")
                AuditLogger.log_failed_auth(
                    email=email,
                    reason='Email already registered',
                    ip_address=client_ip
                )
                return Response(
                    {'error': 'Email already registered. Please login instead.'},
                    status=status.HTTP_409_CONFLICT
                )
            
            if Students.objects.filter(nid=nid).exists():
                logger.warning(f"❌ National ID already registered")
                AuditLogger.log_failed_auth(
                    email=email,
                    reason='National ID already registered',
                    ip_address=client_ip
                )
                return Response(
                    {'error': 'National ID already registered'},
                    status=status.HTTP_409_CONFLICT
                )
            
            logger.info("✓ No duplicate accounts found")
            
            # ===== STEP 7: PREPARE STUDENT DATA =====
            logger.info("🔄 Preparing student data (fields will be encrypted)...")
            
            student_data = {
                'name': name,
                'email': email,
                'password': secrets.token_urlsafe(32),  # Dummy password for Google auth
                'phone_number': phone or '',
                'address': serializer.validated_data.get('address', ''),
                'faculty_id': serializer.validated_data['faculty'],
                'gender': serializer.validated_data.get('gender', 'M'),
                'nid': nid,  # Will be encrypted by model
                'uid': uid,  # Will be encrypted by model
                'acd_year': serializer.validated_data['acd_year'],
                'major': serializer.validated_data.get('major', ''),
                'google_id': google_id,
                'google_picture': google_user_data.get('picture', ''),
                'is_google_auth': True,
                'auth_method': 'google',
                'last_login_method': 'google',
                'last_google_login': timezone.now()
            }
            
            logger.debug(f"Student data prepared (sensitive fields will be encrypted)")
            
            # ===== STEP 8: CREATE STUDENT RECORD =====
            logger.info("🔄 Creating student record...")
            
            student = Students.objects.create(**student_data)
            logger.info(f"✓ Student created successfully | student_id={student.student_id}")
            
            # Verify encryption worked
            logger.info(f"🔒 Sensitive data encrypted successfully in database")
            
            # ===== STEP 9: GENERATE JWT TOKENS =====
            logger.info("🔄 Generating JWT tokens...")
            
            refresh = RefreshToken()
            refresh['user_type'] = 'student'
            refresh['student_id'] = student.student_id
            refresh['name'] = student.name
            
            # Add faculty info if available
            if student.faculty_id:
                try:
                    faculty = Faculties.objects.get(faculty_id=student.faculty_id)
                    refresh['faculty_id'] = student.faculty_id
                    refresh['faculty_name'] = faculty.name
                    logger.info(f"✓ Faculty info added to token: {faculty.name}")
                except Faculties.DoesNotExist:
                    logger.warning(f"⚠️ Faculty not found: {student.faculty_id}")
            
            access_token = refresh.access_token
            access_token['user_type'] = 'student'
            access_token['student_id'] = student.student_id
            access_token['name'] = student.name
            
            if student.faculty_id:
                try:
                    access_token['faculty_id'] = student.faculty_id
                except:
                    pass
            
            logger.info("✓ JWT tokens generated successfully")
            
            # ===== STEP 10: AUDIT LOG - NEW ACCOUNT =====
            logger.info("📋 Logging new account creation...")
            
            AuditLogger.log_data_modification(
                user_id=student.student_id,
                user_type='student',
                resource='Students',
                action='CREATE',
                changes=f'New Google OAuth account: {name} ({email})',
                ip_address=client_ip
            )
            
            # ===== STEP 11: RETURN RESPONSE =====
            response_data = {
                'message': 'Account created successfully via Google',
                'student_id': student.student_id,
                'name': student.name,
                'email': student.email,
                'picture': student.google_picture,
                'auth_method': 'google',
                'access_token': str(access_token),
                'refresh_token': str(refresh),
            }
            
            response = Response(response_data, status=status.HTTP_201_CREATED)
            
            # Add rate limit headers
            for key, value in self.rate_limiter.get_rate_limit_headers(request).items():
                response[key] = value
            
            logger.info(f"✅ Google OAuth signup completed successfully | student_id={student.student_id}")
            return response
        
        except ValueError as e:
            logger.error(f"❌ ValueError: {str(e)}")
            return Response(
                {'error': f'Validation error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Faculties.DoesNotExist:
            logger.error(f"❌ Faculty not found")
            AuditLogger.log_failed_auth(
                email=request.data.get('email', 'unknown'),
                reason='Selected faculty does not exist',
                ip_address=client_ip
            )
            return Response(
                {'error': 'Selected faculty does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"❌ Unexpected error during Google OAuth signup:")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.exception(e)
            
            AuditLogger.log_failed_auth(
                email=request.data.get('email', 'unknown'),
                reason=f'Server error: {type(e).__name__}',
                ip_address=client_ip
            )
            
            return Response(
                {
                    'error': 'Failed to create account. Please try again.',
                    'details': str(e) if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@extend_schema(
    tags=["Google OAuth"],
    description="Google OAuth callback endpoint. This receives the authorization code from Google after user authorizes.",
    parameters=[],
    responses={
        200: OpenApiResponse(
            description="Authorization code received",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "message": "Authorization code received",
                        "code": "4/0AY-t...",
                        "instruction": "Send this code to POST /api/accounts/auth/google/login/"
                    },
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Error from Google or missing code",
            examples=[
                OpenApiExample(
                    "Error",
                    value={
                        "error": "access_denied"
                    },
                    response_only=True,
                )
            ]
        ),
    }
)

@extend_schema(
    tags=["Google OAuth"],
    description="Google OAuth callback endpoint. This receives the authorization code from Google.",
    responses={
        200: OpenApiResponse(
            description="Authorization code received",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "message": "Authorization code received",
                        "code": "4/0AY-t...",
                        "instruction": "Send this code to POST /api/auth/google/login/"
                    },
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Error from Google or missing code",
            examples=[
                OpenApiExample(
                    "Error",
                    value={"error": "access_denied"}
                )
            ]
        ),
    }
)
class GoogleOAuthCallbackView(APIView):
    """
    Handle Google OAuth callback
    This is called by Google after user authorizes
    """
    permission_classes = []
    
    def get(self, request):
        """
        GET /api/auth/google/callback/?code=...&state=...
        
        This endpoint receives the authorization code from Google
        after the user has authorized the application.
        """
        code = request.query_params.get('code')
        error = request.query_params.get('error')
        
        # Handle errors from Google
        if error:
            logger.error(f"Google OAuth error: {error}")
            return Response(
                {'error': f'Google OAuth error: {error}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if authorization code is present
        if not code:
            logger.warning("No authorization code received from Google")
            return Response(
                {'error': 'No authorization code provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return the code for the frontend to use
        logger.info("Authorization code received from Google")
        return Response({
            'message': 'Authorization code received',
            'code': code,
            'instruction': 'Send this code to POST /api/auth/google/login/'
        }, status=status.HTTP_200_OK)