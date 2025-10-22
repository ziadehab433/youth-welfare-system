# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Events(models.Model):
    event_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    dept = models.ForeignKey('solidarity.Departments', models.DO_NOTHING, blank=True, null=True)
    faculty = models.ForeignKey('solidarity.Faculties', models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey('solidarity.Admins', models.DO_NOTHING, db_column='created_by')
    updated_at = models.DateTimeField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    restrictions = models.TextField(blank=True, null=True)
    reward = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)  # This field type is a guess.
    imgs = models.CharField(max_length=255, blank=True, null=True)
    st_date = models.DateField()
    end_date = models.DateField()
    s_limit = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'events'
