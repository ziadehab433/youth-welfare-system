import logging
from rest_framework import viewsets, status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from apps.event.models import Events, Prtcps
from apps.family.models import Students
from apps.accounts.permissions import IsRole, require_permission
from apps.accounts.utils import get_current_admin
from apps.accounts.mixins import AdminActionMixin

logger = logging.getLogger(__name__)

STATUS_PENDING = 'منتظر'
STATUS_APPROVED = 'مقبول'
STATUS_REJECTED = 'مرفوض'

@extend_schema(tags=["Family Fac Admin APIs"])
class FacultyEventParticipantsViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية']
    queryset = Events.objects.all()
    lookup_field = 'pk'

    def get_queryset(self):
        admin = get_current_admin(self.request)
        return Events.objects.filter(
            faculty_id=admin.faculty_id
        ).exclude(
            family__type='مركزية'
        )

    def _validate_event_editable(self, event):
        if event.status != STATUS_APPROVED:
            raise serializers.ValidationError(
                {"error": "Cannot manage participants. The event must be 'مقبول' first."}
            )

    @extend_schema(
        description="Approve ALL pending participants.",
        request=None,
        responses={
            200: OpenApiResponse(description="Approved successfully"),
            400: OpenApiResponse(description="Event not in correct status")
        }
    )
    @action(detail=True, methods=['post'], url_path='approve-all-participants')
    @require_permission('update')
    def approve_all_participants(self, request, pk=None):
        with transaction.atomic():
            event = self.get_object()
            self._validate_event_editable(event)

            def business_operation(admin, ip):
                participants_qs = Prtcps.objects.select_for_update().filter(
                    event=event,
                    status=STATUS_PENDING
                )
                updated_count = participants_qs.update(status=STATUS_APPROVED)
                return {"message": f"Successfully approved {updated_count} participants."}

            result = self.execute_admin_action(
                request=request,
                action_name=f"قبول جماعي للمشاركين في النشاط: {event.title}",
                target_type='نشاط',
                business_operation=business_operation,
                event_id=event.event_id
            )

        return Response(result, status=status.HTTP_200_OK)

    def _set_participant_status(self, request, pk, student_id, new_status, action_name):
        event = self.get_object()
        self._validate_event_editable(event)

        student_id = int(student_id)

        try:
            student = Students.objects.only('faculty_id').get(student_id=student_id)
        except Students.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if student.faculty_id != event.faculty_id:
            return Response(
                {"error": "Student does not belong to the event's faculty"},
                status=status.HTTP_403_FORBIDDEN
            )

        def business_operation(admin, ip):
            updated = Prtcps.objects.select_for_update().filter(
                event=event,
                student_id=student_id
            ).update(status=new_status)

            if updated == 0:
                raise ValidationError("Student not found in this event")

            status_msg = "Participant approved successfully" if new_status == STATUS_APPROVED else "Participant rejected successfully"
            return {"message": status_msg}

        try:
            with transaction.atomic():
                result = self.execute_admin_action(
                    request=request,
                    action_name=action_name,
                    target_type='نشاط',
                    business_operation=business_operation,
                    event_id=event.event_id
                )
            return Response(result, status=status.HTTP_200_OK)
        except ValidationError as e:
            error_msg = e.detail if hasattr(e, "detail") else str(e)
            return Response(
                {"error": error_msg},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        description="Approve a specific participant.",
        request=None,
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(description="Participant approved"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Participant not found")
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'participants/(?P<student_id>\d+)/approve'
    )
    @require_permission('update')
    def approve_participant(self, request, pk=None, student_id=None):
        return self._set_participant_status(
            request, pk, student_id, STATUS_APPROVED,
            f"قبول الطالب رقم {student_id} في النشاط"
        )

    @extend_schema(
        description="Reject a specific participant.",
        request=None,
        parameters=[
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(description="Participant rejected"),
            404: OpenApiResponse(description="Participant not found")
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path=r'participants/(?P<student_id>\d+)/reject'
    )
    @require_permission('update')
    def reject_participant(self, request, pk=None, student_id=None):
        return self._set_participant_status(
            request, pk, student_id, STATUS_REJECTED,
            f"رفض الطالب رقم {student_id} من النشاط"
        )