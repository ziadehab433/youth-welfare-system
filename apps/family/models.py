# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
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
        db_column='faculty_id'
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
    family = models.ForeignKey(
        Families, 
        models.CASCADE, 
        primary_key=False,
        db_column='family_id'
    )
    student = models.ForeignKey(
        Students, 
        models.CASCADE,
        db_column='student_id'
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
        unique_together = ('family', 'student')  # Composite Primary Key
        indexes = [
            models.Index(fields=['student'], name='idx_family_members_student'),
        ]

    def __str__(self):
        return f"{self.family.name} - {self.student}"

