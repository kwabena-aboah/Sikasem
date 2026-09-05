"""
Leaves App Models
Leave types, applications, balances, benefits
"""
from django.db import models
import uuid


class LeaveType(models.Model):
    class AccrualType(models.TextChoices):
        MONTHLY = 'monthly', 'Monthly Accrual'
        ANNUAL = 'annual', 'Annual Grant'
        MANUAL = 'manual', 'Manual Grant Only'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='leave_types')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    days_per_year = models.DecimalField(max_digits=5, decimal_places=1)
    accrual_type = models.CharField(max_length=20, choices=AccrualType.choices, default=AccrualType.MONTHLY)
    is_paid = models.BooleanField(default=True)
    carry_forward = models.BooleanField(default=True)
    max_carry_forward = models.IntegerField(default=5)
    requires_approval = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    min_days = models.IntegerField(default=1)
    max_days_per_request = models.IntegerField(default=14)
    gender_specific = models.CharField(
        max_length=1, blank=True,
        choices=[('M', 'Male Only'), ('F', 'Female Only')],
        help_text='Leave applicable to specific gender only'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'leave_types'
        unique_together = [['company', 'code']]

    def __str__(self):
        return f"{self.name} ({self.days_per_year} days/year)"


class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField()
    entitled = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    taken = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    pending = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    carried_forward = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    adjusted = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_balances'
        unique_together = [['employee', 'leave_type', 'year']]

    @property
    def available(self):
        return self.entitled + self.carried_forward + self.adjusted - self.taken - self.pending


class LeaveApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    days_requested = models.DecimalField(max_digits=5, decimal_places=1)
    reason = models.TextField(blank=True)
    document = models.FileField(upload_to='leave_docs/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    handover_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_applications'
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} ({self.start_date} to {self.end_date})"


class Benefit(models.Model):
    """Non-cash benefits: health insurance, car, housing, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='benefits')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    is_taxable = models.BooleanField(default=False)
    monetary_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'benefits'

    def __str__(self):
        return self.name


class EmployeeBenefit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='benefits')
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    value_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'employee_benefits'
