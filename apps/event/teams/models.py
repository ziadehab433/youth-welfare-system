import secrets
import string

from django.db import models
from django.db.models import Q, F

from apps.accounts.models import AdminsUser, Students
from apps.event.models import Events, Prtcps


class EventTeamSettings(models.Model):
    setting_id = models.AutoField(primary_key=True)

    event = models.OneToOneField(
        Events,
        on_delete=models.CASCADE,
        related_name='team_settings',
        db_column='event_id',
    )

    enabled = models.BooleanField(default=True)

    min_members = models.PositiveIntegerField(default=2)
    max_members = models.PositiveIntegerField(default=5)

    max_teams = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Optional maximum number of approved teams for this event.',
    )

    allow_individual_join = models.BooleanField(default=False)
    require_team_approval = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_event_team_settings',
        db_column='created_by',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'event'
        db_table = 'event_team_settings'
        indexes = [
            models.Index(fields=['event'], name='idx_evt_team_set_event'),
            models.Index(fields=['enabled'], name='idx_evt_team_set_enabled'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(min_members__gte=1),
                name='chk_evt_team_min_gte_1',
            ),
            models.CheckConstraint(
                check=Q(max_members__gte=F('min_members')),
                name='chk_evt_team_max_gte_min',
            ),
            models.CheckConstraint(
                check=Q(max_teams__isnull=True) | Q(max_teams__gte=1),
                name='chk_evt_team_max_teams_gte_1',
            ),
        ]

    def __str__(self):
        return f'Team settings for event {self.event_id}'


class EventTeams(models.Model):
    class TeamStatus(models.TextChoices):
        PENDING = 'منتظر', 'منتظر'
        APPROVED = 'مقبول', 'مقبول'
        REJECTED = 'مرفوض', 'مرفوض'
        CANCELLED = 'ملغي', 'ملغي'

    team_id = models.AutoField(primary_key=True)

    event = models.ForeignKey(
        Events,
        on_delete=models.CASCADE,
        related_name='teams',
        db_column='event_id',
    )

    name = models.CharField(max_length=150)

    captain = models.ForeignKey(
        Students,
        on_delete=models.CASCADE,
        related_name='captained_event_teams',
        db_column='captain_id',
    )

    join_code = models.CharField(
        max_length=12,
        unique=True,
        db_index=True,
    )

    status = models.CharField(
        max_length=30,
        choices=TeamStatus.choices,
        default=TeamStatus.PENDING,
        db_index=True,
    )

    approved_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_event_teams',
        db_column='approved_by',
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    rejected_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_event_teams',
        db_column='rejected_by',
    )

    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)

    created_by_admin = models.ForeignKey(
        AdminsUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manually_created_event_teams',
        db_column='created_by_admin',
    )

    rank = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Team rank in the event. Example: 1, 2, 3.',
    )

    is_winner = models.BooleanField(
        default=False,
        help_text='True if this team is the winner of the event.',
    )

    result_assigned_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_team_results',
        db_column='result_assigned_by',
    )

    result_assigned_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_join_code(length=8):
        alphabet = string.ascii_uppercase + string.digits

        while True:
            code = ''.join(secrets.choice(alphabet) for _ in range(length))
            if not EventTeams.objects.filter(join_code=code).exists():
                return code

    class Meta:
        app_label = 'event'
        db_table = 'event_teams'
        indexes = [
            models.Index(fields=['event'], name='idx_evt_teams_event'),
            models.Index(fields=['status'], name='idx_evt_teams_status'),
            models.Index(fields=['captain'], name='idx_evt_teams_captain'),
            models.Index(fields=['rank'], name='idx_evt_teams_rank'),
            models.Index(fields=['is_winner'], name='idx_evt_teams_winner'),
            models.Index(fields=['event', 'status'], name='idx_evt_teams_event_status'),
            models.Index(fields=['event', 'rank'], name='idx_evt_teams_event_rank'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'name'],
                name='uniq_evt_team_name_per_event',
            ),
            models.UniqueConstraint(
                fields=['event'],
                condition=Q(is_winner=True),
                name='uniq_evt_one_winner_per_event',
            ),
            models.UniqueConstraint(
                fields=['event', 'rank'],
                condition=Q(rank__isnull=False),
                name='uniq_evt_team_rank_per_event',
            ),
            models.CheckConstraint(
                check=Q(rank__isnull=True) | Q(rank__gte=1),
                name='chk_evt_team_rank_gte_1',
            ),
        ]

    def __str__(self):
        return f'{self.name} - Event {self.event_id}'


class EventTeamMembers(models.Model):
    class MemberRole(models.TextChoices):
        CAPTAIN = 'قائد', 'قائد'
        MEMBER = 'عضو', 'عضو'
        SUBSTITUTE = 'بديل', 'بديل'

    class MemberStatus(models.TextChoices):
        ACTIVE = 'نشط', 'نشط'
        LEFT = 'انسحب', 'انسحب'
        REMOVED = 'تمت إزالته', 'تمت إزالته'

    member_id = models.AutoField(primary_key=True)

    team = models.ForeignKey(
        EventTeams,
        on_delete=models.CASCADE,
        related_name='members',
        db_column='team_id',
    )

    student = models.ForeignKey(
        Students,
        on_delete=models.CASCADE,
        related_name='event_team_memberships',
        db_column='student_id',
    )

    participation = models.ForeignKey(
        Prtcps,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_memberships',
        db_column='participation_id',
    )

    role = models.CharField(
        max_length=30,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER,
    )

    status = models.CharField(
        max_length=30,
        choices=MemberStatus.choices,
        default=MemberStatus.ACTIVE,
        db_index=True,
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'event'
        db_table = 'event_team_members'
        indexes = [
            models.Index(fields=['team'], name='idx_evt_team_mem_team'),
            models.Index(fields=['student'], name='idx_evt_team_mem_student'),
            models.Index(fields=['participation'], name='idx_evt_team_mem_prtcps'),
            models.Index(fields=['status'], name='idx_evt_team_mem_status'),
            models.Index(fields=['team', 'status'], name='idx_evt_team_mem_team_status'),
            models.Index(fields=['student', 'status'], name='idx_evt_mem_st_status'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'student'],
                name='uniq_evt_team_student_once',
            ),
        ]

    def __str__(self):
        return f'Student {self.student_id} in team {self.team_id}'