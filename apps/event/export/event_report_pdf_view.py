import os
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
from apps.event.models import Events, Prtcps
from apps.accounts.utils import get_current_admin
from .utils import generate_pdf_from_html, PDFRenderer, get_report_assets
from .serializers import EventReportSerializer

logger = logging.getLogger(__name__)

class EventReportViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [PDFRenderer]
    
    def get_queryset(self):
        return Events.objects.none()
    
    @extend_schema(
        tags=["Events APIs"],
        description="Export event evaluation report as PDF file",
        request=EventReportSerializer,
        responses={
            200: OpenApiResponse(
                description="PDF report generated successfully",
                response={'type': 'string', 'format': 'binary'}
            ),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Event not found"),
            500: OpenApiResponse(description="Error generating PDF")
        }
    )
    @action(detail=True, methods=['post'], url_path='pdf')
    def export_pdf(self, request, pk=None):
        try:
            event = get_object_or_404(Events.objects.select_related('faculty', 'dept'), pk=pk)
            admin = get_current_admin(request)
            
            if admin.role == 'مسؤول كلية' and event.faculty_id != admin.faculty_id:
                return HttpResponse("You do not have permission to view this report", status=403)
            
            serializer = EventReportSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            data = serializer.validated_data
            event_title = data.get('event_title', event.title)
            event_code = data.get('event_code', event.event_id)
            male_count = data.get('male_count')
            if male_count is None:
                male_count = Prtcps.objects.filter(
                    event=event, status='مقبول', student__gender='M'
                ).count()
            
            female_count = data.get('female_count')
            if female_count is None:
                female_count = Prtcps.objects.filter(
                    event=event, status='مقبول', student__gender='F'
                ).count()
            
            total_participants = data.get('total_participants')
            if total_participants is None:
                total_participants = male_count + female_count
            
            start_date = data.get('start_date')
            if start_date is None and event.st_date:
                start_date = event.st_date.strftime("%Y / %m / %d")
            
            duration_days = data.get('duration_days')
            if duration_days is None and event.st_date and event.end_date:
                duration_days = (event.end_date - event.st_date).days
            elif duration_days is None:
                duration_days = 0
            
            assets = get_report_assets()
            
            report_data = {
                'event_title': event_title,
                'event_code': event_code,
                'male_count': male_count,
                'female_count': female_count,
                'total_participants': total_participants,
                'start_date': start_date,
                'duration_days': duration_days,
                'issue_date': timezone.now(),
                'logo_base64': assets['logo'],
                'font_base64': assets['font'],
                'base_url': request.build_absolute_uri('/').rstrip('/'),
                'STATIC_URL': settings.STATIC_URL,
                'project_stages': data.get('project_stages', ''),
                'preparation_stage': data.get('preparation_stage', ''),
                'execution_stage': data.get('execution_stage', ''),
                'evaluation_stage': data.get('evaluation_stage', ''),
                'achieved_goals': data.get('achieved_goals', ''),
                'issue_date_ar': timezone.now().strftime('%Y/%m/%d'), 
                'issue_date_en': timezone.now().strftime('%Y-%m-%d'),  
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