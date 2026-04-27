from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_spectacular.utils import extend_schema
from ..models import Clans, ScoutMembers
from ..serializers import (
    ClanSerializer,
    ScoutJoinSerializer,
    ScoutStatusSerializer,
)
from ..utils import (
    success_response,
    error_response,
)

@extend_schema(tags=["Student Scouts"])

class StudentScoutViewSet(ViewSet):

    # GET /scouts/student/clan/
    @action(detail=False, methods=['get'])
    def clan(self, request):
        """View the clan associated with student's faculty"""
        try:
            student = request.user_data
            faculty_id = student.get('faculty_id')

            try:
                clan = Clans.objects.get(
                    faculty_id=faculty_id,
                    status='active'
                )
            except Clans.DoesNotExist:
                return Response(
                    success_response(
                        "لا توجد عشيرة متاحة لكليتك حالياً",
                        data=None
                    ),
                    status=status.HTTP_200_OK
                )

            serializer = ClanSerializer(clan)

            return Response(
                success_response(
                    "تم جلب بيانات العشيرة بنجاح",
                    data=serializer.data
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                error_response("حدث خطأ أثناء جلب بيانات العشيرة"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # POST /scouts/student/join/
    @action(detail=False, methods=['post'])
    def join(self, request):
        """Submit a request to join — allows re-application after rejection"""
        try:
            student = request.user_data

            existing = ScoutMembers.objects.filter(
                student_id=student['student_id']
            ).first()

            if existing:
                if existing.status == 'منتظر':
                    return Response(
                        error_response("لديك طلب انضمام قيد المراجعة بالفعل"),
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif existing.status == 'مقبول':
                    return Response(
                        error_response("أنت عضو بالفعل في العشيرة"),
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif existing.status == 'مرفوض':
                    # Allow re-application — reset the record
                    with transaction.atomic():
                        existing.status = 'منتظر'
                        existing.role = 'MEMBER'
                        existing.group = None
                        existing.rejection_reason = None
                        existing.reviewed_by = None
                        existing.reviewed_at = None
                        existing.joined_at = None
                        existing.updated_at = None
                        existing.save()

                    return Response(
                        success_response("تم إعادة تقديم طلب الانضمام بنجاح"),
                        status=status.HTTP_201_CREATED
                    )

            serializer = ScoutJoinSerializer(
                data=request.data,
                context={'request': request}
            )

            if not serializer.is_valid():
                return Response(
                    error_response(
                        "بيانات الطلب غير صحيحة",
                        errors=serializer.errors
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                ScoutMembers.objects.create(
                    student_id=student['student_id'],
                    clan=serializer.validated_data['clan'],
                    role='MEMBER',
                    status='منتظر',
                )

            return Response(
                success_response("تم تقديم طلب الانضمام بنجاح"),
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                error_response("حدث خطأ أثناء تقديم طلب الانضمام"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/student/my_status/
    @action(detail=False, methods=['get'])
    def my_status(self, request):
        """Check membership request status"""
        try:
            student = request.user_data

            try:
                membership = ScoutMembers.objects.select_related(
                    'clan', 'group'
                ).get(student_id=student['student_id'])
            except ScoutMembers.DoesNotExist:
                return Response(
                    success_response(
                        "لم تقم بتقديم طلب انضمام بعد",
                        data=None
                    ),
                    status=status.HTTP_200_OK
                )

            serializer = ScoutStatusSerializer(membership)

            return Response(
                success_response(
                    "تم جلب حالة العضوية بنجاح",
                    data=serializer.data
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                error_response("حدث خطأ أثناء جلب حالة العضوية"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # GET /scouts/student/dashboard/
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Full dashboard for accepted members"""
        try:
            student = request.user_data

            try:
                membership = ScoutMembers.objects.select_related(
                    'clan', 'group'
                ).get(
                    student_id=student['student_id'],
                    status='مقبول'
                )
            except ScoutMembers.DoesNotExist:
                return Response(
                    error_response("ليس لديك عضوية مقبولة في أي عشيرة"),
                    status=status.HTTP_403_FORBIDDEN
                )

            dashboard = {
                'membership': {
                    'role': membership.role,
                    'status': membership.status,
                    'joined_at': membership.joined_at,
                },
                'clan': {
                    'clan_id': membership.clan.clan_id,
                    'name': membership.clan.name,
                    'description': membership.clan.description,
                },
                'group': None,
                'group_leaders': None,
                'group_members': [],
            }

            if membership.group:
                dashboard['group'] = {
                    'group_id': membership.group.group_id,
                    'name': membership.group.name,
                }

                # Get all group leaders (male + female)
                group_leaders = ScoutMembers.objects.select_related(
                    'student'
                ).filter(
                    group=membership.group,
                    role__in=[
                        'GROUP_LEADER_MALE',
                        'GROUP_LEADER_FEMALE',
                        'GROUP_ASSISTANT_MALE',
                        'GROUP_ASSISTANT_FEMALE',
                    ],
                    status='مقبول'
                )

                dashboard['group_leaders'] = {
                    leader.role: {
                        'name': leader.student.name,
                        'email': leader.student.email,
                        'phone': leader.student.phone_number,
                    }
                    for leader in group_leaders
                }

                # Get group members
                group_members = ScoutMembers.objects.select_related(
                    'student'
                ).filter(
                    group=membership.group,
                    status='مقبول'
                ).exclude(
                    scout_member_id=membership.scout_member_id
                )

                dashboard['group_members'] = [
                    {
                        'name': m.student.name,
                        'role': m.role,
                        'gender': m.student.gender,
                    }
                    for m in group_members
                ]

            return Response(
                success_response(
                    "تم جلب بيانات لوحة التحكم بنجاح",
                    data=dashboard
                ),
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                error_response("حدث خطأ أثناء جلب بيانات لوحة التحكم"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )