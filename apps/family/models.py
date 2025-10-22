# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Families(models.Model):
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    faculty = models.ForeignKey('solidarity.Faculties', models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey('solidarity.Admins', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    approved_by = models.ForeignKey('solidarity.Admins', models.DO_NOTHING, db_column='approved_by', related_name='families_approved_by_set', blank=True, null=True)
    status = models.TextField(blank=True, null=True)  # This field type is a guess.
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'families'
