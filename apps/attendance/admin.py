from django.contrib import admin
from .models import Shift, AttendanceRecord, PublicHoliday

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'start_time', 'end_time', 'grace_period_minutes']
    list_filter  = ['company']

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'date', 'status', 'clock_in', 'clock_out', 'overtime_hours', 'minutes_late']
    list_filter   = ['status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']

@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'country', 'is_national']
    list_filter  = ['country', 'is_national']
