"""
Loans App Models
Loan and salary advance management
"""
from django.db import models
from decimal import Decimal
import uuid


class LoanType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='loan_types')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_months = models.IntegerField(default=12)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    interest_type = models.CharField(
        max_length=20,
        choices=[('flat', 'Flat Rate'), ('reducing', 'Reducing Balance'), ('none', 'Interest-Free')],
        default='none'
    )
    requires_guarantor = models.BooleanField(default=False)
    min_service_months = models.IntegerField(default=6, help_text='Minimum months of service to qualify')
    max_active_loans = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'loan_types'

    def __str__(self):
        return self.name


class Loan(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        DISBURSED = 'disbursed', 'Disbursed'
        ACTIVE = 'active', 'Active (Repaying)'
        COMPLETED = 'completed', 'Completed'
        DEFAULTED = 'defaulted', 'Defaulted'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    loan_number = models.CharField(max_length=30, unique=True)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_months = models.IntegerField()
    purpose = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    application_date = models.DateField(auto_now_add=True)
    approved_date = models.DateField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    first_repayment_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    rejection_reason = models.TextField(blank=True)
    guarantor = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='guaranteed_loans')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.loan_number} - {self.employee} (GHS {self.principal_amount})"

    def generate_repayment_schedule(self):
        """Generate repayment schedule based on loan terms"""
        from datetime import date
        from dateutil.relativedelta import relativedelta

        schedule = []
        start = self.first_repayment_date or date.today().replace(day=25)
        balance = self.total_amount

        for i in range(self.repayment_months):
            due_date = start + relativedelta(months=i)
            is_last = i == self.repayment_months - 1

            if self.interest_rate > 0 and self.loan_type.interest_type == 'reducing':
                interest = balance * self.interest_rate
                principal = self.monthly_repayment - interest
            else:
                principal = self.monthly_repayment
                interest = Decimal('0')

            if is_last:
                principal = balance  # Clear remaining balance

            balance -= principal

            schedule.append({
                'installment': i + 1,
                'due_date': due_date,
                'principal': float(principal),
                'interest': float(interest),
                'amount': float(principal + interest),
                'balance': max(0, float(balance)),
            })

        return schedule


class LoanRepayment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        DEDUCTED = 'deducted', 'Deducted from Payroll'
        PAID_DIRECTLY = 'paid_directly', 'Paid Directly'
        OVERDUE = 'overdue', 'Overdue'
        WAIVED = 'waived', 'Waived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    principal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    deducted_in = models.ForeignKey('payroll.Payslip', on_delete=models.SET_NULL, null=True, blank=True, related_name='loan_deductions')
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'loan_repayments'
        unique_together = [['loan', 'installment_number']]
        ordering = ['due_date']

    def __str__(self):
        return f"{self.loan.loan_number} - Installment {self.installment_number}"
