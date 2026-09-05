"""apps/leaves/tasks.py - Celery periodic tasks for leaves"""
from celery import shared_task
import logging
from django.utils import timezone
from apps.employees.models import Employee
from .models import LeaveType, LeaveBalance

logger = logging.getLogger(__name__)


@shared_task
def accrue_monthly_leave():
    """
    Monthly task: accrue leave balance for active employees.
    Increments employee leave balance by annual entitlement / 12.
    """
    current_year = timezone.now().year
    employees = Employee.objects.filter(status='active').select_related('company')
    leave_types = LeaveType.objects.filter(is_paid=True)
    accrued_count = 0

    for emp in employees:
        for lt in leave_types:
            if lt.gender_specific and lt.gender_specific != emp.gender:
                continue
            
            monthly_increment = round(float(lt.days_per_year) / 12.0, 2)
            balance, created = LeaveBalance.objects.get_or_create(
                employee=emp,
                leave_type=lt,
                year=current_year,
                defaults={
                    'entitled': lt.days_per_year,
                    'accrued': monthly_increment,
                    'taken': 0,
                    'pending': 0,
                }
            )
            if not created:
                balance.accrued = round(float(balance.accrued) + monthly_increment, 2)
                balance.save(update_fields=['accrued', 'updated_at'])
            accrued_count += 1

    logger.info(f"Monthly leave accrual completed for {accrued_count} balances in year {current_year}.")
    return {'year': current_year, 'accrued_count': accrued_count}
