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
    }
)
class GoogleOAuthLoginView(APIView):
    """
    Step 2: Handle Google OAuth callback
    Exchange authorization code for tokens
    If student exists with this Google ID, login them
    """
    permission_classes = []
    
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
        POST /api/auth/google/login/
        
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
        # Validate request
        serializer = GoogleOAuthLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        code = serializer.validated_data['code']
        
        # Authenticate with Google
        google_user_data = GoogleOAuthService.authenticate_user(code)
        
        if not google_user_data:
            logger.warning("Google OAuth authentication failed")
            return Response(
                {'error': 'Google authentication failed. Please try again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        google_id = google_user_data['google_id']
        email = google_user_data['email']
        
        # Check if student with this Google ID exists
        try:
            student = Students.objects.get(google_id=google_id)
            logger.info(f"Existing student logged in via Google: {email}")
            
            # Update last login info
            student.last_login_method = 'google'
            student.last_google_login = timezone.now()
            student.save(update_fields=['last_login_method', 'last_google_login'])
            
        except Students.DoesNotExist:
            # Student doesn't exist with this Google ID
            # Check if email exists (might be migrating from email auth)
            try:
                student = Students.objects.get(email=email)
                logger.info(f"Linking Google account to existing student: {email}")
                
                # Link Google account to existing student
                student.google_id = google_id
                student.google_picture = google_user_data['picture']
                student.is_google_auth = True
                student.auth_method = 'google'
                student.last_login_method = 'google'
                student.last_google_login = timezone.now()
                student.save()
                
            except Students.DoesNotExist:
                logger.warning(f"Student not found for Google ID: {google_id}")
                return Response(
                    {
                        'error': 'No account found with this Google email',
                        'suggestion': 'Please signup with your Google account first',
                        'google_email': email
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Generate JWT tokens
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
            access_token['faculty_id'] = faculty_id
            access_token['faculty_name'] = faculty_name
        
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
        
        logger.info(f"Student {student.student_id} successfully logged in via Google")
        return Response(response_data, status=status.HTTP_200_OK)



@extend_schema(
    tags=["Google OAuth"],
    description="Step 3: Create new student account via Google OAuth.",
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
        400: OpenApiResponse(description="Validation error"),
        409: OpenApiResponse(description="Conflict - Account already exists"),
        500: OpenApiResponse(description="Server error"),
    }
)
class GoogleOAuthSignUpView(APIView):
    """
    Google OAuth Signup
    Create new student account via Google
    """
    permission_classes = []
    
    def post(self, request):
        """
        POST /api/auth/google/signup/
        """
        try:
            # ===== STEP 1: Validate Input =====
            logger.info("🔄 Starting Google OAuth signup...")
            
            serializer = GoogleOAuthSignUpSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"❌ Validation failed: {serializer.errors}")
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info("✓ Request validation passed")
            
            # ===== STEP 2: Extract Code =====
            code = serializer.validated_data['code']
            logger.info(f"✓ Authorization code received: {code[:20]}...")
            
            # ===== STEP 3: Authenticate with Google =====
            logger.info("🔄 Authenticating with Google...")
            google_user_data = GoogleOAuthService.authenticate_user(code)
            
            if not google_user_data:
                logger.error("❌ Google authentication failed")
                return Response(
                    {'error': 'Google authentication failed. Please check your authorization code.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            logger.info(f"✓ Google authentication successful for: {google_user_data.get('email')}")
            
            google_id = google_user_data['google_id']
            email = google_user_data['email']
            
            # ===== STEP 4: Check for Existing Accounts =====
            logger.info("🔍 Checking for existing accounts...")
            
            if Students.objects.filter(google_id=google_id).exists():
                logger.warning(f"❌ Account already exists with this Google ID: {google_id}")
                return Response(
                    {'error': 'Account already exists with this Google ID. Please login instead.'},
                    status=status.HTTP_409_CONFLICT
                )
            
            if Students.objects.filter(email=email).exists():
                logger.warning(f"❌ Email already registered: {email}")
                return Response(
                    {'error': 'Email already registered. Please login instead.'},
                    status=status.HTTP_409_CONFLICT
                )
            
            nid = serializer.validated_data['nid']
            if Students.objects.filter(nid=nid).exists():
                logger.warning(f"❌ National ID already registered: {nid}")
                return Response(
                    {'error': 'National ID already registered'},
                    status=status.HTTP_409_CONFLICT
                )
            
            logger.info("✓ No existing accounts found")
            
            # ===== STEP 5: Prepare Student Data =====
            logger.info("🔄 Preparing student data...")
            
            student_data = {
                'name': serializer.validated_data['name'],
                'email': email,
                'password': secrets.token_urlsafe(32),
                'phone_number':serializer.validated_data['phone_number'],  # ← ADD THIS
                'address':serializer.validated_data.get('address', ''),     # ← ADD THIS
                'faculty_id': serializer.validated_data['faculty'],
                'gender': serializer.validated_data.get('gender', 'M'),
                'nid': nid,
                'uid': serializer.validated_data['uid'],
                'acd_year': serializer.validated_data['acd_year'],
                'major': serializer.validated_data.get('major', ''),
                'google_id': google_id,
                'google_picture': google_user_data.get('picture', ''),
                'is_google_auth': True,
                'auth_method': 'google',
                'last_login_method': 'google',
                'last_google_login': timezone.now()
            }
            
            logger.debug(f"Student data: {student_data}")
            
            # ===== STEP 6: Create Student =====
            logger.info("🔄 Creating student record...")
            
            student = Students.objects.create(**student_data)
            
            logger.info(f"✓ Student created successfully: {student.student_id}")
            
            # ===== STEP 7: Generate JWT Tokens =====
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
                    logger.info(f"✓ Faculty info added: {faculty.name}")
                except Faculties.DoesNotExist:
                    logger.warning(f"⚠️ Faculty not found: {student.faculty_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Error adding faculty info: {str(e)}")
            
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
            
            # ===== STEP 8: Return Success Response =====
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
            
            logger.info(f"✓ Google OAuth signup completed for: {student.email}")
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            logger.error(f"❌ ValueError: {str(e)}")
            return Response(
                {'error': f'Validation error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Students.DoesNotExist as e:
            logger.error(f"❌ Student not found: {str(e)}")
            return Response(
                {'error': 'Student record error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Faculties.DoesNotExist as e:
            logger.error(f"❌ Faculty not found: {str(e)}")
            return Response(
                {'error': 'Selected faculty does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"❌ Unexpected error during Google OAuth signup:")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.exception(e)  # Print full traceback
            
            return Response(
                {
                    'error': 'Failed to create account. Please try again.',
                    'details': str(e) if getattr(settings, 'DEBUG', False) else None
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