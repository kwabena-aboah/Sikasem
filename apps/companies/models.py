"""
Companies App Models
Multi-company, multi-branch support
"""
from django.db import models
import uuid


class Company(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        TRIAL = 'trial', 'Trial'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    trading_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tin = models.CharField(max_length=50, blank=True, verbose_name='Tax Identification Number')
    ssnit_employer_code = models.CharField(max_length=50, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default='GH')
    currency = models.CharField(max_length=3, default='GHS')
    timezone = models.CharField(max_length=50, default='Africa/Accra')
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    subscription_plan = models.CharField(max_length=50, default='starter')
    max_employees = models.IntegerField(default=50)
    payroll_cycle = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('bi_weekly', 'Bi-Weekly'), ('weekly', 'Weekly')],
        default='monthly'
    )
    payroll_day = models.IntegerField(default=25, help_text='Day of month for payroll processing')
    fiscal_year_start = models.CharField(max_length=5, default='01-01', help_text='MM-DD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_headquarters = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'branches'
        unique_together = [['company', 'code']]
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='departments')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_departments')
    head = models.ForeignKey(
        'employees.Employee', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='headed_departments'
    )
    cost_center = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.company.name} / {self.name}"


class JobGrade(models.Model):
    """Salary bands / job levels"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_grades')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2)
    max_salary = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'job_grades'
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.name} (GHS {self.min_salary} - {self.max_salary})"


class CompanySettings(models.Model):
    """Payroll and HR settings per company"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='settings')
    
    # Tax settings
    enable_paye = models.BooleanField(default=True)
    enable_ssnit = models.BooleanField(default=True)
    enable_tier2 = models.BooleanField(default=True)
    enable_tier3 = models.BooleanField(default=False)
    tier3_employee_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.05)
    tier3_employer_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.00)
    
    # Payroll settings
    overtime_rate_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.5)
    late_penalty_per_minute = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    enable_late_penalty = models.BooleanField(default=False)
    payslip_template = models.CharField(max_length=50, default='standard')
    
    # Leave settings
    annual_leave_days = models.IntegerField(default=15)
    sick_leave_days = models.IntegerField(default=14)
    maternity_leave_days = models.IntegerField(default=84)  # 12 weeks
    paternity_leave_days = models.IntegerField(default=5)
    leave_accrual_method = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('annual', 'Annual')],
        default='monthly'
    )
    
    # Notification preferences
    notify_payslip_ready = models.BooleanField(default=True)
    notify_leave_approved = models.BooleanField(default=True)
    notify_loan_approved = models.BooleanField(default=True)
    notify_payroll_processed = models.BooleanField(default=True)
    
    # Payment
    payment_provider = models.CharField(max_length=30, default='paystack')
    auto_disburse = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'company_settings'
