"""
Secure file serving views for solidarity documents
Uses X-Accel-Redirect for efficient file serving through Nginx
"""
import os
import logging
from django.conf import settings
from django.http import FileResponse, HttpResponse, Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.permissions import IsRole
from apps.accounts.utils import get_current_admin, get_current_student, get_client_ip, log_data_access
from apps.solidarity.models import SolidarityDocs, Solidarities
from apps.solidarity.services.solidarity_service import SolidarityService

logger = logging.getLogger(__name__)


class SecureSolidarityFileViewSet(viewsets.GenericViewSet):
    """
    Secure file access for solidarity documents
    Requires authentication and permission checks
    """
    permission_classes = [IsAuthenticated]
    
    def _serve_file_with_xaccel(self, file_path, filename, mime_type, enable_cache=True):
        """
        Serve file using X-Accel-Redirect (Nginx) or direct FileResponse (dev)
        Files are displayed inline in browser when possible
        
        Args:
            file_path: Absolute path to file
            filename: Original filename for display
            mime_type: MIME type of file
            enable_cache: If True, allows browser caching (default). If False, disables all caching.
        """
        if not os.path.exists(file_path):
            raise Http404("File not found")
        
        # Ensure correct MIME type (fallback to octet-stream if unknown)
        content_type = mime_type or 'application/octet-stream'
        
        # Production: Use X-Accel-Redirect for Nginx
        if getattr(settings, 'USE_X_ACCEL_REDIRECT', False):
            # Convert absolute path to relative path for Nginx
            relative_path = file_path.replace(settings.MEDIA_ROOT, '').lstrip('/')
            internal_url = f"{settings.PRIVATE_MEDIA_URL}{relative_path}"
            
            response = HttpResponse()
            response['X-Accel-Redirect'] = internal_url
            response['Content-Type'] = content_type
            
            # Display inline in browser (not download)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            # Browser compatibility headers
            response['X-Content-Type-Options'] = 'nosniff'
            
            # Cache control based on file type
            if enable_cache:
                # Allow caching for static documents (solidarity docs)
                response['Cache-Control'] = 'private, max-age=3600'  # Cache for 1 hour
            else:
                # Disable caching for dynamic content (profile images)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            logger.info(f"Serving file via X-Accel-Redirect: {internal_url}")
            return response
        
        # Development: Direct file serving
        else:
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type
            )
            
            # Display inline in browser (not download)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            # Browser compatibility headers
            response['X-Content-Type-Options'] = 'nosniff'
            
            # Cache control based on file type
            if enable_cache:
                # Allow caching for static documents (solidarity docs)
                response['Cache-Control'] = 'private, max-age=3600'
            else:
                # Disable caching for dynamic content (profile images)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            logger.info(f"Serving file directly (dev mode): {file_path}")
            return response
    
    @extend_schema(
        tags=["Secure Files - Solidarity"],
        description="View/display a specific solidarity document inline in browser (requires authentication and permission)",
        responses={
            200: OpenApiResponse(description="File content displayed inline"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="File not found")
        }
    )
    @action(detail=True, methods=['get'], url_path='download')
    def download_solidarity_document(self, request, pk=None):
        """
        View/display solidarity document by doc_id (inline in browser)
        
        Permission rules:
        - Students: Can only access their own solidarity documents
        - Faculty admins: Can access documents from their faculty
        - Dept/Super admins: Can access all documents
        """
        try:
            # Get document
            doc = SolidarityDocs.objects.select_related(
                'solidarity', 'solidarity__student', 'solidarity__faculty'
            ).get(doc_id=pk)
            
            solidarity = doc.solidarity
            
            # Determine user type and check permissions
            user = request.user
            
            if hasattr(user, 'student_id'):  # Student user
                student = get_current_student(request)
                if solidarity.student_id != student.student_id:
                    logger.warning(
                        f"Student {student.student_id} attempted to access "
                        f"solidarity document {pk} belonging to student {solidarity.student_id}"
                    )
                    return Response(
                        {'error': 'You can only access your own documents'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            elif hasattr(user, 'admin_id'):  # Admin user
                admin = get_current_admin(request)
                
                # Faculty admin: can only access documents from their faculty
                if admin.role == 'مسؤول كلية':
                    if solidarity.faculty_id != admin.faculty_id:
                        logger.warning(
                            f"Faculty admin {admin.admin_id} attempted to access "
                            f"solidarity document {pk} from different faculty"
                        )
                        return Response(
                            {'error': 'You can only access documents from your faculty'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                
                # Dept/Super admins: full access (no additional checks)
            
            else:
                return Response(
                    {'error': 'Invalid user type'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Log file access
            client_ip = get_client_ip(request)
            actor_id = getattr(user, 'admin_id', None) or getattr(user, 'student_id', None)

            

            
            # Serve file
            file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
            return self._serve_file_with_xaccel(
                file_path=file_path,
                filename=doc.file.name.split('/')[-1],
                mime_type=doc.mime_type
            )
        
        except SolidarityDocs.DoesNotExist:
            logger.warning(f"Document {pk} not found")
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"Error serving solidarity document {pk}: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to serve file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class SecureProfileImageViewSet(viewsets.GenericViewSet):
    """
    Secure file access for student profile images
    Requires authentication and permission checks
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Secure Files - Students"],
        description="View/display student profile image (requires authentication and permission)",
        responses={
            200: OpenApiResponse(description="Profile image displayed inline"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Profile image not found")
        }
    )
    @action(detail=True, methods=['get'], url_path='image')
    def view_profile_image(self, request, pk=None):
        """
        View/display student profile image by student_id
        
        Permission rules:
        - Students: Can only access their own profile image
        - Admins: Can access any student's profile image
        """
        try:
            # Import here to avoid circular imports
            from apps.accounts.models import Students
            
            # Get student
            student = Students.objects.get(student_id=pk)
            
            # Check if profile photo exists
            if not student.profile_photo:
                return Response(
                    {'error': 'No profile photo available'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determine user type and check permissions
            user = request.user
            
            if hasattr(user, 'student_id'):  # Student user
                current_student = get_current_student(request)
                if int(pk) != current_student.student_id:
                    logger.warning(
                        f"Student {current_student.student_id} attempted to access "
                        f"profile image of student {pk}"
                    )
                    return Response(
                        {'error': 'You can only access your own profile image'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            elif hasattr(user, 'admin_id'):  # Admin user
                # Admins can access any student profile image
                pass
            
            else:
                return Response(
                    {'error': 'Invalid user type'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Log file access
            client_ip = get_client_ip(request)
            actor_id = getattr(user, 'admin_id', None) or getattr(user, 'student_id', None)

            
            # Determine MIME type from file extension
            file_extension = os.path.splitext(student.profile_photo)[1].lower()
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_extension, 'image/jpeg')
            
            # Serve file using the existing helper method from SecureSolidarityFileViewSet
            file_path = os.path.join(settings.MEDIA_ROOT, student.profile_photo)
            filename = os.path.basename(student.profile_photo)
            
            # Use the same _serve_file_with_xaccel method with caching disabled
            return SecureSolidarityFileViewSet()._serve_file_with_xaccel(
                file_path=file_path,
                filename=filename,
                mime_type=mime_type,
                enable_cache=False  # Disable caching for profile images
            )
        
        except Students.DoesNotExist:
            logger.warning(f"Student {pk} not found")
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"Error serving profile image for student {pk}: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to serve profile image'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
