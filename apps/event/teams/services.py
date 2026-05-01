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
            raise NotFound('لم يتم العثور على النشاط.')

    @staticmethod
    def get_event_for_update_or_404(event_id):
        try:
            return Events.objects.select_for_update().only(
                'event_id', 'faculty_id', 'dept_id'
            ).get(pk=event_id)
        except Events.DoesNotExist:
            raise NotFound('لم يتم العثور على النشاط.')

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
                    'result_assigned_by',
                )
                .prefetch_related(
                    'members',
                    'members__student',
                    'members__participation',
                )
                .get(pk=team_id)
            )
        except EventTeams.DoesNotExist:
            raise NotFound('لم يتم العثور على الفريق.')

    @staticmethod
    def get_team_for_update_or_404(team_id):
        try:
            return EventTeams.objects.select_for_update().get(pk=team_id)
        except EventTeams.DoesNotExist:
            raise NotFound('لم يتم العثور على الفريق.')

    @staticmethod
    def get_team_settings(event):
        try:
            settings = event.team_settings
        except EventTeamSettings.DoesNotExist:
            raise ValidationError('نظام الفرق غير مفعّل لهذا النشاط.')

        if not settings.enabled:
            raise ValidationError('نظام الفرق معطّل لهذا النشاط.')

        return settings

    @staticmethod
    def validate_event_joinable(event):
        today = timezone.now().date()

        if not getattr(event, 'active', False):
            raise ValidationError('النشاط غير نشط.')

        if event.status != 'مقبول':
            raise ValidationError('النشاط غير معتمد.')

        if event.st_date <= today:
            raise ValidationError('لا يمكن الانضمام إلى نشاط بدأ بالفعل.')

        if event.end_date < today:
            raise ValidationError('لا يمكن الانضمام إلى نشاط انتهى بالفعل.')

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
            raise PermissionDenied('الطالب غير مؤهل للمشاركة في هذا النشاط.')

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

        raise PermissionDenied('ليس لديك صلاحية لإدارة هذا النشاط.')

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
            raise ValidationError('لا يمكن تعديل الفريق إلا إذا كان في حالة الانتظار.')

    @staticmethod
    def validate_team_size(team, settings):
        active_count = TeamService.get_active_member_count(team)

        if active_count < settings.min_members:
            raise ValidationError(
                f'عدد الأعضاء النشطين في الفريق هو {active_count}. '
                f'الحد الأدنى المطلوب هو {settings.min_members}.'
            )

        if active_count > settings.max_members:
            raise ValidationError(
                f'عدد الأعضاء النشطين في الفريق هو {active_count}. '
                f'الحد الأقصى المسموح به هو {settings.max_members}.'
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
            raise ValidationError('تم الوصول إلى الحد الأقصى لعدد الفرق المعتمدة.')

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
                f'لا توجد سعة كافية متبقية في النشاط. '
                f'المقاعد المتبقية: {remaining}، وعدد المقاعد المطلوبة للفريق: {needed_slots}.'
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
            raise ValidationError('تم رفض الطالب مسبقًا من هذا النشاط.')

        return participation

    @staticmethod
    @transaction.atomic
    def create_team(student, event_id, name):
        event = TeamService.get_event_for_update_or_404(event_id)

        TeamService.validate_event_joinable(event)
        TeamService.get_team_settings(event)
        TeamService.validate_student_eligible_for_event(student, event)

        if TeamService.active_team_membership_exists(event, student):
            raise ValidationError('الطالب موجود بالفعل في فريق لهذا النشاط.')

        if EventTeams.objects.filter(event=event, name=name).exists():
            raise ValidationError('يوجد فريق بهذا الاسم بالفعل في هذا النشاط.')

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
            team_lookup = EventTeams.objects.only(
                'team_id',
                'event_id',
            ).get(join_code=join_code)
        except EventTeams.DoesNotExist:
            raise NotFound('id الفريق غير صحيح.')

        event = TeamService.get_event_for_update_or_404(team_lookup.event_id)

        try:
            team = (
                EventTeams.objects
                .select_for_update()
                .select_related('event')
                .get(pk=team_lookup.team_id)
            )
        except EventTeams.DoesNotExist:
            raise NotFound('لم يتم العثور على الفريق.')

        TeamService.validate_event_joinable(event)
        settings = TeamService.get_team_settings(event)
        TeamService.validate_student_eligible_for_event(student, event)
        TeamService.validate_team_pending(team)

        if TeamService.active_team_membership_exists(event, student):
            raise ValidationError('الطالب موجود بالفعل في فريق لهذا النشاط.')

        current_count = TeamService.get_active_member_count(team)

        if current_count >= settings.max_members:
            raise ValidationError('الفريق مكتمل بالفعل.')

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
            raise ValidationError('الطالب عضو بالفعل في هذا الفريق.')

        return member

    @staticmethod
    @transaction.atomic
    def leave_team(student, team_id):
        team = TeamService.get_team_for_update_or_404(team_id)

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('لا يمكن مغادرة فريق معتمد.')

        if team.status in [
            EventTeams.TeamStatus.REJECTED,
            EventTeams.TeamStatus.CANCELLED,
        ]:
            raise ValidationError('لا يمكن مغادرة فريق مغلق.')

        try:
            membership = EventTeamMembers.objects.select_for_update().get(
                team=team,
                student=student,
                status=EventTeamMembers.MemberStatus.ACTIVE,
            )
        except EventTeamMembers.DoesNotExist:
            raise NotFound('أنت لست عضوًا نشطًا في هذا الفريق.')

        if membership.role == EventTeamMembers.MemberRole.CAPTAIN:
            active_count = TeamService.get_active_member_count(team)

            if active_count > 1:
                raise ValidationError(
                    'لا يمكن لقائد الفريق المغادرة أثناء وجود أعضاء نشطين آخرين.'
                )

            membership.status = EventTeamMembers.MemberStatus.LEFT
            membership.save(update_fields=['status'])

            team.status = EventTeams.TeamStatus.CANCELLED
            team.save(update_fields=['status', 'updated_at'])

            return {
                'message': 'تم إلغاء الفريق لأن قائد الفريق غادر.',
                'team_id': team.team_id,
            }

        membership.status = EventTeamMembers.MemberStatus.LEFT
        membership.save(update_fields=['status'])

        return {
            'message': 'تم مغادرة الفريق بنجاح.',
            'team_id': team.team_id,
        }

    @staticmethod
    @transaction.atomic
    def remove_member(actor, team_id, student_id, is_admin=False):
        team = TeamService.get_team_for_update_or_404(team_id)

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('لا يمكن إزالة أعضاء من فريق معتمد.')

        if team.status in [
            EventTeams.TeamStatus.REJECTED,
            EventTeams.TeamStatus.CANCELLED,
        ]:
            raise ValidationError('لا يمكن إزالة أعضاء من فريق مغلق.')

        if not is_admin:
            if team.captain_id != actor.student_id:
                raise PermissionDenied('يمكن لقائد الفريق فقط إزالة الأعضاء.')

            if int(student_id) == actor.student_id:
                raise ValidationError('لا يمكن لقائد الفريق إزالة نفسه.')

        try:
            membership = EventTeamMembers.objects.select_for_update().get(
                team=team,
                student_id=student_id,
                status=EventTeamMembers.MemberStatus.ACTIVE,
            )
        except EventTeamMembers.DoesNotExist:
            raise NotFound('لم يتم العثور على عضو نشط في هذا الفريق.')

        if membership.role == EventTeamMembers.MemberRole.CAPTAIN:
            raise ValidationError('لا يمكن إزالة قائد الفريق.')

        membership.status = EventTeamMembers.MemberStatus.REMOVED
        membership.save(update_fields=['status'])

        return {
            'message': 'تم إزالة العضو بنجاح.',
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
            raise ValidationError('لا يمكن إنشاء الفريق إلا لنشاط معتمد.')

        if event.end_date < timezone.now().date():
            raise ValidationError('لا يمكن إنشاء فريق لنشاط منتهٍ.')

        if not student_ids:
            raise ValidationError('لا يمكن أن تكون قائمة معرفات الطلاب فارغة.')

        student_ids = list(dict.fromkeys([int(student_id) for student_id in student_ids]))
        captain_id = int(captain_id)

        if captain_id not in student_ids:
            raise ValidationError('يجب أن يكون قائد الفريق ضمن قائمة الطلاب.')

        if len(student_ids) < settings.min_members:
            raise ValidationError(f'الحد الأدنى لحجم الفريق هو {settings.min_members}.')

        if len(student_ids) > settings.max_members:
            raise ValidationError(f'الحد الأقصى لحجم الفريق هو {settings.max_members}.')

        if EventTeams.objects.filter(event=event, name=name).exists():
            raise ValidationError('يوجد فريق بهذا الاسم بالفعل في هذا النشاط.')

        students = list(
            Students.objects
            .select_related('faculty')
            .filter(student_id__in=student_ids)
        )

        found_ids = {student.student_id for student in students}
        missing_ids = set(student_ids) - found_ids

        if missing_ids:
            raise ValidationError(f'بعض الطلاب غير موجودين: {sorted(missing_ids)}.')

        for student in students:
            TeamService.validate_student_eligible_for_event(student, event)

            if TeamService.active_team_membership_exists(event, student):
                raise ValidationError(
                    f'الطالب رقم {student.student_id} موجود بالفعل في فريق آخر لهذا النشاط.'
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
            raise NotFound('لم يتم العثور على الفريق.')

        TeamService.validate_admin_can_manage_event(admin, event)

        if event.status != 'مقبول':
            raise ValidationError('يجب اعتماد النشاط قبل اعتماد الفرق.')

        if event.end_date < timezone.now().date():
            raise ValidationError('لا يمكن اعتماد الفريق بعد انتهاء النشاط.')

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('الفريق معتمد بالفعل.')

        if team.status in [
            EventTeams.TeamStatus.REJECTED,
            EventTeams.TeamStatus.CANCELLED,
        ]:
            raise ValidationError('لا يمكن اعتماد فريق مرفوض أو ملغي.')

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
            raise ValidationError('بعض أعضاء الفريق لا يملكون سجلات مشاركة مرتبطة.')

        participation_ids = list(
            active_members.values_list('participation_id', flat=True)
        )

        if not participation_ids:
            raise ValidationError('الفريق لا يحتوي على سجلات مشاركة مرتبطة.')

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
            'message': 'تم اعتماد الفريق بنجاح.',
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
            raise NotFound('لم يتم العثور على الفريق.')

        TeamService.validate_admin_can_manage_event(admin, event)

        if team.status == EventTeams.TeamStatus.APPROVED:
            raise ValidationError('لا يمكن رفض فريق معتمد بالفعل.')

        if team.status == EventTeams.TeamStatus.REJECTED:
            raise ValidationError('الفريق مرفوض بالفعل.')

        if team.status == EventTeams.TeamStatus.CANCELLED:
            raise ValidationError('لا يمكن رفض فريق ملغي.')

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
            'message': 'تم رفض الفريق بنجاح.',
            'team_id': team.team_id,
            'team_name': team.name,
            'rejected_members': len(participation_ids),
            'reason': reason,
        }

    @staticmethod
    @transaction.atomic
    def assign_team_result(admin, event_id, team_id, rank=None, is_winner=None):
        event = TeamService.get_event_for_update_or_404(event_id)

        try:
            team = EventTeams.objects.select_for_update().get(
                pk=team_id,
                event=event,
            )
        except EventTeams.DoesNotExist:
            raise NotFound('لم يتم العثور على الفريق.')

        TeamService.validate_admin_can_manage_event(admin, event)

        if team.status != EventTeams.TeamStatus.APPROVED:
            raise ValidationError('يمكن تسجيل النتائج للفرق المعتمدة فقط.')

        if rank is None and is_winner is None:
            raise ValidationError('يجب إرسال الترتيب أو تحديد حالة الفوز على الأقل.')

        if is_winner is True and rank is None:
            rank = 1

        if rank == 1:
            is_winner = True

        now = timezone.now()

        if is_winner is True:
            old_winner_teams = (
                EventTeams.objects
                .select_for_update()
                .filter(
                    event=event,
                    is_winner=True,
                )
                .exclude(pk=team.pk)
            )

            old_winner_participation_ids = EventTeamMembers.objects.filter(
                team__in=old_winner_teams,
                status=EventTeamMembers.MemberStatus.ACTIVE,
                participation__isnull=False,
            ).values_list('participation_id', flat=True)

            old_winner_teams.update(
                is_winner=False,
                rank=None,
                result_assigned_by=admin,
                result_assigned_at=now,
            )

            Prtcps.objects.filter(
                id__in=old_winner_participation_ids,
            ).update(rank=None)

        if rank is not None:
            rank_exists = EventTeams.objects.select_for_update().filter(
                event=event,
                rank=rank,
            ).exclude(pk=team.pk).exists()

            if rank_exists:
                raise ValidationError(f'الترتيب {rank} مخصص بالفعل لفريق آخر.')

        team.rank = rank
        team.is_winner = bool(is_winner)
        team.result_assigned_by = admin
        team.result_assigned_at = now
        team.save(update_fields=[
            'rank',
            'is_winner',
            'result_assigned_by',
            'result_assigned_at',
            'updated_at',
        ])

        participation_ids = EventTeamMembers.objects.filter(
            team=team,
            status=EventTeamMembers.MemberStatus.ACTIVE,
            participation__isnull=False,
        ).values_list('participation_id', flat=True)

        Prtcps.objects.filter(
            id__in=participation_ids,
        ).update(rank=rank)

        return {
            'message': 'تم تسجيل نتائج الفريق بنجاح.',
            'team_id': team.team_id,
            'team_name': team.name,
            'rank': team.rank,
            'is_winner': team.is_winner,
        }