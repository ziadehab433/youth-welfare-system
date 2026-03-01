import os
import base64
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from urllib.parse import quote
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.event.models import Events, Prtcps, EventDocs
from apps.accounts.utils import get_current_admin
from .utils import generate_pdf_sync, PDFRenderer, get_report_assets

logger = logging.getLogger(__name__)

class EventSummaryReportViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [PDFRenderer]
    
    def get_queryset(self):
        return Events.objects.none()
    
    @extend_schema(
        tags=["Events APIs"],
        description="Export event summary report as PDF with photos",
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
    @action(detail=True, methods=['get'], url_path='summary-pdf')
    def export_summary_pdf(self, request, pk=None):
        try:
            event = get_object_or_404(
                Events.objects.select_related('faculty', 'dept'), 
                pk=pk
            )
            admin = get_current_admin(request)
            
            if admin.role == 'مسؤول كلية' and event.faculty_id != admin.faculty_id:
                return HttpResponse("ليس لديك صلاحية لعرض هذا التقرير", status=403)
            
            faculty = event.faculty
            university_name = "جامعة العاصمة"  
            faculty_name = faculty.name if faculty else "كلية الحاسبات والذكاء الاصطناعي"
            office_name = "إدارة رعاية الشباب"
            
            participants = Prtcps.objects.filter(
                event=event,
                status='مقبول'
            ).select_related('student')
            
            male_count = participants.filter(student__gender='M').count()
            female_count = participants.filter(student__gender='F').count()
            total_participants = male_count + female_count
            
            if event.st_date and event.end_date:
                duration_days = (event.end_date - event.st_date).days
                if duration_days == 0:
                    duration_days = 1
            else:
                duration_days = 0
            
            event_images = EventDocs.objects.filter(
                event=event,
                doc_type='image'
            )[:2]
            
            images_base64 = []
            for img in event_images[:2]:
                try:
                    img_path = os.path.join(settings.MEDIA_ROOT, img.file_path)
                    if os.path.exists(img_path):
                        with open(img_path, 'rb') as f:
                            img_base64 = base64.b64encode(f.read()).decode('ascii')
                            images_base64.append(img_base64)
                    else:
                        images_base64.append(None)
                except Exception as e:
                    logger.warning(f"Error loading image {img.file_path}: {e}")
                    images_base64.append(None)
            
            while len(images_base64) < 2:
                images_base64.append(None)
            
            assets = get_report_assets()
            event_date_str = event.st_date.strftime("%Y/%m/%d") if event.st_date else ''
            
            report_data = {
                'logo_base64': assets['logo'],
                'university_name': university_name,
                'faculty_name': faculty_name,
                'office_name': office_name,
                'event_type': event.type,
                'event_title': event.title,
                'preparation_stage': event.description,
                'start_date': event_date_str,
                'end_date': event.end_date.strftime("%Y/%m/%d") if event.end_date else '',
                'duration_days': duration_days,
                'total_participants': total_participants,
                'location': event.location,
                'event_date': event_date_str, 
                'image1_base64': images_base64[0],
                'image2_base64': images_base64[1],
            }
            
            filename = f"event_summary_{event.event_id}.pdf"
            html_string = render_to_string('event/event_summary_report.html', report_data)
            pdf_buffer = generate_pdf_sync(html_string)
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            filename_encoded = quote(filename)
            response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename_encoded}'
            response['Content-Length'] = len(pdf_buffer)
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            
            return response
            
        except Exception as e:
            logger.exception("Error generating summary PDF for event %s: %s", pk, str(e))
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)