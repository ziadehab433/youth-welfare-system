from django.db import models


class Faculties(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    major = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'faculties'


class Departments(models.Model):
    dept_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'departments'


class Admins(models.Model):
    admin_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField()
    role = models.TextField()
    faculty = models.OneToOneField(Faculties, on_delete=models.DO_NOTHING, blank=True, null=True)
    dept = models.ForeignKey(Departments, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    can_create = models.BooleanField(blank=True, null=True)
    can_update = models.BooleanField(blank=True, null=True)
    can_read = models.BooleanField(blank=True, null=True)
    can_delete = models.BooleanField(blank=True, null=True)
    acc_status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'admins'


class Students(models.Model):
    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField()
    faculty = models.ForeignKey(Faculties, on_delete=models.DO_NOTHING)
    profile_photo = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=1)
    nid = models.TextField(unique=True)
    uid = models.TextField(unique=True)
    phone_number = models.TextField(unique=True)
    address = models.CharField(max_length=255)
    acd_year = models.CharField(max_length=50)
    join_date = models.DateField()
    gpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    major = models.CharField(max_length=255)

    class Meta:
        db_table = 'students'


class Events(models.Model):
    event_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    dept = models.ForeignKey(Departments, on_delete=models.DO_NOTHING, blank=True, null=True)
    faculty = models.ForeignKey(Faculties, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(Admins, on_delete=models.DO_NOTHING, db_column='created_by')
    updated_at = models.DateTimeField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    restrictions = models.TextField(blank=True, null=True)
    reward = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    imgs = models.CharField(max_length=255, blank=True, null=True)
    st_date = models.DateField()
    end_date = models.DateField()
    s_limit = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'events'


class Families(models.Model):
    family_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    faculty = models.ForeignKey(Faculties, on_delete=models.DO_NOTHING, blank=True, null=True)
    created_by = models.ForeignKey(Admins, on_delete=models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    approved_by = models.ForeignKey(Admins, on_delete=models.DO_NOTHING, db_column='approved_by', related_name='families_approved_by_set', blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'families'


class FamilyMembers(models.Model):
    family = models.ForeignKey(Families, on_delete=models.DO_NOTHING)
    student = models.ForeignKey(Students, on_delete=models.DO_NOTHING)
    role = models.CharField(max_length=30, blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    joined_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'family_members'
        unique_together = (('family', 'student'),)


class Solidarities(models.Model):
    solidarity_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Students, on_delete=models.DO_NOTHING, blank=True, null=True)
    faculty = models.ForeignKey(Faculties, on_delete=models.DO_NOTHING, blank=True, null=True)
    req_status = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
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
    docs = models.CharField(max_length=255, blank=True, null=True)
    disabilities = models.TextField(blank=True, null=True)
    housing_status = models.TextField(blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    acd_status = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255)
    approved_by = models.ForeignKey(Admins, on_delete=models.DO_NOTHING, db_column='approved_by', blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'solidarities'


class Documents(models.Model):
    doc_id = models.AutoField(primary_key=True)
    owner_type = models.TextField(blank=True, null=True)
    owner_id = models.IntegerField()
    f_name = models.CharField(max_length=255)
    f_path = models.CharField(max_length=255)
    f_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'documents'


class Logs(models.Model):
    log_id = models.AutoField(primary_key=True)
    actor = models.ForeignKey(Admins, on_delete=models.DO_NOTHING)
    actor_type = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=100)
    target_type = models.TextField()
    event = models.ForeignKey(Events, on_delete=models.DO_NOTHING, blank=True, null=True)
    solidarity = models.ForeignKey(Solidarities, on_delete=models.DO_NOTHING, blank=True, null=True)
    family = models.ForeignKey(Families, on_delete=models.DO_NOTHING, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    logged_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'logs'


class Prtcps(models.Model):
    event = models.ForeignKey(Events, on_delete=models.DO_NOTHING)
    student = models.ForeignKey(Students, on_delete=models.DO_NOTHING)
    rank = models.IntegerField(blank=True, null=True)
    reward = models.CharField(max_length=255, blank=True, null=True)
    status = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'prtcps'
        unique_together = (('event', 'student'),)
