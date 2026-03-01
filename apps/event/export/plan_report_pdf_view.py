import os
import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Sum
from urllib.parse import quote
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from apps.event.models import Plans, Events
from .utils import generate_pdf_sync, PDFRenderer, get_report_assets

logger = logging.getLogger(__name__)

@extend_schema(
    tags=["Events APIs"],
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
        
        cache_key = f"plan_pdf_{plan_id}_{plan.updated_at.timestamp()}"
        cached_pdf = cache.get(cache_key)
        if cached_pdf:
            logger.info(f"PDF for plan {plan_id} served from cache")
            response = HttpResponse(cached_pdf, content_type='application/pdf')
            filename = f"plan_{plan_id}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(cached_pdf)
            return response
        
        events = Events.objects.filter(
            plan=plan
        ).annotate(
            males=Count('prtcps_set', filter=Q(prtcps_set__student__gender='M', prtcps_set__status='مقبول')),
            females=Count('prtcps_set', filter=Q(prtcps_set__student__gender='F', prtcps_set__status='مقبول')),
            total_p=Count('prtcps_set', filter=Q(prtcps_set__status='مقبول'))
        ).order_by('type', 'st_date')
        
        totals = events.aggregate(
            total_cost=Sum('cost'),
            total_males=Sum('males'),
            total_females=Sum('females'),
            total_participants=Sum('total_p')
        )
        
        grouped_data = {}
        for event in events:
            etype = event.type or "أنشطة متنوعة"
            if etype not in grouped_data:
                grouped_data[etype] = []
            grouped_data[etype].append(event)
        
        assets = get_report_assets()
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
            'total_cost': totals['total_cost'] or 0,
            'total_males': totals['total_males'] or 0,
            'total_females': totals['total_females'] or 0,
            'total_participants': totals['total_participants'] or 0,
            'signature_1_title': "مسئول الأنشطة",
            'signature_1_name': "",
            'signature_2_title': "أمين الكلية",
            'signature_2_name': "",
            'signature_3_title': "وكيل الكلية لشئون التعليم والطلاب",
            'signature_3_name': "",
            'font_base64': assets['font'],
            'logo_base64': assets['logo'],
            'base_url': request.build_absolute_uri('/').rstrip('/'),
            'STATIC_URL': settings.STATIC_URL,
        }
        
        html_string = render_to_string('event/activity_report.html', context)
        pdf_buffer = generate_pdf_sync(html_string)
        
        cache.set(cache_key, pdf_buffer, timeout=60 * 60)
        logger.info(f"PDF for plan {plan_id} generated and cached")
        
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