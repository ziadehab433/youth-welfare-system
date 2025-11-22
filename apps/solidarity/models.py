# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.postgres.fields import ArrayField 
from django.db import models

class Solidarities(models.Model):
    solidarity_id = models.AutoField(primary_key=True)
    student = models.ForeignKey('accounts.Students', models.DO_NOTHING, blank=True, null=True)
    faculty = models.ForeignKey('Faculties', models.DO_NOTHING, blank=True, null=True)
    req_status = models.TextField(blank=True, null=True)  # This field type is a guess.
    created_at = models.DateTimeField(blank=True, null=True , auto_now_add=True)
    family_numbers = models.IntegerField()
    father_status = models.CharField(max_length=50, blank=True, null=True)
    mother_status = models.CharField(max_length=50, blank=True, null=True)
    father_income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mother_income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    arrange_of_brothers = models.IntegerField(blank=True, null=True)
    m_phone_num = models.TextField(blank=True, null=True)
    f_phone_num = models.TextField(blank=True, null=True)
    reason = models.TextField()
    disabilities = models.TextField(blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    acd_status = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255)
    approved_by = models.ForeignKey('Admins', models.DO_NOTHING, db_column='approved_by', blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    req_type = models.TextField(blank=True, null=True)  # This field type is a guess.
    housing_status = models.TextField(blank=True, null=True)  # This field type is a guess.
    total_discount = models.FloatField(blank=True, null=True)
    discount_type = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="List of discount types applied"
    )


    class Meta:
        managed = False
        db_table = 'solidarities'


class Logs(models.Model):
    log_id = models.AutoField(primary_key=True)
    actor = models.ForeignKey('Admins', models.DO_NOTHING)
    action = models.CharField(max_length=100)
    #event = models.ForeignKey('Events', models.DO_NOTHING, blank=True, null=True)
    solidarity = models.ForeignKey(Solidarities, models.DO_NOTHING, blank=True, null=True)
    #family = models.ForeignKey('Families', models.DO_NOTHING, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    logged_at = models.DateTimeField(blank=True, null=True)
    actor_type = models.TextField(blank=True, null=True)  # This field type is a guess.
    target_type = models.TextField()  # This field type is a guess.
    event  = models.ForeignKey('event.Events',     models.DO_NOTHING,
                               blank=True, null=True)
    family = models.ForeignKey('family.Families', models.DO_NOTHING,
                               blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'logs'


def solidarity_doc_upload_path(instance, filename):
    return f"uploads/solidarity/{instance.solidarity.solidarity_id}/{filename}" 

class SolidarityDocs(models.Model):
    doc_id = models.AutoField(primary_key=True)
    solidarity = models.ForeignKey(Solidarities, models.DO_NOTHING)
    doc_type = models.CharField(max_length=50, choices=[
        ('بحث احتماعي', 'بحث احتماعي'),
        ('اثبات دخل', 'اثبات دخل'),
        ('ص.ب ولي امر', 'ص.ب ولي امر'),
        ('ص.ب شخصية', 'ص.ب شخصية'),
        ('حبازة زراعية', 'حبازة زراعية'),
    ])
    # file_name = models.CharField(max_length=255)
    # file_path = models.CharField(max_length=255)
    file = models.FileField(upload_to=solidarity_doc_upload_path  , null=True, blank=True) 
    mime_type = models.CharField(max_length=80)
    file_size = models.IntegerField(blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'solidarity_docs'
        unique_together = (('solidarity', 'doc_type'),)

class Departments(models.Model):
    dept_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'departments'




class Faculties(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    major = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    
    created_at = models.DateTimeField()
    
    aff_discount = ArrayField(
        models.FloatField(), 
        default=list, 
        blank=True, 
        null=True
    )
    reg_discount = ArrayField(
        models.FloatField(), 
        default=list, 
        blank=True, 
        null=True
    )
    bk_discount = ArrayField(
        models.FloatField(), 
        default=list, 
        blank=True, 
        null=True
    )
    full_discount = ArrayField(
        models.FloatField(), 
        default=list, 
        blank=True, 
        null=True
    )

    class Meta:
        managed = False
        db_table = 'faculties'

class Admins(models.Model):
    admin_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField()
    faculty = models.ForeignKey(Faculties, models.DO_NOTHING, blank=True, null=True)
    dept = models.ForeignKey(Departments, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    can_create = models.BooleanField(blank=True, null=True)
    can_update = models.BooleanField(blank=True, null=True)
    can_read = models.BooleanField(blank=True, null=True)
    can_delete = models.BooleanField(blank=True, null=True)
    acc_status = models.CharField(max_length=20, blank=True, null=True)
    role = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'admins'


#not needed tables (models) just quick fix


