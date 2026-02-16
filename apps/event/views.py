import os
import base64
import logging
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from urllib.parse import quote
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated 
from rest_framework.renderers import BaseRenderer
from apps.event.models import Plans, Events
from apps.event.pdf_utils import generate_pdf_sync
logger = logging.getLogger(__name__)

class PDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'
    charset = None
    render_style = 'binary'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

@extend_schema(
    tags=["Events APIs"],
    summary="Export Plan PDF",
    description="Export plan activities as PDF file",
    responses={
        200: OpenApiResponse(
            description="PDF file generated successfully",
            response={'type': 'string', 'format': 'binary'}
        ),
        404: OpenApiResponse(description="Plan not found"),
        500: OpenApiResponse(description="Error generating PDF")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])  
@renderer_classes([PDFRenderer])
def export_plan_pdf(request, plan_id):
    try:
        plan = get_object_or_404(
            Plans.objects.select_related('faculty'), 
            pk=plan_id
        )
        events = Events.objects.filter(
            plan=plan
        ).annotate(
            males=Count('prtcps_set', filter=Q(prtcps_set__student__gender='M', prtcps_set__status='مقبول')),
            females=Count('prtcps_set', filter=Q(prtcps_set__student__gender='F', prtcps_set__status='مقبول')),
            total_p=Count('prtcps_set', filter=Q(prtcps_set__status='مقبول'))
        ).order_by('type', 'st_date')
        grouped_data = {}
        total_cost = 0
        total_males = 0
        total_females = 0
        total_participants = 0
        for event in events:
            etype = event.type or "أنشطة متنوعة"
            if etype not in grouped_data:
                grouped_data[etype] = []
            grouped_data[etype].append(event)
            total_cost += (event.cost or 0)
            total_males += (event.males or 0)
            total_females += (event.females or 0)
            total_participants += (event.total_p or 0)
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
        
        faculty = plan.faculty
        context = {
            'plan': plan,
            'plan_name': plan.name,
            'plan_term': plan.term,
            'university_name': "جامعة حلوان",
            'faculty_name': faculty.name if faculty else "كلية الحاسبات والذكاء الاصطناعي",
            'office_name': "إدارة رعاية الشباب",
            'events': events,
            'grouped_data': grouped_data,
            'total_events': events.count(),
            'total_cost': total_cost,
            'total_males': total_males,
            'total_females': total_females,
            'total_participants': total_participants,
            'signature_1_title': "مسئول الأنشطة",
            'signature_1_name': "",
            'signature_2_title': "أمين الكلية",
            'signature_2_name': "",
            'signature_3_title': "وكيل الكلية لشئون التعليم والطلاب",
            'signature_3_name': "",
            'font_base64': font_base64, 
            'logo_base64': logo_base64,  
            'base_url': request.build_absolute_uri('/').rstrip('/'),
            'STATIC_URL': settings.STATIC_URL,
        }
        html_string = render_to_string('event/activity_report.html', context)
        pdf_buffer = generate_pdf_sync(html_string)  
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        filename = f"plan_{plan_id}.pdf" 
        encoded_filename = quote(filename)
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
        response['Content-Length'] = len(pdf_buffer)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'  
        
        return response
    except Exception as e:
        import traceback
        logger.exception("Error generating PDF for plan %s: %s", plan_id, str(e))
        print(traceback.format_exc())
        return HttpResponse(f"Error: {str(e)}", status=500)