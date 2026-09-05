from django.contrib import admin
from .models import (
    SalaryComponent, SalaryStructure, SalaryStructureComponent,
    EmployeeSalary, PayrollPeriod, Payslip, TaxTable,
    CustomPayrollRule, PaymentBatch, PaymentRecord
)

@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'component_type', 'calculation_method', 'is_taxable', 'company']
    list_filter  = ['component_type', 'company', 'is_taxable']

@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'company', 'is_default', 'is_active']
    list_filter  = ['company']

@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'basic_salary', 'structure', 'effective_from', 'is_current']
    list_filter  = ['is_current', 'structure__company']

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'period_start', 'period_end', 'status', 'total_net', 'employee_count']
    list_filter  = ['status', 'company']
    readonly_fields = ['total_gross', 'total_deductions', 'total_net', 'employee_count']

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'gross_pay', 'net_pay', 'status', 'is_anomaly']
    list_filter  = ['status', 'is_anomaly', 'payroll_period__company']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']

@admin.register(TaxTable)
class TaxTableAdmin(admin.ModelAdmin):
    list_display = ['effective_year', 'band_name', 'min_amount', 'max_amount', 'rate', 'country']
    list_filter  = ['effective_year', 'country']

@admin.register(CustomPayrollRule)
class CustomPayrollRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_type', 'component', 'action_type', 'priority', 'is_active']
    list_filter  = ['is_active', 'trigger_type', 'company']

admin.site.register(PaymentBatch)
admin.site.register(PaymentRecord)
admin.site.register(SalaryStructureComponent)
