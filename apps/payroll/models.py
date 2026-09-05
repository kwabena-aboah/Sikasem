"""
Payroll App Models
Core payroll engine: structures, runs, payslips, tax tables, rules engine
"""
from django.db import models
from django.conf import settings
import uuid
from decimal import Decimal


class SalaryComponent(models.Model):
    """Defines individual pay components (basic, housing, transport, etc.)"""
    class ComponentType(models.TextChoices):
        EARNING = 'earning', 'Earning'
        DEDUCTION = 'deduction', 'Deduction'
        EMPLOYER_CONTRIBUTION = 'employer_contribution', 'Employer Contribution'

    class CalculationMethod(models.TextChoices):
        FIXED = 'fixed', 'Fixed Amount'
        PERCENTAGE_BASIC = 'pct_basic', 'Percentage of Basic'
        PERCENTAGE_GROSS = 'pct_gross', 'Percentage of Gross'
        FORMULA = 'formula', 'Custom Formula'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='salary_components')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30)
    component_type = models.CharField(max_length=30, choices=ComponentType.choices)
    calculation_method = models.CharField(max_length=20, choices=CalculationMethod.choices, default=CalculationMethod.FIXED)
    default_value = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    is_taxable = models.BooleanField(default=True)
    is_pensionable = models.BooleanField(default=True, help_text='Include in SSNIT calculation base')
    is_statutory = models.BooleanField(default=False, help_text='Statutory component (SSNIT, PAYE, etc.)')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    display_on_payslip = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'salary_components'
        unique_together = [['company', 'code']]
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class SalaryStructure(models.Model):
    """A template defining which components an employee gets"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='salary_structures')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    components = models.ManyToManyField(SalaryComponent, through='SalaryStructureComponent')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'salary_structures'
        unique_together = [['company', 'code']]

    def __str__(self):
        return self.name


class SalaryStructureComponent(models.Model):
    """Component values within a structure"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE, related_name='structure_components')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    calculation_method = models.CharField(max_length=20, blank=True)
    formula = models.TextField(blank=True, help_text='Python-safe formula expression')

    class Meta:
        db_table = 'salary_structure_components'
        unique_together = [['structure', 'component']]


class EmployeeSalary(models.Model):
    """Employee's assigned salary structure and basic pay"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='salary_assignments')
    structure = models.ForeignKey(SalaryStructure, on_delete=models.CASCADE)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='GHS')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employee_salaries'
        indexes = [models.Index(fields=['employee', 'is_current'])]

    def __str__(self):
        return f"{self.employee} - GHS {self.basic_salary}"


class EmployeeSalaryComponent(models.Model):
    """Override component values for individual employees"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_salary = models.ForeignKey(EmployeeSalary, on_delete=models.CASCADE, related_name='component_overrides')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    override_method = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'employee_salary_components'
        unique_together = [['employee_salary', 'component']]


class PayrollPeriod(models.Model):
    """A payroll run period (e.g., January 2024)"""
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PROCESSING = 'processing', 'Processing'
        REVIEW = 'review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='payroll_periods')
    name = models.CharField(max_length=100)
    period_start = models.DateField()
    period_end = models.DateField()
    pay_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    processed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')
    paid_at = models.DateTimeField(null=True, blank=True)
    total_gross = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_employer_costs = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    employee_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    ai_anomalies_detected = models.JSONField(default=list)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_payrolls')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payroll_periods'
        unique_together = [['company', 'period_start', 'period_end']]
        ordering = ['-period_start']

    def __str__(self):
        return f"{self.company.name} - {self.name}" if self.company_id else str(self.id)


class Payslip(models.Model):
    """Individual employee payslip for a period"""
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        GENERATED = 'generated', 'Generated'
        APPROVED = 'approved', 'Approved'
        PAID = 'paid', 'Paid'
        DISPUTED = 'disputed', 'Disputed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='payslips')

    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Statutory deductions
    paye_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ssnit_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tier2_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tier3_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Employer contributions (not deducted from employee)
    ssnit_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tier2_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Other deductions
    loan_repayment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_recovery = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_penalty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Net pay
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Attendance
    working_days = models.IntegerField(default=0)
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Line items (JSON breakdown)
    earnings_breakdown = models.JSONField(default=list)
    deductions_breakdown = models.JSONField(default=list)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    pdf_file = models.FileField(upload_to='payslips/', null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    dispute_reason = models.TextField(blank=True)
    is_anomaly = models.BooleanField(default=False)
    anomaly_notes = models.TextField(blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payslips'
        unique_together = [['payroll_period', 'employee']]
        indexes = [models.Index(fields=['employee', 'status'])]

    def __str__(self):
        return f"Payslip: {self.employee} - {self.payroll_period.name}"

    def calculate_totals(self):
        """Recalculate derived totals"""
        self.total_deductions = (
            self.paye_tax + self.ssnit_employee + self.tier2_employee +
            self.tier3_employee + self.loan_repayment + self.advance_recovery +
            self.late_penalty + self.other_deductions
        )
        self.gross_pay = self.basic_salary + self.total_allowances + self.overtime_pay + self.bonus
        self.net_pay = self.gross_pay - self.total_deductions


class PayslipComponent(models.Model):
    """Detailed line items on a payslip"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='line_items')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'payslip_components'


class TaxTable(models.Model):
    """Ghana PAYE tax bands - updatable"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    effective_year = models.IntegerField()
    band_name = models.CharField(max_length=50)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)  # null = unlimited
    rate = models.DecimalField(max_digits=5, decimal_places=4)
    cumulative_tax_below = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_monthly = models.BooleanField(default=True)
    country = models.CharField(max_length=2, default='GH')

    class Meta:
        db_table = 'tax_tables'
        ordering = ['effective_year', 'min_amount']

    def __str__(self):
        return f"{self.effective_year} Band: {self.min_amount} - {self.max_amount or '∞'} @ {self.rate*100}%"


class CustomPayrollRule(models.Model):
    """Custom rules engine for conditional payroll logic"""
    class TriggerType(models.TextChoices):
        ALWAYS = 'always', 'Always Apply'
        IF_DEPARTMENT = 'dept', 'If Department'
        IF_JOB_GRADE = 'grade', 'If Job Grade'
        IF_EMPLOYMENT_TYPE = 'emp_type', 'If Employment Type'
        IF_TAX_TREATMENT = 'tax', 'If Tax Treatment'
        IF_YEARS_SERVICE = 'tenure', 'If Years of Service'
        IF_SALARY_RANGE = 'salary', 'If Salary Range'
        FORMULA = 'formula', 'Custom Formula'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='payroll_rules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices)
    trigger_condition = models.JSONField(default=dict, help_text='Trigger parameters (dept_id, grade_id, etc.)')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE)
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('add', 'Add Amount'),
            ('set', 'Set Amount'),
            ('multiply', 'Multiply By'),
            ('formula', 'Apply Formula'),
        ]
    )
    action_value = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    action_formula = models.TextField(blank=True)
    priority = models.IntegerField(default=0, help_text='Higher = applied later (can override)')
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'custom_payroll_rules'
        ordering = ['priority', 'name']

    def __str__(self):
        return self.name


class PaymentBatch(models.Model):
    """Payment disbursement batch"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        PARTIAL = 'partial', 'Partial'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='payment_batches')
    provider = models.CharField(max_length=30, default='paystack')
    batch_reference = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    initiated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    response_data = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'payment_batches'


class PaymentRecord(models.Model):
    """Individual payment for each employee"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        REVERSED = 'reversed', 'Reversed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(PaymentBatch, on_delete=models.CASCADE, related_name='payments')
    payslip = models.OneToOneField(Payslip, on_delete=models.CASCADE, related_name='payment')
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20)
    account_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    provider_reference = models.CharField(max_length=100, blank=True)
    transfer_reference = models.CharField(max_length=50, blank=True, null=True, unique=True)
    recipient_code = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'payment_records'
