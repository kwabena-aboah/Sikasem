from django.contrib import admin
from .models import Company, Branch, Department, JobGrade, CompanySettings

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display  = ['name', 'tin', 'status', 'subscription_plan', 'payroll_day']
    list_filter   = ['status', 'country']
    search_fields = ['name', 'tin', 'email']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display  = ['name', 'company', 'city', 'is_headquarters', 'is_active']
    list_filter   = ['company', 'is_headquarters']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['name', 'company', 'branch', 'is_active']
    list_filter   = ['company', 'branch']
    search_fields = ['name', 'code']

@admin.register(JobGrade)
class JobGradeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'company', 'min_salary', 'max_salary']
    list_filter   = ['company']

admin.site.register(CompanySettings)
