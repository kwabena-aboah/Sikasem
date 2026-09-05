from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveApplication, Benefit, EmployeeBenefit

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'days_per_year', 'is_paid', 'company']
    list_filter  = ['company', 'is_paid']

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'entitled', 'taken', 'pending']
    list_filter  = ['year', 'leave_type__company']

@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'leave_type', 'start_date', 'end_date', 'days_requested', 'status']
    list_filter   = ['status', 'leave_type']
    search_fields = ['employee__first_name', 'employee__last_name']

admin.site.register(Benefit)
admin.site.register(EmployeeBenefit)
