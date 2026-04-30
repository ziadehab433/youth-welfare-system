from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import Students
from apps.event.models import Events, Prtcps
from apps.event.teams.models import EventTeamMembers, EventTeams, EventTeamSettings


class TeamService:
    PARTICIPANT_PENDING = 'منتظر'
    PARTICIPANT_APPROVED = 'مقبول'
    PARTICIPANT_REJECTED = 'مرفوض'

    ACTIVE_TEAM_STATUSES = [
        EventTeams.TeamStatus.PENDING,
        EventTeams.TeamStatus.APPROVED,
    ]

    @staticmethod
    def get_event_or_404(event_id):
        try:
            return Events.objects.select_related(
                'faculty',
                'dept',
            ).get(pk=event_id)
        except Events.DoesNotExist:
            raise NotFound('Event not found.')

    @staticmethod
    def get_event_for_update_or_404(event_id):
        try:
            return Events.objects.select_for_update().get(pk=event_id)
        except Events.DoesNotExist:
            raise NotFound('Event not found.')

    @staticmethod
    def get_team_or_404(team_id):
        try:
            return (
                EventTeams.objects
                .select_related(
                    'event',
                    'event__faculty',
                    'event__dept',
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
                .get(pk=team_id)
            )
        except EventTeams.DoesNotExist:
            raise NotFound('Team not found.')

    @staticmethod
    def get_team_for_update_or_404(team_id):
        try:
            return (
                EventTeams.objects
                .select_for_update()
                .get(pk=team_id)
            )
        except EventTeams.DoesNotExist:
            raise NotFound('Team not found.')

    @staticmethod
    def get_team_settings(event):
        try:
            settings = event.team_settings
        except EventTeamSettings.DoesNotExist:
            raise ValidationError('Team system is not enabled for this event.')

        if not settings.enabled:
            raise ValidationError('Team system is disabled for this event.')

        return settings

    @staticmethod
    def validate_event_joinable(event):
        today = timezone.now().date()

        if not getattr(event, 'active', False):
            raise ValidationError('Event is not active.')

        if event.status != 'مقبول':
            raise ValidationError('Event is not approved.')

        if event.st_date <= today:
            raise ValidationError('Cannot join an event that has already started.')

        if event.end_date < today:
            raise ValidationError('Cannot join an event that has already ended.')

    @staticmethod
    def validate_student_eligible_for_event(student, event):
        student_faculty_id = student.faculty_id
        selected_facs = getattr(event, 'selected_facs', None)

        is_same_faculty = event.faculty_id == student_faculty_id

        is_selected_faculty = (
            bool(selected_facs)
            and student_faculty_id in selected_facs
        )

        is_global_event = (
            event.faculty_id is None
            and not selected_facs
        )

        if not (is_same_faculty or is_selected_faculty or is_global_event):
            raise PermissionDenied('Student is not eligible for this event.')

    @staticmethod
    def validate_admin_can_manage_event(admin, event):
        if admin.role == 'مشرف النظام':
            return

        if admin.role == 'مدير ادارة' and event.dept_id == admin.dept_id:
            return

        if admin.role == 'مسؤول كلية' and event.faculty_id == admin.faculty_id:
            return

        if admin.role == 'مدير كلية' and event.faculty_id == admin.faculty_id:
            return

        if admin.role == 'مدير عام' and event.faculty_id is None:
            return

        raise PermissionDenied('You do not have permission to manage this event.')

    @staticmethod
    def active_team_membership_exists(event, student):
        return EventTeamMembers.objects.filter(
            student=student,
            team__event=event,
            status=EventTeamMembers.MemberStatus.ACTIVE,
            team__status__in=TeamService.ACTIVE_TEAM_STATUSES,
        ).exists()

    @staticmethod
    def get_active_member_count(team):
        return EventTeamMembers.objects.filter(
            team=team,
            status=EventTeamMembers.MemberStatus.ACTIVE,
        ).count()

    @staticmethod
    def validate_team_pending(team):
        if team.status != EventTeams.TeamStatus.PENDING:
            raise ValidationError('Only pending teams can be modified.')

    @staticmethod
    def validate_team_size(team, settings):
        active_count = TeamService.get_active_member_count(team)

        if active_count < settings.min_members:
            raise ValidationError(
                f'Team has {active_count} active member(s). '
                f'Minimum required is {settings.min_members}.'
            )

        if active_count > settings.max_members:
            raise ValidationError(
                f'Team has {active_count} active member(s). '
                f'Maximum allowed is {settings.max_members}.'
            )

        return active_count

    @staticmethod
    def validate_max_approved_teams(event, settings):
        if not settings.max_teams:
            return

        approved_teams_count = EventTeams.objects.filter(
            event=event,
            status=EventTeams.TeamStatus.APPROVED,
        ).count()

        if approved_teams_count >= settings.max_teams:
            raise ValidationError('Maximum approved teams limit has been reached.')

    @staticmethod
    def validate_event_capacity_for_team_approval(event, team):
        if not event.s_limit:
            return

        active_members = EventTeamMembers.objects.filter(
            team=team,
            status=EventTeamMembers.MemberStatus.ACTIVE,
            participation__isnull=False,
        )

        participation_ids = list(
            active_members.values_list('participation_id', flat=True)
        )

        approved_count = Prtcps.objects.filter(
            event=event,
            status=TeamService.PARTICIPANT_APPROVED,
        ).count()

        already_approved_in_team = Prtcps.objects.filter(
            id__in=participation_ids,
            status=TeamService.PARTICIPANT_APPROVED,
        ).count()

        needed_slots = len(participation_ids) - already_approved_in_team

        if approved_count + needed_slots > event.s_limit:
            remaining = max(event.s_limit - approved_count, 0)
            raise ValidationError(
                f'Event does not have enough remaining capacity. '
                f'Remaining slots: {remaining}, team needs: {needed_slots}.'
            )

    @staticmethod
    def get_or_create_participation(event, student):
        try:
            participation, _ = Prtcps.objects.get_or_create(
                event=event,
                student=student,
                defaults={
                    'status': TeamService.PARTICIPANT_PENDING,
                },
            )
        except IntegrityError:
            participation = Prtcps.objects.get(
                event=event,
                student=student,
            )

        if participation.status == TeamService.PARTICIPANT_REJECTED:
            raise ValidationError('Student was previously rejected from this event.')

        return participation

    @staticmethod
    @transaction.atomic
    def create_team(student, event_id, name):
        event = TeamService.get_event_for_update_or_404(event_id)

        TeamService.validate_event_joinable(event)
        TeamService.get_team_settings(event)
        TeamService.validate_student_eligible_for_event(student, event)

        if TeamService.active_team_membership_exists(event, student):
            raise ValidationError('Student is already in a team for this event.')

        if EventTeams.objects.filter(event=event, name=name).exists():
            raise ValidationError('A team with this name already exists for this event.')

        participation = TeamService.get_or_create_participation(event, student)

        team = EventTeams.objects.create(
            event=event,
            name=name,
            captain=student,
            join_code=EventTeams.generate_join_code(),
            status=EventTeams.TeamStatus.PENDING,
        )

        EventTeamMembers.objects.create(
            team=team,
            student=student,
            participation=participation,
            role=EventTeamMembers.MemberRole.CAPTAIN,
            status=EventTeamMembers.MemberStatus.ACTIVE,
        )

        return team

    @staticmethod
    @transaction.atomic
    def join_team_by_code(student, join_code):
        try:
            team = (
                EventTeams.objects
                .select_for_update()
                .get(join_code=join_code)
            )
        except EventTeams.DoesNotExist:
            raise NotFound('Invalid team code.')

        event = team.event

        TeamService.validate_event_joinable(event)
        settings = TeamService.get_team_settings(event)
        TeamService.validate_student_eligible_for_event(student, event)
        TeamService.validate_team_pending(team)

        if TeamService.active_team_membership_exists(event, student):
            raise ValidationError('Student is already in a team for this event.')

        current_count = TeamService.get_active_member_count(team)

        if current_count >= settings.max_members:
            raise ValidationError('Team is already full.')

        participation = TeamService.get_or_create_participation(event, student)

        try:
            member = EventTeamMembers.objects.create(
                team=team,
                student=student,
                participation=participation,
                role=EventTeamMembers.MemberRole.MEMBER,
                status=EventTeamMembers.MemberStatus.ACTIVE,
            )
        except IntegrityError:
            raise ValidationError('Student is already a member of this team.')

        return member

    @staticmethod
    @transaction.atomic
    def leave_team(student, team_id):
        team = TeamService.get_team_for_update_or_404(team_id)

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('Cannot leave an approved team.')

        if team.status in [
            EventTeams.TeamStatus.REJECTED,
            EventTeams.TeamStatus.CANCELLED,
        ]:
            raise ValidationError('Cannot leave a closed team.')

        try:
            membership = EventTeamMembers.objects.select_for_update().get(
                team=team,
                student=student,
                status=EventTeamMembers.MemberStatus.ACTIVE,
            )
        except EventTeamMembers.DoesNotExist:
            raise NotFound('You are not an active member of this team.')

        if membership.role == EventTeamMembers.MemberRole.CAPTAIN:
            active_count = TeamService.get_active_member_count(team)

            if active_count > 1:
                raise ValidationError(
                    'Captain cannot leave while other active members exist.'
                )

            membership.status = EventTeamMembers.MemberStatus.LEFT
            membership.save(update_fields=['status'])

            team.status = EventTeams.TeamStatus.CANCELLED
            team.save(update_fields=['status', 'updated_at'])

            return {
                'message': 'Team cancelled because captain left.',
                'team_id': team.team_id,
            }

        membership.status = EventTeamMembers.MemberStatus.LEFT
        membership.save(update_fields=['status'])

        return {
            'message': 'Left team successfully.',
            'team_id': team.team_id,
        }

    @staticmethod
    @transaction.atomic
    def remove_member(actor, team_id, student_id, is_admin=False):
        team = TeamService.get_team_for_update_or_404(team_id)

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('Cannot remove members from an approved team.')

        if team.status in [
            EventTeams.TeamStatus.REJECTED,
            EventTeams.TeamStatus.CANCELLED,
        ]:
            raise ValidationError('Cannot remove members from a closed team.')

        if not is_admin:
            if team.captain_id != actor.student_id:
                raise PermissionDenied('Only the team captain can remove members.')

            if int(student_id) == actor.student_id:
                raise ValidationError('Captain cannot remove themselves.')

        try:
            membership = EventTeamMembers.objects.select_for_update().get(
                team=team,
                student_id=student_id,
                status=EventTeamMembers.MemberStatus.ACTIVE,
            )
        except EventTeamMembers.DoesNotExist:
            raise NotFound('Active member not found in this team.')

        if membership.role == EventTeamMembers.MemberRole.CAPTAIN:
            raise ValidationError('Cannot remove the team captain.')

        membership.status = EventTeamMembers.MemberStatus.REMOVED
        membership.save(update_fields=['status'])

        return {
            'message': 'Member removed successfully.',
            'team_id': team.team_id,
            'student_id': int(student_id),
        }

    @staticmethod
    @transaction.atomic
    def create_team_from_participants(admin, event_id, name, captain_id, student_ids):
        event = TeamService.get_event_for_update_or_404(event_id)

        TeamService.validate_admin_can_manage_event(admin, event)
        settings = TeamService.get_team_settings(event)

        if event.status != 'مقبول':
            raise ValidationError('Team can only be created for an approved event.')

        if event.end_date < timezone.now().date():
            raise ValidationError('Cannot create a team for an ended event.')

        if not student_ids:
            raise ValidationError('student_ids cannot be empty.')

        student_ids = list(dict.fromkeys([int(student_id) for student_id in student_ids]))
        captain_id = int(captain_id)

        if captain_id not in student_ids:
            raise ValidationError('Captain must be included in student_ids.')

        if len(student_ids) < settings.min_members:
            raise ValidationError(f'Minimum team size is {settings.min_members}.')

        if len(student_ids) > settings.max_members:
            raise ValidationError(f'Maximum team size is {settings.max_members}.')

        if EventTeams.objects.filter(event=event, name=name).exists():
            raise ValidationError('A team with this name already exists for this event.')

        students = list(
            Students.objects
            .select_related('faculty')
            .filter(student_id__in=student_ids)
        )

        found_ids = {student.student_id for student in students}
        missing_ids = set(student_ids) - found_ids

        if missing_ids:
            raise ValidationError(f'Some students do not exist: {sorted(missing_ids)}.')

        for student in students:
            TeamService.validate_student_eligible_for_event(student, event)

            if TeamService.active_team_membership_exists(event, student):
                raise ValidationError(
                    f'Student {student.student_id} is already in another team for this event.'
                )

        captain = next(
            student for student in students
            if student.student_id == captain_id
        )

        team = EventTeams.objects.create(
            event=event,
            name=name,
            captain=captain,
            join_code=EventTeams.generate_join_code(),
            status=EventTeams.TeamStatus.PENDING,
            created_by_admin=admin,
        )

        for student in students:
            participation = TeamService.get_or_create_participation(event, student)

            EventTeamMembers.objects.create(
                team=team,
                student=student,
                participation=participation,
                role=(
                    EventTeamMembers.MemberRole.CAPTAIN
                    if student.student_id == captain_id
                    else EventTeamMembers.MemberRole.MEMBER
                ),
                status=EventTeamMembers.MemberStatus.ACTIVE,
            )

        return team

    @staticmethod
    @transaction.atomic
    def approve_team(admin, event_id, team_id):
        event = TeamService.get_event_for_update_or_404(event_id)

        try:
            team = EventTeams.objects.select_for_update().get(
                pk=team_id,
                event=event,
            )
        except EventTeams.DoesNotExist:
            raise NotFound('Team not found.')

        TeamService.validate_admin_can_manage_event(admin, event)

        if event.status != 'مقبول':
            raise ValidationError('Event must be approved before approving teams.')

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('Team is already approved.')

        if team.status in [
            EventTeams.TeamStatus.REJECTED,
            EventTeams.TeamStatus.CANCELLED,
        ]:
            raise ValidationError('Cannot approve a rejected or cancelled team.')

        settings = TeamService.get_team_settings(event)

        active_count = TeamService.validate_team_size(team, settings)
        TeamService.validate_max_approved_teams(event, settings)
        TeamService.validate_event_capacity_for_team_approval(event, team)

        active_members = EventTeamMembers.objects.filter(
            team=team,
            status=EventTeamMembers.MemberStatus.ACTIVE,
        )

        linked_participation_count = active_members.filter(
            participation__isnull=False
        ).count()

        if linked_participation_count != active_count:
            raise ValidationError('Some team members do not have linked participant records.')

        participation_ids = list(
            active_members.values_list('participation_id', flat=True)
        )

        if not participation_ids:
            raise ValidationError('Team has no linked participant records.')

        Prtcps.objects.filter(
            id__in=participation_ids,
        ).update(status=TeamService.PARTICIPANT_APPROVED)

        team.status = EventTeams.TeamStatus.APPROVED
        team.approved_by = admin
        team.approved_at = timezone.now()
        team.rejected_by = None
        team.rejected_at = None
        team.rejection_reason = None
        team.save(update_fields=[
            'status',
            'approved_by',
            'approved_at',
            'rejected_by',
            'rejected_at',
            'rejection_reason',
            'updated_at',
        ])

        return {
            'message': 'Team approved successfully.',
            'team_id': team.team_id,
            'team_name': team.name,
            'approved_members': active_count,
        }

    @staticmethod
    @transaction.atomic
    def reject_team(admin, event_id, team_id, reason=None):
        event = TeamService.get_event_for_update_or_404(event_id)

        try:
            team = EventTeams.objects.select_for_update().get(
                pk=team_id,
                event=event,
            )
        except EventTeams.DoesNotExist:
            raise NotFound('Team not found.')

        TeamService.validate_admin_can_manage_event(admin, event)

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('Cannot reject an already approved team.')

        if team.status == EventTeams.TeamStatus.REJECTED:
            raise ValidationError('Team is already rejected.')

        if team.status == EventTeams.TeamStatus.CANCELLED:
            raise ValidationError('Cannot reject a cancelled team.')

        participation_ids = list(
            EventTeamMembers.objects.filter(
                team=team,
                status=EventTeamMembers.MemberStatus.ACTIVE,
                participation__isnull=False,
            ).values_list('participation_id', flat=True)
        )

        if participation_ids:
            Prtcps.objects.filter(
                id__in=participation_ids,
            ).update(status=TeamService.PARTICIPANT_REJECTED)

        team.status = EventTeams.TeamStatus.REJECTED
        team.rejected_by = admin
        team.rejected_at = timezone.now()
        team.rejection_reason = reason
        team.save(update_fields=[
            'status',
            'rejected_by',
            'rejected_at',
            'rejection_reason',
            'updated_at',
        ])

        return {
            'message': 'Team rejected successfully.',
            'team_id': team.team_id,
            'team_name': team.name,
            'rejected_members': len(participation_ids),
            'reason': reason,
        }