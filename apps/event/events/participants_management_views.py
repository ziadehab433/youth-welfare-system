from django.utils import timezone
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.db import transaction
from apps.accounts.utils import get_current_admin, get_client_ip, log_data_access
from apps.accounts.permissions import require_permission
from apps.event.models import Events, Prtcps
from apps.family.models import Students
from .serializers import ParticipantResultSerializer

@extend_schema(tags=["Event Management APIs"])
class EventParticipantViewSet(viewsets.GenericViewSet):
    queryset = Events.objects.all()
    """
    Complete event management system for admins
    - Approve/reject participant requests
    - Bulk operations
    - Assign results and rewards
    """
    def _validate_event_editable(self, event):
        if event.status != 'مقبول':
            raise serializers.ValidationError(
                {"error": "Cannot manage participants. Event must be 'مقبول' first."}
            )
    def _validate_event_completed(self, event):
        today = timezone.now().date()
        if event.end_date > today:
            return Response({
                "error": "Cannot assign results before event ends",
                "event_end_date": event.end_date,
                "today": today,
                "days_remaining": (event.end_date - today).days
            }, status=status.HTTP_400_BAD_REQUEST)
        return None

    @extend_schema(
        description="Approve a specific student's request to join the event.",
        responses={
            200: OpenApiResponse(description="Participant approved successfully"),
            400: OpenApiResponse(description="Invalid request"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Participant not found")
        },
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)]
    )
    @action(detail=True, methods=['patch'], url_path=r'participants/(?P<student_id>\d+)/approve')
    @require_permission('update')
    def approve_participant(self, request, pk=None, student_id=None):
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        event = self.get_object()
        self._validate_event_editable(event)

        with transaction.atomic():
            participation = Prtcps.objects.select_for_update().filter(
                event=event, 
                student_id=student_id
            ).first()
            if not participation:
                return Response(
                    {"error": "No join request found for this student"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            if participation.status == 'مقبول':
                return Response(
                    {"message": "Student is already approved"}, 
                    status=status.HTTP_200_OK
                )
            if participation.status == 'مرفوض':
                return Response(
                    {"error": "Cannot approve a previously rejected student"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            student = Students.objects.filter(student_id=student_id).first()
            if not student:
                return Response(
                    {"error": "Student not found in system"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            if student.faculty_id != event.faculty_id:
                return Response(
                    {"error": "Student does not belong to event's faculty"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            participation.status = 'مقبول'
            participation.save()
            log_data_access(
            actor_id=admin.admin_id, 
            actor_type=admin.role,
            action=f"تم قبول الطالب {student.name} (رقم: {student_id}) في نشاط: {event.title}",
            target_type='نشاط', 
            event_id=event.event_id, 
            ip_address=ip
        )
            return Response({
                "message": "Student approved successfully",
                "data": {
                    "student_id": student_id,
                    "student_name": student.name,
                    "event_id": event.event_id,
                    "event_title": event.title,
                    "status": participation.status
                }
            })
    @extend_schema(
        description="Reject a specific student's request to join the event.",
        responses={
            200: OpenApiResponse(description="Participant rejected successfully"),
            400: OpenApiResponse(description="Invalid request"),
            404: OpenApiResponse(description="Participant not found")
        },
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)]
    )
    @action(detail=True, methods=['patch'], url_path=r'participants/(?P<student_id>\d+)/reject')
    @require_permission('update')
    def reject_participant(self, request, pk=None, student_id=None):
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        event = self.get_object()
        self._validate_event_editable(event)

        with transaction.atomic():
            participation = Prtcps.objects.select_for_update().filter(
                event=event, 
                student_id=student_id
            ).first()
            if not participation:
                return Response(
                    {"error": "No join request found for this student"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            if participation.status == 'مرفوض':
                return Response(
                    {"message": "Student is already rejected"}, 
                    status=status.HTTP_200_OK
                )
            if participation.status == 'مقبول':
                return Response(
                    {"error": "Cannot reject an already approved student"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            participation.status = 'مرفوض'
            participation.save()

            log_data_access(
                actor_id=admin.admin_id, 
                actor_type=admin.role,
                action=f"تم رفض طلب انضمام الطالب (رقم: {student_id}) للنشاط: {event.title}",
                target_type='نشاط', 
                event_id=event.event_id, 
                ip_address=ip
            )
            return Response({"message": "Student request rejected successfully"})
    @extend_schema(
        description="Approve all currently pending student requests for this event in bulk.",
        responses={200: OpenApiResponse(description="All pending participants approved")}
    )
    @action(detail=True, methods=['patch'], url_path='approve-all-participants')
    @require_permission('update')
    def approve_all_participants(self, request, pk=None):
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        event = self.get_object()
        self._validate_event_editable(event)
        with transaction.atomic():
            pending_count = Prtcps.objects.filter(
                event=event, 
                status='منتظر'
            ).count()
            participants_qs = Prtcps.objects.select_for_update().filter(
                event=event, 
                status='منتظر'
            )
            updated_count = participants_qs.update(status='مقبول')
            log_data_access(
                actor_id=admin.admin_id, 
                actor_type=admin.role,
                action=f"تم قبول جميع الطلاب (العدد: {updated_count}) في نشاط: {event.title}",
                target_type='نشاط', 
                event_id=event.event_id, 
                ip_address=ip
            )
        return Response({
            "message": f"Successfully approved {updated_count} out of {pending_count} pending participants",
            "data": {
                "event_id": event.event_id,
                "event_title": event.title,
                "approved_count": updated_count,
                "pending_count": pending_count - updated_count
            }
        })
    @extend_schema(
        request=ParticipantResultSerializer,
        responses={
            200: OpenApiResponse(description="Result assigned successfully"),
            400: OpenApiResponse(description="Event not completed or invalid data"),
            404: OpenApiResponse(description="Participant not found")
        },
        parameters=[OpenApiParameter(name='student_id', type=int, location=OpenApiParameter.PATH)]
    )
    @action(detail=True, methods=['patch'], url_path=r'participants/(?P<student_id>\d+)/assign-result')
    @require_permission('update')
    def assign_participant_result(self, request, pk=None, student_id=None):
        """
        Assign rank and reward to a participant
        - Event must be completed (end_date passed)
        - Participant must be approved
        """
        admin = get_current_admin(request)
        ip = get_client_ip(request)
        event = self.get_object()
        self._validate_event_editable(event)
        today = timezone.now().date()
        if event.end_date > today:
            return Response({
                "error": "Cannot assign results before event ends",
                "event_end_date": event.end_date,
                "today": today,
                "days_remaining": (event.end_date - today).days
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = ParticipantResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            participant = Prtcps.objects.select_for_update().filter(
                event=event, 
                student_id=student_id, 
                status='مقبول'
            ).first()
            if not participant:
                return Response({
                    "error": "Student not found or not approved in this event"
                }, status=status.HTTP_404_NOT_FOUND)
            old_rank = participant.rank
            old_reward = participant.reward
            participant.rank = serializer.validated_data.get('rank', participant.rank)
            participant.reward = serializer.validated_data.get('reward', participant.reward)
            participant.save()
            log_data_access(
                actor_id=admin.admin_id, 
                actor_type=admin.role,
                action=f"تم تسجيل نتيجة الطالب (رقم: {student_id}) في نشاط: {event.title} - المركز: {participant.rank} - المكافأة: {participant.reward}",
                target_type='نشاط', 
                event_id=event.event_id, 
                ip_address=ip
            )
        return Response({
            "message": "Result assigned successfully",
            "data": {
                "student_id": student_id,
                "event_id": event.event_id,
                "event_title": event.title,
                "rank": participant.rank,
                "reward": participant.reward,
                "assigned_at": timezone.now().isoformat()  
            }
        })
