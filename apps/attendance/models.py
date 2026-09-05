"""
Attendance App Models
"""
from django.db import models
import uuid


class Shift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='shifts')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.IntegerField(default=60)
    overtime_threshold_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    grace_period_minutes = models.IntegerField(default=15)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'shifts'

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"


class EmployeeShift(models.Model):
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='shifts')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = 'employee_shifts'


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        HALF_DAY = 'half_day', 'Half Day'
        LEAVE = 'leave', 'On Leave'
        HOLIDAY = 'holiday', 'Public Holiday'
        WEEKEND = 'weekend', 'Weekend'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    minutes_late = models.IntegerField(default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    is_manual = models.BooleanField(default=False)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'attendance_records'
        unique_together = [['employee', 'date']]
        indexes = [models.Index(fields=['employee', 'date'])]

    def __str__(self):
        return f"{self.employee} - {self.date}: {self.status}"


class PublicHoliday(models.Model):
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    date = models.DateField()
    country = models.CharField(max_length=2, default='GH')
    is_national = models.BooleanField(default=True)

    class Meta:
        db_table = 'public_holidays'
        unique_together = [['date', 'company']]
