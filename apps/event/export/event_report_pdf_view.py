import os
import base64
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from urllib.parse import quote
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.event.models import Events, Prtcps
from apps.accounts.utils import get_current_admin
from .utils import generate_pdf_from_html

logger = logging.getLogger(__name__)

class PDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'
    charset = None
    render_style = 'binary'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
    
class EventReportViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [PDFRenderer]
    
    def get_queryset(self):
        return Events.objects.none()
    
    @extend_schema(
        tags=["Events APIs"],
        description="Export event evaluation report as PDF file",
        responses={
            200: OpenApiResponse(
                description="PDF report generated successfully",
                response={'type': 'string', 'format': 'binary'}
            ),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Event not found"),
            500: OpenApiResponse(description="Error generating PDF")
        }
    )
    @action(detail=True, methods=['get'], url_path='pdf')
    def export_pdf(self, request, pk=None):
        try:
            event = get_object_or_404(Events.objects.select_related('faculty', 'dept'), pk=pk)
            admin = get_current_admin(request)
            if admin.role == 'مسؤول كلية' and event.faculty_id != admin.faculty_id:
                return HttpResponse("ليس لديك صلاحية لعرض هذا التقرير", status=403)
            participants = Prtcps.objects.filter(
                event=event,
                status='مقبول'
            ).select_related('student')   
            male_count = participants.filter(student__gender='M').count()
            female_count = participants.filter(student__gender='F').count()
            if event.st_date and event.end_date:
                duration_days = (event.end_date - event.st_date).days
            else:
                duration_days = 0
            logo_base64 = ""
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo', 'logo.png')
            if os.path.exists(logo_path):
                try:
                    with open(logo_path, 'rb') as f:
                        logo_base64 = base64.b64encode(f.read()).decode('ascii')
                    logger.info("Logo loaded as base64: %s", logo_path)
                except Exception as e:
                    logger.warning("Logo error: %s", e)
            else:
                logger.warning("Logo not found at: %s", logo_path)
            font_base64 = ""
            possible_paths = [
                os.path.join(settings.STATIC_ROOT, 'fonts', 'Amiri-Regular.ttf'),
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf'),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        with open(path, 'rb') as f:
                            font_base64 = base64.b64encode(f.read()).decode('ascii')
                        logger.info("Font loaded as base64: %s", path)
                        break
                    except Exception as e:
                        logger.warning("Font error: %s", e)
            report_data = {
                'event': event,
                'male_count': male_count,
                'female_count': female_count,
                'total_participants': participants.count(),
                'duration_days': duration_days,
                'issue_date': timezone.now(),
                'participants': participants,
                'show_participants': participants.count() > 0,
                'logo_base64': logo_base64,  
                'font_base64': font_base64,  
                'base_url': request.build_absolute_uri('/').rstrip('/'),
                'STATIC_URL': settings.STATIC_URL,
            }
            filename = f"event_report_{event.event_id}.pdf"
            folder_path = os.path.join(settings.MEDIA_ROOT, 'event_reports')
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            full_path = os.path.join(folder_path, filename)
            html_string = render_to_string('event/event_report.html', report_data)
            success = generate_pdf_from_html(html_string, full_path)
            
            if not success:
                return HttpResponse("Error generating PDF", status=500)
            with open(full_path, 'rb') as pdf_file:
                pdf_buffer = pdf_file.read()
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            filename_encoded = quote(filename)
            response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename_encoded}'
            response['Content-Length'] = len(pdf_buffer)
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            
            return response
        except Exception as e:
            logger.exception("Error generating PDF for event %s: %s", pk, str(e))
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)