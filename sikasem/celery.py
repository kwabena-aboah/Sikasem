"""
Sikasem Celery Configuration
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sikasem.settings.development')

app = Celery('sikasem')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    # Run payroll calculations at start of each month
    'auto-process-payroll': {
        'task': 'apps.payroll.tasks.auto_process_monthly_payroll',
        'schedule': crontab(day_of_month=1, hour=6, minute=0),
    },
    # Daily attendance sync
    'sync-attendance': {
        'task': 'apps.attendance.tasks.sync_attendance_data',
        'schedule': crontab(hour=23, minute=30),
    },
    # Leave balance accrual
    'accrue-leave-balances': {
        'task': 'apps.leaves.tasks.accrue_monthly_leave',
        'schedule': crontab(day_of_month=1, hour=0, minute=30),
    },
    # Loan repayment reminders
    'loan-repayment-reminders': {
        'task': 'apps.loans.tasks.send_repayment_reminders',
        'schedule': crontab(day_of_month=25, hour=9, minute=0),
    },
    # AI anomaly detection on payroll data
    'ai-payroll-anomaly-check': {
        'task': 'apps.payroll.tasks.run_ai_anomaly_detection',
        'schedule': crontab(day_of_month=2, hour=8, minute=0),
    },
    # Compliance reports
    'monthly-compliance-report': {
        'task': 'apps.reports.tasks.generate_compliance_report',
        'schedule': crontab(day_of_month=5, hour=9, minute=0),
    },
}
