from django.db import models
from apps.accounts.models import Students, AdminsUser
from apps.solidarity.models import Faculties


class Clans(models.Model):

    STATUS_CHOICES = [
        ('نشط', 'نشط'),
        ('غير نشط', 'غير نشط'),
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
        default='نشط'
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
        ('قائد العشيرة', 'قائد العشيرة'),
        ('مساعد قائد', 'مساعد قائد'),
        ('مساعدة قائد', 'مساعدة قائد'),
        ('رائد أكبر', 'رائد أكبر'),
        ('سكرتير', 'سكرتير'),
        ('مسؤول عهدة', 'مسؤول عهدة'),
        ('قائد السواعد', 'قائد السواعد'),
    ]

    GROUP_LEVEL_ROLES = [
        ('رائد رهط', 'رائد رهط'),
        ('رائدة رهط', 'رائدة رهط'),
        ('مساعد رائد', 'مساعد رائد'),
        ('مساعدة رائد', 'مساعدة رائد'),
    ]

    MEMBER_ROLE = [
        ('عضو', 'عضو'),
    ]

    ROLE_CHOICES = CLAN_LEVEL_ROLES + GROUP_LEVEL_ROLES + MEMBER_ROLE

    MALE_ONLY_ROLES = [
        'مساعد قائد',
        'رائد رهط',
        'مساعد رائد',
    ]

    FEMALE_ONLY_ROLES = [
        'مساعدة قائد',
        'رائدة رهط',
        'مساعدة رائد',
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
        default='عضو'
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
        return self.role != 'عضو'

    @property
    def is_clan_level_leader(self):
        return self.role in [r[0] for r in self.CLAN_LEVEL_ROLES]

    @property
    def is_group_level_leader(self):
        return self.role in [r[0] for r in self.GROUP_LEVEL_ROLES]

    @property
    def has_group(self):
        return self.group_id is not None
class UniversityScoutPrograms(models.Model):

    program_id = models.AutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.DO_NOTHING,
        db_column='created_by',
        blank=True,
        null=True,
        related_name='created_university_programs'
    )

    created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'university_scout_programs'

    def __str__(self):

        return self.name


class UniversityScoutMembers(models.Model):

    UNIVERSITY_ROLES = [
        ('قائد عشاير الجامعة', 'قائد عشاير الجامعة'),
        ('مساعد قائد العشاير', 'مساعد قائد العشاير'),
        ('منفذ برامج', 'منفذ برامج'),
        ('قائد الجوالات', 'قائد الجوالات'),
        ('سكرتير العشاير', 'سكرتير العشاير'),
        ('قائد السواعد', 'قائد السواعد'),
    ]

    university_member_id = models.AutoField(
        primary_key=True
    )

    scout_member = models.ForeignKey(
        ScoutMembers,
        on_delete=models.DO_NOTHING,
        db_column='scout_member_id',
        related_name='university_memberships'
    )

    university_role = models.CharField(
        max_length=100,
        choices=UNIVERSITY_ROLES,
        blank=True,
        null=True
    )

    selected_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.DO_NOTHING,
        db_column='selected_by',
        blank=True,
        null=True,
        related_name='selected_university_members'
    )

    created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'university_scout_members'

    def __str__(self):

        return (
            f"{self.scout_member.student.name}"
        )


class UniversityScoutProgramMembers(models.Model):

    id = models.AutoField(primary_key=True)

    university_member = models.ForeignKey(
        UniversityScoutMembers,
        on_delete=models.DO_NOTHING,
        db_column='university_member_id',
        related_name='program_memberships'
    )

    program = models.ForeignKey(
        UniversityScoutPrograms,
        on_delete=models.DO_NOTHING,
        db_column='program_id',
        related_name='program_members'
    )

    created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = 'university_scout_program_members'

    def __str__(self):

        return (
            f"{self.university_member.scout_member.student.name}"
            f" - "
            f"{self.program.name}"
        )