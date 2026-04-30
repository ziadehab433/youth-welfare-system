from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsRole
from apps.accounts.utils import get_current_admin, get_current_student
from apps.event.teams.models import EventTeamMembers, EventTeams, EventTeamSettings
from apps.event.teams.serializers import (
    AdminCreateTeamSerializer,
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
                'message': 'Team created successfully.',
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
                'message': 'Joined team successfully.',
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
            )
            .prefetch_related(
                'members',
                'members__student',
                'members__participation',
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
            raise PermissionDenied('You are not a member of this team.')

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
)
class AdminTeamViewSet(viewsets.GenericViewSet):
    permission_classes = [IsRole]
    allowed_roles = [
        'مسؤول كلية',
        'مدير ادارة',
        'مدير كلية',
        'مدير عام',
        'مشرف النظام',
    ]

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

        settings_obj, created = EventTeamSettings.objects.get_or_create(
            event=event,
            defaults={
                'created_by': admin,
                'enabled': True,
            },
        )

        serializer = EventTeamSettingsCreateUpdateSerializer(
            settings_obj,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        serializer.save(
            created_by=settings_obj.created_by or admin,
        )

        settings_obj.refresh_from_db()

        return Response(
            {
                'message': 'Team settings saved successfully.',
                'created': created,
                'settings': EventTeamSettingsSerializer(settings_obj).data,
            },
            status=status.HTTP_200_OK,
        )

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
            )
            .prefetch_related(
                'members',
                'members__student',
                'members__participation',
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

        serializer = AdminCreateTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team = TeamService.create_team_from_participants(
            admin=admin,
            event_id=event_id,
            name=serializer.validated_data['name'],
            captain_id=serializer.validated_data['captain_id'],
            student_ids=serializer.validated_data['student_ids'],
        )

        team = TeamService.get_team_or_404(team.team_id)

        return Response(
            {
                'message': 'Team created successfully by admin.',
                'team': EventTeamDetailSerializer(team).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=['patch'],
        url_path=r'events/(?P<event_id>\d+)/teams/(?P<team_id>\d+)/approve',
    )
    def approve_team(self, request, event_id=None, team_id=None):
        admin = get_current_admin(request)

        result = TeamService.approve_team(
            admin=admin,
            event_id=event_id,
            team_id=team_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['patch'],
        url_path=r'events/(?P<event_id>\d+)/teams/(?P<team_id>\d+)/reject',
    )
    def reject_team(self, request, event_id=None, team_id=None):
        admin = get_current_admin(request)

        serializer = RejectTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = TeamService.reject_team(
            admin=admin,
            event_id=event_id,
            team_id=team_id,
            reason=serializer.validated_data.get('reason'),
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

        result = TeamService.remove_member(
            actor=admin,
            team_id=team_id,
            student_id=student_id,
            is_admin=True,
        )

        return Response(result, status=status.HTTP_200_OK)