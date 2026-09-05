from django.contrib import admin
from .models import Employee, EmployeeDocument, SalaryHistory

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ['employee_id', 'first_name', 'last_name', 'job_title', 'department', 'status', 'company']
    list_filter   = ['status', 'employment_type', 'company', 'department']
    search_fields = ['employee_id', 'first_name', 'last_name', 'work_email', 'ssnit_number', 'tin']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'doc_type', 'name', 'uploaded_at']
    list_filter   = ['doc_type']

@admin.register(SalaryHistory)
class SalaryHistoryAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'basic_salary', 'effective_date', 'reason']
    readonly_fields = ['created_at']
