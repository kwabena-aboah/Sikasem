"""apps/loans/tasks.py - Celery periodic tasks for loans"""
from celery import shared_task
import logging
from django.utils import timezone
from .models import Loan, LoanRepayment

logger = logging.getLogger(__name__)


@shared_task
def send_repayment_reminders():
    """
    Monthly task: find upcoming repayment installments due in the current month
    and prepare repayment deduction reminders for active loans.
    """
    today = timezone.now().date()
    repayments = LoanRepayment.objects.filter(
        status='pending',
        due_date__year=today.year,
        due_date__month=today.month,
        loan__status='active',
    ).select_related('loan__employee')

    reminded_count = repayments.count()
    for rep in repayments:
        logger.info(
            f"Loan repayment reminder: {rep.loan.loan_number} installment #{rep.installment_number} "
            f"amount GHS {rep.amount} for {rep.loan.employee.get_full_name()}"
        )

    logger.info(f"Loan repayment reminders processed for {reminded_count} installments.")
    return {'reminded_count': reminded_count}
