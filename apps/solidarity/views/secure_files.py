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
    
    def _serve_file_with_xaccel(self, file_path, filename, mime_type):
        """
        Serve file using X-Accel-Redirect (Nginx) or direct FileResponse (dev)
        Files are displayed inline in browser when possible
        
        Args:
            file_path: Absolute path to file
            filename: Original filename for display
            mime_type: MIME type of file
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
            response['Cache-Control'] = 'private, max-age=3600'  # Cache for 1 hour
            
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
            response['Cache-Control'] = 'private, max-age=3600'
            
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
