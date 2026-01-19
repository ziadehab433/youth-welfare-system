from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator

from django.contrib.postgres.fields import ArrayField

from .fields import EncryptedTextField
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
    dept_fac_ls = ArrayField(
        base_field=models.CharField(max_length=255),
        blank=True,
        null=True
    )
    nid = models.CharField(
    max_length=14,
    blank=True,
    null=True,
    validators=[
        RegexValidator(
            regex=r'^\d{14}$',
            message='NID must be exactly 14 digits'
        )
    ]
)

    phone_number = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,14}$',
                message='Phone number must be between 1 and 14 digits'
            )
        ]
    )

    
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
    



    def has_create_permission(self, resource=None):
        """Check if admin has create permission"""
        if not self.is_active:
            return False
        return bool(self.can_create)

    def has_read_permission(self, resource=None):
        """Check if admin has read permission"""
        if not self.is_active:
            return False
        return bool(self.can_read)

    def has_update_permission(self, resource=None):
        """Check if admin has update permission"""
        if not self.is_active:
            return False
        return bool(self.can_update)

    def has_delete_permission(self, resource=None):
        """Check if admin has delete permission"""
        if not self.is_active:
            return False
        return bool(self.can_delete)

    def has_permission(self, permission_type, resource=None):
        """
        Generic permission checker
        
        Args:
            permission_type: 'create', 'read', 'update', 'delete'
            resource: optional resource name for future granular permissions
        
        Returns:
            bool: True if admin has permission
        """
        if not self.is_active:
            return False
            
        permission_map = {
            'create': self.can_create,
            'read': self.can_read,
            'update': self.can_update,
            'delete': self.can_delete,
        }
        
        return bool(permission_map.get(permission_type, False))

    def get_permissions(self):
        """Get list of permissions admin has"""
        permissions = []
        if self.can_create:
            permissions.append('create')
        if self.can_read:
            permissions.append('read')
        if self.can_update:
            permissions.append('update')
        if self.can_delete:
            permissions.append('delete')
        return permissions

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
    can_create_fam = models.BooleanField(default=False)

    
    # ============ NEW: Google OAuth Fields ============
    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Google user ID for SSO authentication"
    )
    
    google_picture = models.URLField(
        null=True,
        blank=True,
        help_text="Profile picture URL from Google"
    )
    
    is_google_auth = models.BooleanField(
        default=False,
        help_text="Whether student authenticated via Google OAuth"
    )
    
    auth_method = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email/Password'),
            ('google', 'Google OAuth'),
        ],
        default='email'
    )
    
    last_login_method = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Last authentication method used"
    )
    
    last_google_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last Google OAuth login"
    )
    # ===================================================
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
        
    def __str__(self):
        return f"{self.name} ({self.email})"