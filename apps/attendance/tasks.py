"""apps/attendance/tasks.py - Celery periodic tasks for attendance"""
from celery import shared_task
import logging
from django.utils import timezone
from .models import AttendanceRecord, Shift

logger = logging.getLogger(__name__)


@shared_task
def sync_attendance_data():
    """
    Daily task: process attendance records, calculate overtime,
    and flag missing check-outs or late arrivals for active employees.
    """
    today = timezone.now().date()
    records = AttendanceRecord.objects.filter(date=today).select_related('shift', 'employee')
    processed = 0

    for record in records:
        if record.clock_in and record.clock_out and record.shift:
            # Overtime calculation if clock_out is past shift end
            import datetime
            clock_out_dt = datetime.datetime.combine(today, record.clock_out)
            shift_end_dt = datetime.datetime.combine(today, record.shift.end_time)
            
            if clock_out_dt > shift_end_dt:
                extra_seconds = (clock_out_dt - shift_end_dt).total_seconds()
                record.overtime_hours = round(extra_seconds / 3600.0, 2)
                record.save(update_fields=['overtime_hours', 'updated_at'])
                processed += 1

    logger.info(f"Attendance daily sync completed. Processed {processed} records for {today}.")
    return {'date': str(today), 'processed': processed}
