from django.db.models import Count, F, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.mixins import AdminActionMixin
from apps.accounts.permissions import IsRole
from apps.accounts.utils import get_current_admin, get_current_student
from apps.event.teams.models import EventTeamMembers, EventTeams, EventTeamSettings
from apps.event.teams.serializers import (
    AdminCreateTeamSerializer,
    AssignTeamResultSerializer,
    CreateTeamSerializer,
    EventTeamDetailSerializer,
    EventTeamSettingsCreateUpdateSerializer,
    EventTeamSettingsSerializer,
    JoinTeamByCodeSerializer,
    RejectTeamSerializer,
)
from apps.event.teams.services import TeamService


@extend_schema_view(
    create_team=extend_schema(
        tags=['Teams - Student'],
        request=CreateTeamSerializer,
        responses={201: EventTeamDetailSerializer},
        description='Create a team for an event. Current student becomes the captain.',
    ),
    join_by_code=extend_schema(
        tags=['Teams - Student'],
        request=JoinTeamByCodeSerializer,
        responses={201: EventTeamDetailSerializer},
        description='Join an existing team using its join code.',
    ),
    my_teams=extend_schema(
        tags=['Teams - Student'],
        responses={200: EventTeamDetailSerializer(many=True)},
        description='List teams where the current student is an active member.',
    ),
    team_details=extend_schema(
        tags=['Teams - Student'],
        responses={
            200: EventTeamDetailSerializer,
            403: OpenApiResponse(description='Student is not a member of this team.'),
        },
        description='Get details for a team where the current student is an active member.',
    ),
    leave_team=extend_schema(
        tags=['Teams - Student'],
        responses={200: dict},
        description='Leave a team. Captain can only leave if they are the only active member.',
    ),
    remove_member=extend_schema(
        tags=['Teams - Student'],
        responses={200: dict},
        description='Captain removes an active member from their pending team.',
    ),
)
class StudentTeamViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = ['student']

    @action(
        detail=False,
        methods=['post'],
        url_path=r'events/(?P<event_id>\d+)/create-team',
    )
    def create_team(self, request, event_id=None):
        student = get_current_student(request)

        serializer = CreateTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team = TeamService.create_team(
            student=student,
            event_id=event_id,
            name=serializer.validated_data['name'],
        )

        team = TeamService.get_team_or_404(team.team_id)

        return Response(
            {
                'message': 'تم إنشاء الفريق بنجاح.',
                'team': EventTeamDetailSerializer(team).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='join-by-code',
    )
    def join_by_code(self, request):
        student = get_current_student(request)

        serializer = JoinTeamByCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member = TeamService.join_team_by_code(
            student=student,
            join_code=serializer.validated_data['join_code'],
        )

        team = TeamService.get_team_or_404(member.team_id)

        return Response(
            {
                'message': 'تم الانضمام إلى الفريق بنجاح.',
                'team': EventTeamDetailSerializer(team).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='my-teams',
    )
    def my_teams(self, request):
        student = get_current_student(request)

        teams = (
            EventTeams.objects
            .filter(
                members__student=student,
                members__status=EventTeamMembers.MemberStatus.ACTIVE,
            )
            .select_related(
                'event',
                'captain',
                'approved_by',
                'rejected_by',
                'created_by_admin',
                'result_assigned_by',
            )
            .prefetch_related(
                'members',
                'members__student',
                'members__participation',
            )
            .annotate(
                active_members_count=Count(
                    'members',
                    filter=Q(
                        members__status=EventTeamMembers.MemberStatus.ACTIVE
                    ),
                )
            )
            .distinct()
            .order_by('-created_at')
        )

        return Response(
            {
                'count': teams.count(),
                'data': EventTeamDetailSerializer(teams, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='details',
    )
    def team_details(self, request, pk=None):
        student = get_current_student(request)

        team = TeamService.get_team_or_404(pk)

        is_member = EventTeamMembers.objects.filter(
            team=team,
            student=student,
            status=EventTeamMembers.MemberStatus.ACTIVE,
        ).exists()

        if not is_member:
            raise PermissionDenied('أنت لست عضوًا في هذا الفريق.')

        return Response(
            EventTeamDetailSerializer(team).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='leave',
    )
    def leave_team(self, request, pk=None):
        student = get_current_student(request)

        result = TeamService.leave_team(
            student=student,
            team_id=pk,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['delete'],
        url_path=r'members/(?P<student_id>\d+)',
    )
    def remove_member(self, request, pk=None, student_id=None):
        captain = get_current_student(request)

        result = TeamService.remove_member(
            actor=captain,
            team_id=pk,
            student_id=student_id,
            is_admin=False,
        )

        return Response(result, status=status.HTTP_200_OK)


@extend_schema_view(
    team_settings=extend_schema(
        tags=['Teams - Admin'],
        request=EventTeamSettingsCreateUpdateSerializer,
        responses={200: EventTeamSettingsSerializer},
        description='Get, create, or update team settings for an event.',
    ),
    get_event_teams=extend_schema(
        tags=['Teams - Admin'],
        responses={200: EventTeamDetailSerializer(many=True)},
        description='List all teams for a specific event.',
    ),
    get_team_details=extend_schema(
        tags=['Teams - Admin'],
        responses={200: EventTeamDetailSerializer},
        description='Get details of a specific team.',
    ),
    admin_create_team=extend_schema(
        tags=['Teams - Admin'],
        request=AdminCreateTeamSerializer,
        responses={201: EventTeamDetailSerializer},
        description='Admin manually creates a team from selected participants/students.',
    ),
    approve_team=extend_schema(
        tags=['Teams - Admin'],
        responses={200: dict},
        description='Approve a team and bulk approve all active team members in Prtcps.',
    ),
    reject_team=extend_schema(
        tags=['Teams - Admin'],
        request=RejectTeamSerializer,
        responses={200: dict},
        description='Reject a team and bulk reject all active team members in Prtcps.',
    ),
    admin_remove_member=extend_schema(
        tags=['Teams - Admin'],
        responses={200: dict},
        description='Admin removes an active member from a pending team.',
    ),
    assign_team_result=extend_schema(
        tags=['Teams - Admin'],
        request=AssignTeamResultSerializer,
        responses={200: dict},
        description='Assign simple team result/winner for an event.',
    ),
    get_event_team_ranking=extend_schema(
        tags=['Teams - Admin'],
        responses={200: EventTeamDetailSerializer(many=True)},
        description='Get simple team ranking for an event.',
    ),
)
class AdminTeamViewSet(AdminActionMixin, viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = [
        'مسؤول كلية',
        'مدير ادارة',
        'مدير كلية',
        'مدير عام',
        'مشرف النظام',
    ]

    @staticmethod
    def _validate_team_belongs_to_event(team, event):
        if int(team.event_id) != int(event.event_id):
            raise ValidationError('الفريق لا ينتمي إلى هذا النشاط.')

    @action(
        detail=False,
        methods=['get', 'post', 'patch'],
        url_path=r'events/(?P<event_id>\d+)/settings',
    )
    def team_settings(self, request, event_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        if request.method == 'GET':
            settings_obj = TeamService.get_team_settings(event)

            return Response(
                EventTeamSettingsSerializer(settings_obj).data,
                status=status.HTTP_200_OK,
            )

        existing_settings = EventTeamSettings.objects.filter(event=event).first()

        serializer = EventTeamSettingsCreateUpdateSerializer(
            existing_settings,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        def business_operation(admin, ip_address):
            settings_obj, created = EventTeamSettings.objects.get_or_create(
                event=event,
                defaults={
                    'created_by': admin,
                    'enabled': True,
                },
            )

            for field, value in serializer.validated_data.items():
                setattr(settings_obj, field, value)

            if not settings_obj.created_by_id:
                settings_obj.created_by = admin

            settings_obj.save()

            return {
                'message': 'تم حفظ إعدادات الفرق بنجاح.',
                'created': created,
                'settings': EventTeamSettingsSerializer(settings_obj).data,
            }

        result = self.execute_admin_action(
            request=request,
            action_name=f"حفظ إعدادات الفرق للنشاط: {event.title}",
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path=r'events/(?P<event_id>\d+)/teams',
    )
    def get_event_teams(self, request, event_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        teams = (
            EventTeams.objects
            .filter(event=event)
            .select_related(
                'event',
                'captain',
                'approved_by',
                'rejected_by',
                'created_by_admin',
                'result_assigned_by',
            )
            .prefetch_related(
                'members',
                'members__student',
                'members__participation',
            )
            .annotate(
                active_members_count=Count(
                    'members',
                    filter=Q(
                        members__status=EventTeamMembers.MemberStatus.ACTIVE
                    ),
                )
            )
            .order_by('-created_at')
        )

        return Response(
            {
                'count': teams.count(),
                'data': EventTeamDetailSerializer(teams, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path=r'teams/(?P<team_id>\d+)',
    )
    def get_team_details(self, request, team_id=None):
        admin = get_current_admin(request)

        team = TeamService.get_team_or_404(team_id)
        TeamService.validate_admin_can_manage_event(admin, team.event)

        return Response(
            EventTeamDetailSerializer(team).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['post'],
        url_path=r'events/(?P<event_id>\d+)/create-team',
    )
    def admin_create_team(self, request, event_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        serializer = AdminCreateTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def business_operation(admin, ip_address):
            team = TeamService.create_team_from_participants(
                admin=admin,
                event_id=event_id,
                name=serializer.validated_data['name'],
                captain_id=serializer.validated_data['captain_id'],
                student_ids=serializer.validated_data['student_ids'],
            )

            team = TeamService.get_team_or_404(team.team_id)

            return {
                'message': 'تم إنشاء الفريق بواسطة المسؤول بنجاح.',
                'team': EventTeamDetailSerializer(team).data,
            }

        result = self.execute_admin_action(
            request=request,
            action_name=(
                f"إنشاء فريق يدويًا للنشاط: {event.title} "
                f"- اسم الفريق: {serializer.validated_data['name']}"
            ),
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id,
        )

        return Response(result, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['patch'],
        url_path=r'events/(?P<event_id>\d+)/teams/(?P<team_id>\d+)/approve',
    )
    def approve_team(self, request, event_id=None, team_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        team = TeamService.get_team_or_404(team_id)
        self._validate_team_belongs_to_event(team, event)

        def business_operation(admin, ip_address):
            return TeamService.approve_team(
                admin=admin,
                event_id=event_id,
                team_id=team_id,
            )

        result = self.execute_admin_action(
            request=request,
            action_name=(
                f"اعتماد فريق: {team.name} "
                f"في النشاط: {event.title}"
            ),
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['patch'],
        url_path=r'events/(?P<event_id>\d+)/teams/(?P<team_id>\d+)/reject',
    )
    def reject_team(self, request, event_id=None, team_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        team = TeamService.get_team_or_404(team_id)
        self._validate_team_belongs_to_event(team, event)

        serializer = RejectTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def business_operation(admin, ip_address):
            return TeamService.reject_team(
                admin=admin,
                event_id=event_id,
                team_id=team_id,
                reason=serializer.validated_data.get('reason'),
            )

        result = self.execute_admin_action(
            request=request,
            action_name=(
                f"رفض فريق: {team.name} "
                f"في النشاط: {event.title}"
            ),
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['delete'],
        url_path=r'teams/(?P<team_id>\d+)/members/(?P<student_id>\d+)',
    )
    def admin_remove_member(self, request, team_id=None, student_id=None):
        admin = get_current_admin(request)

        team = TeamService.get_team_or_404(team_id)
        TeamService.validate_admin_can_manage_event(admin, team.event)

        def business_operation(admin, ip_address):
            return TeamService.remove_member(
                actor=admin,
                team_id=team_id,
                student_id=student_id,
                is_admin=True,
            )

        result = self.execute_admin_action(
            request=request,
            action_name=(
                f"حذف الطالب رقم {student_id} من فريق: {team.name} "
                f"في النشاط: {team.event.title}"
            ),
            target_type='نشاط',
            business_operation=business_operation,
            event_id=team.event.event_id,
            student_id=student_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['patch'],
        url_path=r'events/(?P<event_id>\d+)/teams/(?P<team_id>\d+)/result',
    )
    def assign_team_result(self, request, event_id=None, team_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        team = TeamService.get_team_or_404(team_id)
        self._validate_team_belongs_to_event(team, event)

        serializer = AssignTeamResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        def business_operation(admin, ip_address):
            return TeamService.assign_team_result(
                admin=admin,
                event_id=event_id,
                team_id=team_id,
                rank=serializer.validated_data.get('rank'),
                is_winner=serializer.validated_data.get('is_winner'),
            )

        result = self.execute_admin_action(
            request=request,
            action_name=(
                f"تسجيل نتيجة فريق: {team.name} "
                f"في النشاط: {event.title} "
                f"- الترتيب: {serializer.validated_data.get('rank')} "
                f"- فائز: {serializer.validated_data.get('is_winner')}"
            ),
            target_type='نشاط',
            business_operation=business_operation,
            event_id=event.event_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path=r'events/(?P<event_id>\d+)/ranking',
    )
    def get_event_team_ranking(self, request, event_id=None):
        admin = get_current_admin(request)

        event = TeamService.get_event_or_404(event_id)
        TeamService.validate_admin_can_manage_event(admin, event)

        teams = (
            EventTeams.objects
            .filter(
                event=event,
                status=EventTeams.TeamStatus.APPROVED,
            )
            .select_related(
                'event',
                'captain',
                'approved_by',
                'rejected_by',
                'created_by_admin',
                'result_assigned_by',
            )
            .prefetch_related(
                'members',
                'members__student',
                'members__participation',
            )
            .annotate(
                active_members_count=Count(
                    'members',
                    filter=Q(
                        members__status=EventTeamMembers.MemberStatus.ACTIVE
                    ),
                )
            )
            .order_by(
                '-is_winner',
                F('rank').asc(nulls_last=True),
                'created_at',
            )
        )

        return Response(
            {
                'event_id': event.event_id,
                'event_title': event.title,
                'count': teams.count(),
                'ranking': EventTeamDetailSerializer(teams, many=True).data,
            },
            status=status.HTTP_200_OK,
        )