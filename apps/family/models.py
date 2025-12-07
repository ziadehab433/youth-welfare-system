from django.db import models
from apps.solidarity.models import Departments 
from apps.accounts.models import Students
from apps.solidarity.models import Faculties 
from apps.accounts.models import AdminsUser


class Families(models.Model):
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    faculty = models.ForeignKey(
        Faculties, 
        models.DO_NOTHING, 
        blank=True, 
        null=True,
        db_column='faculty_id',
    )
    created_by = models.ForeignKey(
        AdminsUser, 
        models.DO_NOTHING, 
        db_column='created_by', 
        blank=True, 
        null=True,
        related_name='families_created_by_set'
    )
    approved_by = models.ForeignKey(
        AdminsUser, 
        models.DO_NOTHING, 
        db_column='approved_by', 
        blank=True, 
        null=True,
        related_name='families_approved_by_set'
    )
    status = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    min_limit = models.IntegerField(default=50)
    type = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'families'

    def __str__(self):
        return self.name


class FamilyMembers(models.Model):
    # REMOVE the id field - database doesn't have it
    family = models.ForeignKey(
        Families, 
        models.CASCADE,
        db_column='family_id',
        related_name='family_members'
    )
    student = models.ForeignKey(
        Students, 
        models.CASCADE,
        db_column='student_id',
        primary_key=True  # Use student as part of composite key
    )
    role = models.CharField(max_length=30, default='member')
    status = models.TextField(blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    dept = models.ForeignKey(
        Departments, 
        models.DO_NOTHING, 
        blank=True, 
        null=True,
        db_column='dept_id'
    )

    class Meta:
        managed = False
        db_table = 'family_members'
        unique_together = ('family', 'student')
        indexes = [
            models.Index(fields=['student'], name='idx_family_members_student'),
        ]

    def __str__(self):
        return f"{self.family.name} - {self.student}"
    


class Posts(models.Model):
    post_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    family = models.ForeignKey(
        Families,
        models.CASCADE,
        db_column='family_id'
    )
    faculty = models.ForeignKey(
        Faculties,
        models.CASCADE,
        db_column='faculty_id'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'posts'
        indexes = [
            models.Index(fields=['family_id'], name='idx_posts_family_id'),
            models.Index(fields=['faculty_id'], name='idx_posts_faculty_id'),
            models.Index(fields=['-created_at'], name='idx_posts_created_at'),
        ]

    def __str__(self):
        return self.title