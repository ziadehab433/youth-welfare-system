import os
import json
import logging
import hashlib
from django.conf import settings
from django.core.cache import cache
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
from .utils import generate_pdf_sync, PDFRenderer, get_report_assets
from .serializers import EventReportSerializer

logger = logging.getLogger(__name__)

def build_pdf_response(pdf_buffer, filename):
    filename_encoded = quote(filename)

    response = HttpResponse(
        pdf_buffer,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"; '
        f"filename*=UTF-8''{filename_encoded}"
    )

    response["Content-Length"] = len(pdf_buffer)
    response["Access-Control-Expose-Headers"] = "Content-Disposition"

    return response
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
                response={"type": "string", "format": "binary"}
            ),
            400: OpenApiResponse(description="Invalid data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Event not found"),
            500: OpenApiResponse(description="Error generating PDF")
        }
    )
    @action(detail=True, methods=["post"], url_path="pdf")
    def export_pdf(self, request, pk=None):
        try:

            event = get_object_or_404(
                Events.objects.select_related("faculty", "dept"),
                pk=pk
            )

            admin = get_current_admin(request)

            if admin.role == "مسؤول كلية" and event.faculty_id != admin.faculty_id:
                return Response(
                    {"detail": "You do not have permission to view this report"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = EventReportSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = serializer.validated_data
            sorted_data = json.dumps(data, sort_keys=True, default=str)

            hash_part = hashlib.sha256(
                sorted_data.encode("utf-8")
            ).hexdigest()

            cache_key = (
                f"pdf_event_report_"
                f"{event.event_id}_"
                f"{event.updated_at.timestamp()}_"
                f"{hash_part}"
            )

            cached_pdf = cache.get(cache_key)

            if cached_pdf:
                logger.info(
                    f"PDF for event {event.event_id} served from cache"
                )

                filename = f"event_report_{event.event_id}.pdf"

                return build_pdf_response(
                    cached_pdf,
                    filename
                )
            participants = (
                Prtcps.objects
                .filter(event=event, status="مقبول")
                .select_related("student")
            )

            event_title = data.get("event_title", event.title)
            event_code = data.get("event_code", event.event_id)

            male_count = data.get("male_count")
            if male_count is None:
                male_count = participants.filter(
                    student__gender="M"
                ).count()

            female_count = data.get("female_count")
            if female_count is None:
                female_count = participants.filter(
                    student__gender="F"
                ).count()

            total_participants = data.get("total_participants")
            if total_participants is None:
                total_participants = male_count + female_count

            start_date = data.get("start_date")
            if start_date is None and event.st_date:
                start_date = event.st_date.strftime("%Y / %m / %d")

            duration_days = data.get("duration_days")

            if duration_days is None and event.st_date and event.end_date:
                duration_days = (event.end_date - event.st_date).days
            elif duration_days is None:
                duration_days = 0

            assets = get_report_assets()

            report_data = {
                "event_title": event_title,
                "event_code": event_code,
                "male_count": male_count,
                "female_count": female_count,
                "total_participants": total_participants,
                "start_date": start_date,
                "duration_days": duration_days,
                "issue_date": timezone.now(),
                "logo_base64": assets["logo"],
                "font_base64": assets["font"],
                "base_url": request.build_absolute_uri("/").rstrip("/"),
                "STATIC_URL": settings.STATIC_URL,

                "project_stages": data.get("project_stages", ""),
                "preparation_stage": data.get("preparation_stage", ""),
                "execution_stage": data.get("execution_stage", ""),
                "evaluation_stage": data.get("evaluation_stage", ""),
                "achieved_goals": data.get("achieved_goals", ""),

                "issue_date_ar": timezone.now().strftime("%Y/%m/%d"),
                "issue_date_en": timezone.now().strftime("%Y-%m-%d"),

                "committees": {
                    "preparation": data.get("committee_preparation", ""),
                    "organizing": data.get("committee_organizing", ""),
                    "execution": data.get("committee_execution", ""),
                    "purchases": data.get("committee_purchases", ""),
                    "supervision": data.get("committee_supervision", ""),
                    "other": data.get("committee_other", ""),
                },

                "evaluation": data.get("evaluation", ""),
                "suggestions": data.get("suggestions", []),
                "current_page": 1,
                "total_pages": 2,
            }
            filename = f"event_report_{event.event_id}.pdf"

            html_string = render_to_string(
                "event/event_evaluation_report.html",
                report_data
            )

            pdf_buffer = generate_pdf_sync(html_string)

            cache.set(
                cache_key,
                pdf_buffer,
                timeout=60 * 60 * 24
            )

            logger.info(
                f"PDF for event {event.event_id} generated and cached"
            )

            return build_pdf_response(
                pdf_buffer,
                filename
            )

        except Exception as e:
            logger.exception(
                "Error generating PDF for event %s: %s",
                pk,
                str(e)
            )

            return Response(
                {"detail": "Error generating PDF"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )