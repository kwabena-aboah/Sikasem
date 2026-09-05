"""
Accounts App Models
Custom user model with RBAC
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        COMPANY_ADMIN = 'company_admin', 'Company Admin'
        HR_MANAGER = 'hr_manager', 'HR Manager'
        PAYROLL_OFFICER = 'payroll_officer', 'Payroll Officer'
        FINANCE_MANAGER = 'finance_manager', 'Finance Manager'
        BRANCH_MANAGER = 'branch_manager', 'Branch Manager'
        EMPLOYEE = 'employee', 'Employee'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.EMPLOYEE)
    company = models.ForeignKey(
        'companies.Company', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )
    branch = models.ForeignKey(
        'companies.Branch', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    must_change_password = models.BooleanField(default=True)
    two_factor_enabled = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        db_table = 'auth_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def has_company_access(self, company_id):
        if self.role == self.Role.SUPER_ADMIN:
            return True
        return str(self.company_id) == str(company_id)

    def can_approve_payroll(self):
        return self.role in [
            self.Role.SUPER_ADMIN, self.Role.COMPANY_ADMIN,
            self.Role.HR_MANAGER, self.Role.FINANCE_MANAGER
        ]


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        VIEW = 'view', 'View'
        EXPORT = 'export', 'Export'
        PAYROLL_RUN = 'payroll_run', 'Payroll Run'
        PAYROLL_APPROVE = 'payroll_approve', 'Payroll Approve'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=Action.choices)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    company = models.ForeignKey(
        'companies.Company', on_delete=models.SET_NULL, null=True, related_name='audit_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.resource_type} at {self.timestamp}"


class Permission(models.Model):
    """Granular permissions beyond role-based access"""
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50)

    class Meta:
        db_table = 'custom_permissions'

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """Map roles to granular permissions"""
    role = models.CharField(max_length=30, choices=User.Role.choices)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    company = models.ForeignKey(
        'companies.Company', on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        db_table = 'role_permissions'
        unique_together = [['role', 'permission', 'company']]


class UserPermission(models.Model):
    """Override permissions at user level"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted = models.BooleanField(default=True)  # False = explicitly denied

    class Meta:
        db_table = 'user_permissions_custom'
        unique_together = [['user', 'permission']]
