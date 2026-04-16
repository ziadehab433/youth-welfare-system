import logging
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from apps.event.models import Events
from apps.event.serializers import EventSerializer
from apps.family.serializers import EventDetailSerializer
from apps.family.models import Families
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.accounts.mixins import AdminActionMixin

logger = logging.getLogger(__name__)

STATUS_PENDING = 'منتظر'
STATUS_APPROVED = 'مقبول'
STATUS_REJECTED = 'مرفوض'

@extend_schema(tags=["Family Fac Admin APIs"])
class FacultyEventApprovalViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer

    def get_queryset(self):
        admin = get_current_admin(self.request)
        return Events.objects.filter(
            faculty_id=admin.faculty_id
        ).exclude(
            family__type='مركزية'
        )

    @extend_schema(
        description="List pending events for families within this faculty.",
        responses={200: EventSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        events = self.get_queryset().filter(status=STATUS_PENDING)
        return Response(self.get_serializer(events, many=True).data)

    @extend_schema(
        description="Get event details including registered members.",
        responses={200: EventDetailSerializer}
    )
    def retrieve(self, request, pk=None):
        event = self.get_object()
        return Response(self.get_serializer(event).data)

    def _set_event_status(self, request, pk, new_status, action_name):
        event = self.get_object()
        if event.status != STATUS_PENDING:
            return Response(
                {"error": "This event is not pending approval"},
                status=status.HTTP_400_BAD_REQUEST
            )

        def business_operation(admin, ip):
            event.status = new_status
            event.save()
            status_msg = "Event approved successfully" if new_status == STATUS_APPROVED else "Event rejected successfully"
            return {"message": status_msg}

        result = self.execute_admin_action(
            request=request,
            action_name=action_name,
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id
        )
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        description="Approve an event for a faculty family.",
        request=None,
        responses={200: OpenApiResponse(description="Event approved")}
    )
    @action(detail=True, methods=['post'], url_path='approve')
    @require_permission('update')
    def approve(self, request, pk=None):
        event = self.get_object()
        return self._set_event_status(
            request, pk, STATUS_APPROVED,
            f"الموافقة على نشاط: {event.title}"
        )

    @extend_schema(
        description="Reject an event for a faculty family.",
        request=None,
        responses={200: OpenApiResponse(description="Event rejected")}
    )
    @action(detail=True, methods=['post'], url_path='reject')
    @require_permission('update')
    def reject(self, request, pk=None):
        event = self.get_object()
        return self._set_event_status(
            request, pk, STATUS_REJECTED,
            f"رفض نشاط: {event.title}"
        )

    @extend_schema(
        description="List accepted events for a specific family within this faculty.",
        parameters=[
            OpenApiParameter(name='family_id', required=True, type=OpenApiTypes.INT),
        ],
        responses={
            200: EventSerializer(many=True),
            400: OpenApiResponse(description="Invalid Family ID"),
            404: OpenApiResponse(description="Family not found or invalid")
        }
    )
    @action(detail=False, methods=['get'], url_path='by-family')
    def list_accepted_events_by_family(self, request):
        family_id = request.query_params.get('family_id')
        admin = get_current_admin(request)

        try:
            family_id = int(family_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "family_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        family_is_valid = Families.objects.filter(
            family_id=family_id,
            faculty_id=admin.faculty_id,
        ).exists()

        if not family_is_valid:
            return Response(
                {"error": "Family not found, is not 'نوعية', or does not belong to your faculty."},
                status=status.HTTP_404_NOT_FOUND
            )

        events = self.get_queryset().filter(family_id=family_id, status=STATUS_APPROVED)
        return Response(self.get_serializer(events, many=True).data)