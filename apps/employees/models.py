"""
Employees App Models
Full employee lifecycle management
"""
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_LEAVE = 'on_leave', 'On Leave'
        SUSPENDED = 'suspended', 'Suspended'
        TERMINATED = 'terminated', 'Terminated'
        PROBATION = 'probation', 'Probation'

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full Time'
        PART_TIME = 'part_time', 'Part Time'
        CONTRACT = 'contract', 'Contract'
        INTERN = 'intern', 'Intern'
        CASUAL = 'casual', 'Casual'

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    class MaritalStatus(models.TextChoices):
        SINGLE = 'single', 'Single'
        MARRIED = 'married', 'Married'
        DIVORCED = 'divorced', 'Divorced'
        WIDOWED = 'widowed', 'Widowed'

    class TaxTreatment(models.TextChoices):
        RESIDENT = 'resident', 'Resident (Standard PAYE)'
        NON_RESIDENT = 'non_resident', 'Non-Resident (Flat Rate)'
        EXPATRIATE = 'expatriate', 'Expatriate'
        CASUAL = 'casual', 'Casual Worker'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='employee_profile'
    )
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='employees')
    branch = models.ForeignKey('companies.Branch', on_delete=models.SET_NULL, null=True, related_name='employees')
    department = models.ForeignKey('companies.Department', on_delete=models.SET_NULL, null=True, related_name='employees')
    job_grade = models.ForeignKey('companies.JobGrade', on_delete=models.SET_NULL, null=True, blank=True)
    reports_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')

    # Identity
    employee_id = models.CharField(max_length=30)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=2, default='GH')
    national_id = models.CharField(max_length=50, blank=True, verbose_name='Ghana Card Number')
    tin = models.CharField(max_length=50, blank=True, verbose_name='TIN')
    ssnit_number = models.CharField(max_length=50, blank=True, verbose_name='SSNIT Number')
    marital_status = models.CharField(max_length=20, choices=MaritalStatus.choices, default=MaritalStatus.SINGLE)

    # Contact
    personal_email = models.EmailField(blank=True)
    work_email = models.EmailField(blank=True)
    personal_phone = PhoneNumberField(blank=True)
    work_phone = PhoneNumberField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = PhoneNumberField(blank=True)
    emergency_contact_relation = models.CharField(max_length=100, blank=True)

    # Employment
    job_title = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROBATION)
    hire_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)
    probation_end_date = models.DateField(null=True, blank=True)

    # Tax
    tax_treatment = models.CharField(max_length=20, choices=TaxTreatment.choices, default=TaxTreatment.RESIDENT)
    tax_relief_count = models.IntegerField(default=1, help_text='Number of personal reliefs (children, disability etc.)')
    is_exempt_ssnit = models.BooleanField(default=False)
    is_exempt_paye = models.BooleanField(default=False)

    # Bank details
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    bank_code = models.CharField(max_length=20, blank=True, help_text='Paystack bank/institution code')
    account_number = models.CharField(max_length=50, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    paystack_recipient_code = models.CharField(max_length=100, blank=True, help_text='Saved Paystack transfer recipient code')
    mobile_money_number = models.CharField(max_length=20, blank=True)
    mobile_money_provider = models.CharField(
        max_length=20,
        choices=[('mtn', 'MTN Mobile Money'), ('vodafone', 'Vodafone Cash'), ('airteltigo', 'AirtelTigo Money')],
        blank=True
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[('bank', 'Bank Transfer'), ('mobile_money', 'Mobile Money'), ('cash', 'Cash'), ('cheque', 'Cheque')],
        default='bank'
    )

    # Profile
    photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)
    bio = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_employees'
    )

    class Meta:
        db_table = 'employees'
        unique_together = [['company', 'employee_id']]
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return ' '.join(p for p in parts if p).strip()

    @property
    def age(self):
        today = timezone.now().date()
        return (today - self.date_of_birth).days // 365

    @property
    def years_of_service(self):
        end = self.termination_date or timezone.now().date()
        return (end - self.hire_date).days / 365.25


class EmployeeDocument(models.Model):
    class DocType(models.TextChoices):
        GHANA_CARD = 'ghana_card', 'Ghana Card'
        PASSPORT = 'passport', 'Passport'
        BIRTH_CERTIFICATE = 'birth_cert', 'Birth Certificate'
        EDUCATIONAL = 'educational', 'Educational Certificate'
        CONTRACT = 'contract', 'Employment Contract'
        OFFER_LETTER = 'offer_letter', 'Offer Letter'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='employee_docs/')
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employee_documents'


class EmployeeQualification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='qualifications')
    institution = models.CharField(max_length=255)
    qualification = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True)
    year_obtained = models.IntegerField()
    grade = models.CharField(max_length=50, blank=True)
    certificate = models.FileField(upload_to='qualifications/', null=True, blank=True)

    class Meta:
        db_table = 'employee_qualifications'


class SalaryHistory(models.Model):
    """Track salary changes over time"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_history')
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'salary_history'
        ordering = ['-effective_date']
