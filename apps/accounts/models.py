from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class AdminsUserManager(BaseUserManager):
    use_in_migrations = False

    def get_by_natural_key(self, email):
        return self.get(email=email)


class AdminsUser(AbstractBaseUser, PermissionsMixin):
    admin_id   = models.AutoField(primary_key=True)
    name       = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)
    password   = models.CharField(max_length=255)
    faculty    = models.ForeignKey('solidarity.Faculties', models.DO_NOTHING,
                                   blank=True, null=True)
    dept       = models.ForeignKey('solidarity.Departments', models.DO_NOTHING,
                                   blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    can_create = models.BooleanField(blank=True, null=True)
    can_update = models.BooleanField(blank=True, null=True)
    can_read   = models.BooleanField(blank=True, null=True)
    can_delete = models.BooleanField(blank=True, null=True)
    acc_status = models.CharField(max_length=20, blank=True, null=True)
    role       = models.TextField(blank=True, null=True)

    @property
    def id(self):
        return self.admin_id

    last_login   = None          # <-- removes field coming from AbstractBaseUser
    is_superuser = None

    #  -------- Django-auth requirements ----------
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []
    objects = AdminsUserManager()

    class Meta:
        managed  = False          # DB-first – do not let Django touch table
        db_table = 'admins'

    def __str__(self):
        return f"{self.name} ({self.email})"

    # password helpers
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # ---- mandatory flags ------------------------
    @property
    def is_active(self):
        return str(self.acc_status).lower() in ('active', 'enabled', '1', 'true', '')

    @property
    def is_staff(self):           # needed to enter Django admin
        return self.role and self.role != 'طالب'

    @property
    def is_authenticated(self):
        return True               # any instance is authenticated

    @property
    def is_anonymous(self):
        return False
    


# Std 
class Students(models.Model):
    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password = models.CharField()
    faculty = models.ForeignKey('solidarity.Faculties', models.DO_NOTHING)
    profile_photo = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=1 , default='M')
    nid = models.TextField(unique=True)
    uid = models.TextField(unique=True)
    phone_number = models.TextField(unique=True , null= True)
    address = models.CharField(max_length=255 ,null= True)
    acd_year = models.CharField(max_length=50)
    join_date = models.DateField(auto_now_add=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    major = models.CharField(max_length=255 , null= True)

    @property
    def id(self):
        return self.student_id

    @property
    def is_authenticated(self):
        """Assumed True if loaded successfully via the JWT token."""
        return True

    @property
    def is_anonymous(self):
        return False
        
    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return False
        
    class Meta:
        managed = False 
        db_table = 'students'