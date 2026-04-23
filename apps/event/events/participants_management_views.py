from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.db import transaction
from apps.accounts.utils import get_current_admin, log_data_access
from apps.accounts.mixins import AdminActionMixin
from apps.event.models import Events, Prtcps
from apps.family.models import Students
from .serializers import ParticipantResultSerializer
from apps.accounts.permissions import require_permission, IsRole
from apps.accounts.serializers import StudentDetailSerializer

@extend_schema(tags=["Event Management APIs"])
class EventParticipantViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['مسؤول كلية', 'مدير ادارة', 'مشرف النظام']

    def get_queryset(self):
        admin = get_current_admin(self.request)
        queryset = Events.objects.filter(family__isnull=True).select_related('faculty', 'dept')
        if admin.role == 'مشرف النظام':
            return queryset
        if admin.role == 'مدير ادارة':
            return queryset.filter(dept_id=admin.dept_id)
        return queryset.filter(faculty_id=admin.faculty_id)

    def _validate_event_editable(self, event):
        if event.status != 'مقبول':
            raise ValidationError({"error": "Cannot manage participants. Event must be 'مقبول' first."})

    def _validate_event_completed(self, event):
        today = timezone.now().date()
        if event.end_date > today:
            raise ValidationError({
                "error": "Cannot assign results before event ends",
                "event_end_date": str(event.end_date),
                "today": str(today),
                "days_remaining": (event.end_date - today).days,
            })

    def _validate_student_faculty(self, student, event):
        if event.faculty_id and student.faculty_id != event.faculty_id:
            raise PermissionDenied("Student does not belong to the organizing faculty.")
        if event.selected_facs and student.faculty_id not in event.selected_facs:
            raise PermissionDenied("Student's faculty is not selected for this event.")

    def _get_eligible_pending_qs(self, event):
        qs = Prtcps.objects.filter(event=event, status='منتظر')
        if event.faculty_id:
            return qs.filter(student__faculty_id=event.faculty_id)
        if event.selected_facs:
            return qs.filter(student__faculty_id__in=event.selected_facs)
        return qs

    def _get_participation(self, event, student_id):
        try:
            return (
                Prtcps.objects
                .select_for_update()
                .select_related('student')
                .get(event=event, student_id=student_id)
            )
        except Prtcps.DoesNotExist:
            raise NotFound("No join request found for this student.")
        except Prtcps.MultipleObjectsReturned:
            raise ValidationError({"error": "Data integrity error: duplicate participation records found."})

    def _process_participant(self, request, event, student_id, target_status):
        opposite    = 'مرفوض' if target_status == 'مقبول' else 'مقبول'
        already_msg = "Student is already approved." if target_status == 'مقبول' else "Student is already rejected."
        conflict_msg = (
            "Cannot approve a previously rejected student."
            if target_status == 'مقبول' else
            "Cannot reject an already approved student."
        )
        is_approve = target_status == 'مقبول'

        with transaction.atomic():
            participation = self._get_participation(event, student_id)

            if participation.status == target_status:
                return Response({"message": already_msg}, status=status.HTTP_200_OK)

            if participation.status == opposite:
                return Response({"error": conflict_msg}, status=status.HTTP_400_BAD_REQUEST)

            if is_approve:
                self._validate_student_faculty(participation.student, event)

            participation.status = target_status
            participation.save(update_fields=['status'])

        student = participation.student
        action_name = (
            f"تم قبول الطالب {student.name} (رقم: {student_id}) في نشاط: {event.title}"
            if is_approve else
            f"تم رفض طلب انضمام الطالب (رقم: {student_id}) للنشاط: {event.title}"
        )

        result = self.execute_admin_action(
            request=request,
            action_name=action_name,
            target_type='نشاط',
            business_operation=lambda admin, ip: {
                "message": "Student approved successfully." if is_approve else "Student request rejected successfully.",
                **({"data": {
                    "student_id": student_id,
                    "student_name": student.name,
                    "event_id": event.event_id,
                    "event_title": event.title,
                    "status": target_status,
                }} if is_approve else {}),
            },
            event_id=event.event_id,
        )
        return Response(result)

    @extend_schema(
        description="Approve a specific student's request to join the event.",
        responses={
            200: OpenApiResponse(description="Participant approved successfully"),
            400: OpenApiResponse(description="Invalid request"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Participant not found"),
        },
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)],
    )
    @action(detail=True, methods=['patch'], url_path=r'participants/(?P<student_id>\d+)/approve')
    @require_permission('update')
    def approve_participant(self, request, pk=None, student_id=None):
        event = self.get_object()
        self._validate_event_editable(event)
        return self._process_participant(request, event, student_id, target_status='مقبول')

    @extend_schema(
        description="Reject a specific student's request to join the event.",
        responses={
            200: OpenApiResponse(description="Participant rejected successfully"),
            400: OpenApiResponse(description="Invalid request"),
            404: OpenApiResponse(description="Participant not found"),
        },
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)],
    )
    @action(detail=True, methods=['patch'], url_path=r'participants/(?P<student_id>\d+)/reject')
    @require_permission('update')
    def reject_participant(self, request, pk=None, student_id=None):
        event = self.get_object()
        self._validate_event_editable(event)
        return self._process_participant(request, event, student_id, target_status='مرفوض')

    @extend_schema(
        description="Approve all eligible pending participants for the event using a single DB-level update.",
        responses={
            200: OpenApiResponse(description="All eligible participants approved"),
            400: OpenApiResponse(description="Event not editable"),
        },
    )
    @action(detail=True, methods=['patch'], url_path='approve-all-participants')
    @require_permission('update')
    def approve_all_participants(self, request, pk=None):
        event = self.get_object()
        self._validate_event_editable(event)

        with transaction.atomic():
            eligible_qs     = self._get_eligible_pending_qs(event).select_for_update()
            total_pending   = Prtcps.objects.filter(event=event, status='منتظر').count()
            approved_ids    = list(eligible_qs.values_list('student_id', flat=True))
            approved_count  = eligible_qs.update(status='مقبول')
            skipped_count   = total_pending - approved_count

        result = self.execute_admin_action(
            request=request,
            action_name=f"تم قبول جميع الطلاب المؤهلين في نشاط: {event.title}",
            target_type='نشاط',
            business_operation=lambda admin, ip: {
                "message": f"Approved {approved_count} participant(s). Skipped {skipped_count} due to faculty mismatch.",
                "data": {
                    "event_id": event.event_id,
                    "event_title": event.title,
                    "approved_count": approved_count,
                    "skipped_count": skipped_count,
                    "approved_student_ids": approved_ids,
                },
            },
            event_id=event.event_id,
        )
        return Response(result)

    @extend_schema(
        request=ParticipantResultSerializer,
        responses={
            200: OpenApiResponse(description="Result assigned successfully"),
            400: OpenApiResponse(description="Event not completed or invalid data"),
            404: OpenApiResponse(description="Participant not found"),
        },
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)],
    )
    @action(
        detail=True,
        methods=['patch'],
        url_path=r'participants/(?P<student_id>\d+)/assign-result',
    )
    @require_permission('update')
    def assign_participant_result(self, request, pk=None, student_id=None):
        event = self.get_object()
        self._validate_event_editable(event)
        self._validate_event_completed(event)

        serializer = ParticipantResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            try:
                participant = (
                    Prtcps.objects
                    .select_for_update()
                    .get(event=event, student_id=student_id, status='مقبول')
                )
            except Prtcps.DoesNotExist:
                raise NotFound("Student not found or not approved in this event.")

            participant.rank   = serializer.validated_data.get('rank', participant.rank)
            participant.reward = serializer.validated_data.get('reward', participant.reward)
            participant.save(update_fields=['rank', 'reward'])

        result = self.execute_admin_action(
            request=request,
            action_name=(
                f"تم تسجيل نتيجة الطالب (رقم: {student_id}) في نشاط: {event.title} "
                f"- المركز: {participant.rank} - المكافأة: {participant.reward}"
            ),
            target_type='نشاط',
            business_operation=lambda admin, ip: {
                "message": "Result assigned successfully.",
                "data": {
                    "student_id": student_id,
                    "event_id": event.event_id,
                    "event_title": event.title,
                    "rank": participant.rank,
                    "reward": participant.reward,
                    "assigned_at": timezone.now().isoformat(),
                },
            },
            event_id=event.event_id,
        )
        return Response(result)

    @extend_schema(
        tags=["Event Management APIs"],
        description="Retrieve detailed information of a specific student for admins.",
        responses={200: StudentDetailSerializer},
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)],
    )
    @action(detail=False, methods=['get'], url_path=r'student-details/(?P<student_id>\d+)')
    @require_permission('read')
    def get_student_info(self, request, student_id=None):
        student = get_object_or_404(Students, pk=student_id)
        serializer = StudentDetailSerializer(student, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)