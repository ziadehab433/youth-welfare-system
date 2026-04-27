from django.db import models
from apps.accounts.models import Students, AdminsUser
from apps.solidarity.models import Faculties


class Clans(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    clan_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    faculty = models.OneToOneField(
        Faculties,
        on_delete=models.DO_NOTHING,
        db_column='faculty_id',
        related_name='clan'
    )

    created_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.DO_NOTHING,
        db_column='created_by',
        blank=True,
        null=True,
        related_name='created_clans'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    min_members = models.IntegerField(default=50)

    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clans'

    def __str__(self):
        return self.name


class ClanGroups(models.Model):

    group_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    clan = models.ForeignKey(
        Clans,
        on_delete=models.DO_NOTHING,
        db_column='clan_id',
        related_name='groups'
    )

    display_order = models.IntegerField(default=1)

    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clan_groups'
        ordering = ['display_order']

    def __str__(self):
        return f"{self.name} - {self.clan.name}"


class ScoutMembers(models.Model):

    CLAN_LEVEL_ROLES = [
        ('CLAN_LEADER', 'Clan Leader'),
        ('ASSISTANT_MALE', 'Assistant Male'),
        ('ASSISTANT_FEMALE', 'Assistant Female'),
        ('HEAD_ROVER', 'Head Rover'),
        ('SECRETARY', 'Secretary'),
        ('EQUIPMENT_MANAGER', 'Equipment Manager'),
        ('VETERAN', 'Veteran'),
    ]

    GROUP_LEVEL_ROLES = [
        ('GROUP_LEADER_MALE', 'Group Leader Male'),
        ('GROUP_LEADER_FEMALE', 'Group Leader Female'),
        ('GROUP_ASSISTANT_MALE', 'Group Assistant Male'),
        ('GROUP_ASSISTANT_FEMALE', 'Group Assistant Female'),
    ]

    MEMBER_ROLE = [
        ('MEMBER', 'Member'),
    ]

    ROLE_CHOICES = CLAN_LEVEL_ROLES + GROUP_LEVEL_ROLES + MEMBER_ROLE

    MALE_ONLY_ROLES = [
        'ASSISTANT_MALE',
        'GROUP_LEADER_MALE',
        'GROUP_ASSISTANT_MALE',
    ]

    FEMALE_ONLY_ROLES = [
        'ASSISTANT_FEMALE',
        'GROUP_LEADER_FEMALE',
        'GROUP_ASSISTANT_FEMALE',
    ]

    STATUS_CHOICES = [
        ('منتظر', 'منتظر'),
        ('مقبول', 'مقبول'),
        ('مرفوض', 'مرفوض'),
    ]

    scout_member_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Students,
        on_delete=models.DO_NOTHING,
        db_column='student_id',
        related_name='scout_memberships'
    )

    clan = models.ForeignKey(
        Clans,
        on_delete=models.DO_NOTHING,
        db_column='clan_id',
        related_name='members'
    )

    group = models.ForeignKey(
        ClanGroups,
        on_delete=models.DO_NOTHING,
        db_column='group_id',
        blank=True,
        null=True,
        related_name='group_members'
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='MEMBER'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='منتظر'
    )

    reviewed_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.DO_NOTHING,
        db_column='reviewed_by',
        blank=True,
        null=True,
        related_name='reviewed_scouts'
    )

    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    joined_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scout_members'
        unique_together = (('student', 'clan'),)

    def __str__(self):
        return f"{self.student.name} - {self.clan.name} ({self.get_role_display()})"

    @property
    def is_accepted(self):
        return self.status == 'مقبول'

    @property
    def is_pending(self):
        return self.status == 'منتظر'

    @property
    def is_rejected(self):
        return self.status == 'مرفوض'

    @property
    def is_leader(self):
        return self.role != 'MEMBER'

    @property
    def is_clan_level_leader(self):
        return self.role in [r[0] for r in self.CLAN_LEVEL_ROLES]

    @property
    def is_group_level_leader(self):
        return self.role in [r[0] for r in self.GROUP_LEVEL_ROLES]

    @property
    def has_group(self):
        return self.group_id is not None