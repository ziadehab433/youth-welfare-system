from django.db import models
from apps.accounts.models import Students, AdminsUser
from apps.solidarity.models import Faculties


# ============================================
# 1. Clan
# ============================================
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
        on_delete=models.CASCADE,
        related_name='clan'
    )

    created_by = models.ForeignKey(
        AdminsUser,  
        on_delete=models.SET_NULL,  
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


# ============================================
# 2. Clan Group (Raht)
# ============================================
class ClanGroups(models.Model):

    group_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    clan = models.ForeignKey(
        Clans,
        on_delete=models.CASCADE,
        related_name='groups'
    )

    display_order = models.IntegerField(default=1)

    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clan_groups'

    def __str__(self):
        return f"{self.name} - {self.clan.name}"


# ============================================
# 3. Scout Member
# ============================================
class ScoutMembers(models.Model):

    ROLE_CHOICES = [
        ('CLAN_LEADER', 'Clan Leader'),
        ('ASSISTANT_MALE', 'Assistant Male'),
        ('ASSISTANT_FEMALE', 'Assistant Female'),
        ('HEAD_ROVER', 'Head Rover'),
        ('SECRETARY', 'Secretary'),
        ('EQUIPMENT_MANAGER', 'Equipment Manager'),
        ('VETERAN', 'Veteran'),

        ('GROUP_LEADER_MALE', 'Group Leader Male'),
        ('GROUP_LEADER_FEMALE', 'Group Leader Female'),
        ('GROUP_ASSISTANT_MALE', 'Group Assistant Male'),
        ('GROUP_ASSISTANT_FEMALE', 'Group Assistant Female'),

        ('MEMBER', 'Member'),
    ]

    STATUS_CHOICES = [
        ('منتظر', 'منتظر'),
        ('موافقة مبدئية', 'موافقة مبدئية'),
        ('مقبول', 'مقبول'),
        ('مرفوض', 'مرفوض'),
    ]

    scout_member_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Students, 
        on_delete=models.CASCADE,  
        related_name='scout_membership'
    )

    clan = models.ForeignKey(
        Clans,
        on_delete=models.CASCADE,  
        related_name='members'
    )

    group = models.ForeignKey(
        ClanGroups,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='members'
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
        on_delete=models.SET_NULL,  
        blank=True,
        null=True,
        db_column='reviewed_by',
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
        return f"{self.student.name} - {self.clan.name} ({self.role})"