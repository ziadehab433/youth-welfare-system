# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from apps.solidarity.models import Departments 
from apps.family.models import Families , Faculties 
from apps.accounts.models import AdminsUser, Students 
from django.contrib.postgres.fields import ArrayField 





class Plans(models.Model):
    plan_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    term = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    faculty = models.ForeignKey(
    Faculties,
    models.SET_NULL,
    blank=True,
    null=True,
    db_column='faculty_id',
    related_name='plans'
)

    class Meta:
        managed = False
        db_table = 'plans'
        indexes = [
            models.Index(fields=['name'], name='idx_plans_name'),
            models.Index(fields=['faculty'], name='idx_plans_faculty_id'),
        ]

    def __str__(self):
        return self.name
    




class Events(models.Model):
    event_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    dept = models.ForeignKey(
        Departments, 
        models.SET_NULL, 
        blank=True, 
        null=True,
        db_column='dept_id'
    )
    faculty = models.ForeignKey(
        Faculties, 
        models.SET_NULL, 
        blank=True, 
        null=True,
        db_column='faculty_id'
    )
    created_by = models.ForeignKey(
        AdminsUser, 
        models.RESTRICT,
        db_column='created_by'
    )
    updated_at = models.DateTimeField(auto_now=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    restrictions = models.TextField(blank=True, null=True)
    reward = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    # imgs = models.CharField(max_length=255, blank=True, null=True)
    st_date = models.DateField()
    end_date = models.DateField()
    s_limit = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.TextField(blank=True, null=True)
    family = models.ForeignKey(
        Families, 
        models.DO_NOTHING, 
        blank=True, 
        null=True,
        db_column='family_id'
    )
    resource = models.TextField(blank=True, null=True)



    selected_facs = ArrayField(
    models.IntegerField(),
    blank=True,
    null=True,
    help_text="List of faculty IDs. If NULL, event applies to all faculties."
)
    plan = models.ForeignKey(
        Plans,
        models.SET_NULL,
        blank=True,
        null=True,
        db_column='plan_id',
        related_name='events'
    )
    active = models.BooleanField(default=True)


    class Meta:
        managed = False
        db_table = 'events'
        indexes = [
            models.Index(fields=['created_by'], name='idx_events_created_by'),
            models.Index(fields=['dept'], name='idx_events_dept_id'),
            models.Index(fields=['faculty'], name='idx_events_faculty_id'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F('st_date')),
                name='events_check'
            )
        ]

    def __str__(self):
        return self.title
from django.db import connection

class Prtcps(models.Model):
    id = models.BigAutoField(primary_key=True)

    event = models.ForeignKey(Events, models.DO_NOTHING, related_name="prtcps_set")
    student = models.ForeignKey(Students, models.DO_NOTHING)

    rank = models.IntegerField(blank=True, null=True)
    reward = models.CharField(max_length=255, blank=True, null=True)
    status = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "prtcps"
        unique_together = (("event", "student"),)


class EventDocs(models.Model):
    doc_id = models.AutoField(primary_key=True)
    event = models.ForeignKey(
        Events, 
        on_delete=models.CASCADE,
        db_column='event_id',
        related_name='event_docs'
    )
    doc_type = models.CharField(max_length=40)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=80, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        AdminsUser,
        on_delete=models.SET_NULL,
        db_column='uploaded_by',
        null=True,
        blank=True
    )
    
    @property
    def file_url(self):
        """Generate full file URL"""
        from django.conf import settings
        if self.file_path:
            return f"{settings.MEDIA_URL}{self.file_path}"
        return None

    class Meta:
        managed = True
        db_table = 'event_docs'
        indexes = [
            models.Index(fields=['event'], name='idx_event_docs_event'),
        ]

    def __str__(self):
        return f"{self.doc_type} - Event {self.event.event_id}"



    # IF we want to ignore writing SQL directly, we can update DB by drop the composite key (just will be a constraint) , then add an id field as primary key , finally no need to override save method.
    # using this code :
    #     event = models.ForeignKey(
    #     Events, 
    #     on_delete=models.CASCADE,  # Better than DO_NOTHING
    #     db_column='event_id',
    #     related_name='prtcps_set'
    # )
    # student = models.ForeignKey(
    #     Students, 
    #     on_delete=models.CASCADE,
    #     db_column='student_id',
    #     related_name='event_registrations'
    # )