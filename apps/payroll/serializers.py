"""
apps/payroll/serializers.py
Fixed:
  - 'company' added to read_only_fields on ALL serializers that set it via perform_create
  - 'created_by' added to read_only_fields on CustomPayrollRule
  - 'status', 'processed_at', 'approved_at', 'approved_by', 'paid_at' read-only on PayrollPeriod
  - remaining models.Q reference removed (moved to views.py top-level Q import)
"""
from rest_framework import serializers
from .models import (
    PayrollPeriod, Payslip, SalaryStructure, SalaryComponent,
    EmployeeSalary, CustomPayrollRule, TaxTable, PaymentBatch
)


class SalaryComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryComponent
        fields = '__all__'
        read_only_fields = [
            'id',
            'company',   # always set from request.user in perform_create
        ]


class SalaryStructureSerializer(serializers.ModelSerializer):
    components_count = serializers.SerializerMethodField()

    class Meta:
        model = SalaryStructure
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at',
            'company',   # always set from request.user in perform_create
        ]

    def get_components_count(self, obj):
        return obj.components.count()


class EmployeeSalarySerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_num = serializers.CharField(source='employee.employee_id',   read_only=True)
    structure_name  = serializers.CharField(source='structure.name',          read_only=True)

    class Meta:
        model = EmployeeSalary
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'approved_at', 'approved_by']


class PayrollPeriodSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    disbursement_completed = serializers.SerializerMethodField()
    effective_status = serializers.SerializerMethodField()
    effective_status_display = serializers.SerializerMethodField()

    class Meta:
        model = PayrollPeriod
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'company',         # always set from request.user in perform_create
            'created_by',      # always set from request.user in perform_create
            'total_gross', 'total_deductions', 'total_net', 'employee_count',
            'total_employer_costs',
            'status',          # changed via dedicated actions (process/approve/disburse)
            'processed_at', 'approved_at', 'approved_by', 'paid_at',
            'ai_anomalies_detected',
        ]

    def validate(self, attrs):
        """Catch duplicate company/date periods before the DB constraint does."""
        request = self.context.get('request')
        company = getattr(getattr(request, 'user', None), 'company', None)
        period_start = attrs.get('period_start')
        period_end = attrs.get('period_end')

        if self.instance is None and company and period_start and period_end:
            if PayrollPeriod.objects.filter(
                company=company,
                period_start=period_start,
                period_end=period_end,
            ).exists():
                raise serializers.ValidationError({
                    'period_start': 'A payroll period already exists for these dates.',
                    'period_end': 'Use the existing period or choose different dates.',
                })

        return attrs

    def get_disbursement_completed(self, obj):
        return obj.payment_batches.filter(status='completed').exists()

    def get_effective_status(self, obj):
        return 'paid' if self.get_disbursement_completed(obj) else obj.status

    def get_effective_status_display(self, obj):
        return 'Paid' if self.get_disbursement_completed(obj) else obj.get_status_display()


class PayslipSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_num = serializers.CharField(source='employee.employee_id',   read_only=True)
    department      = serializers.SerializerMethodField()
    period_name     = serializers.CharField(source='payroll_period.name',    read_only=True)

    class Meta:
        model = Payslip
        fields = '__all__'
        read_only_fields = ['id', 'generated_at']

    def get_department(self, obj):
        try:
            return obj.employee.department.name if obj.employee.department else ''
        except Exception:
            return ''


class PayslipDetailSerializer(PayslipSerializer):
    """Detailed payslip including company and employee info for PDF generation."""
    company_name    = serializers.CharField(source='payroll_period.company.name',    read_only=True)
    company_address = serializers.CharField(source='payroll_period.company.address', read_only=True)
    company_tin     = serializers.CharField(source='payroll_period.company.tin',     read_only=True)
    employee_tin    = serializers.CharField(source='employee.tin',                    read_only=True)
    employee_ssnit  = serializers.CharField(source='employee.ssnit_number',           read_only=True)
    job_title       = serializers.CharField(source='employee.job_title',              read_only=True)
    bank_name       = serializers.CharField(source='employee.bank_name',              read_only=True)
    account_number  = serializers.CharField(source='employee.account_number',         read_only=True)
    period_start    = serializers.DateField(source='payroll_period.period_start',     read_only=True)
    period_end      = serializers.DateField(source='payroll_period.period_end',       read_only=True)
    pay_date        = serializers.DateField(source='payroll_period.pay_date',         read_only=True)


class CustomPayrollRuleSerializer(serializers.ModelSerializer):
    component_name = serializers.CharField(source='component.name', read_only=True)

    class Meta:
        model = CustomPayrollRule
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at',
            'company',     # always set from request.user in perform_create
            'created_by',  # always set from request.user in perform_create
        ]


class TaxTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxTable
        fields = '__all__'
        read_only_fields = ['id']
