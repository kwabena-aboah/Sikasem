"""apps/reports/tasks.py - Celery periodic tasks for reports"""
from celery import shared_task
import logging
from django.utils import timezone
from django.db.models import Sum, Count
from apps.companies.models import Company
from apps.payroll.models import PayrollPeriod, Payslip

logger = logging.getLogger(__name__)


@shared_task
def generate_compliance_report():
    """
    Monthly task: compile PAYE and SSNIT compliance metrics for active companies.
    """
    today = timezone.now().date()
    companies = Company.objects.filter(status='active')
    results = []

    for company in companies:
        periods = PayrollPeriod.objects.filter(
            company=company,
            period_start__year=today.year,
            period_start__month=today.month,
            status__in=['approved', 'paid']
        )
        total_paye = 0.0
        total_ssnit = 0.0

        for period in periods:
            totals = Payslip.objects.filter(payroll_period=period).aggregate(
                paye=Sum('paye_tax'),
                ssnit_emp=Sum('ssnit_employee'),
                ssnit_empr=Sum('ssnit_employer'),
            )
            total_paye += float(totals['paye'] or 0)
            total_ssnit += float((totals['ssnit_emp'] or 0) + (totals['ssnit_empr'] or 0))

        logger.info(
            f"Monthly compliance summary for {company.name}: "
            f"PAYE GHS {total_paye:.2f}, SSNIT GHS {total_ssnit:.2f}"
        )
        results.append({
            'company_id': str(company.id),
            'company_name': company.name,
            'paye': total_paye,
            'ssnit': total_ssnit,
        })

    return {'processed_companies': len(results), 'data': results}
