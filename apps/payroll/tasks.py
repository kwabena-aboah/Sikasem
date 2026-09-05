"""apps/payroll/tasks.py - Celery async tasks"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_payroll_period_task(self, period_id: str):
    """Async task: run full payroll calculation for a period"""
    try:
        from .calculator import run_payroll_period
        result = run_payroll_period(period_id)
        logger.info(f"Payroll processed: {result}")
        return result
    except Exception as exc:
        logger.error(f"Payroll processing failed for {period_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def generate_payslip_pdf_task(payslip_id: str):
    """Generate and store PDF for a payslip"""
    from .models import Payslip
    from .pdf_generator import generate_payslip_pdf
    from django.core.files.base import ContentFile
    import os

    payslip = Payslip.objects.select_related('employee', 'payroll_period').get(id=payslip_id)
    pdf_bytes = generate_payslip_pdf(payslip)
    filename = f"payslip_{payslip.employee.employee_id}_{payslip.payroll_period.name.replace(' ', '_')}.pdf"
    payslip.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
    logger.info(f"PDF generated for payslip {payslip_id}")
    return {'payslip_id': payslip_id, 'filename': filename}


@shared_task
def generate_all_payslip_pdfs(period_id: str):
    """Bulk generate PDFs for all payslips in a period"""
    from .models import Payslip
    payslips = Payslip.objects.filter(payroll_period_id=period_id).values_list('id', flat=True)
    for payslip_id in payslips:
        generate_payslip_pdf_task.delay(str(payslip_id))
    return {'queued': len(payslips)}


@shared_task
def disburse_payroll_task(period_id: str, initiated_by_id: str):
    """Create Paystack recipients and initiate one bulk Ghana bank transfer."""
    from decimal import Decimal
    import requests
    from django.conf import settings
    from django.utils import timezone
    from .models import PayrollPeriod, Payslip, PaymentBatch, PaymentRecord

    period = PayrollPeriod.objects.get(id=period_id)
    if not settings.PAYSTACK_SECRET_KEY:
        raise RuntimeError('PAYSTACK_SECRET_KEY is not configured.')

    existing = PaymentBatch.objects.filter(
        payroll_period=period, status__in=['processing', 'completed']
    ).order_by('-initiated_at').first()
    if existing:
        return {'batch_id': str(existing.id), 'message': 'A disbursement already exists for this payroll period.'}

    payslips = list(Payslip.objects.filter(
        payroll_period=period, status='approved'
    ).select_related('employee'))
    if not payslips:
        raise RuntimeError('No approved payslips are available for disbursement.')

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    base_url = getattr(settings, 'PAYSTACK_BASE_URL', 'https://api.paystack.co').rstrip('/')

    def paystack_post(path, payload):
        response = requests.post(f'{base_url}{path}', json=payload, headers=headers, timeout=30)
        try:
            data = response.json()
        except ValueError:
            data = {'message': response.text or 'Paystack returned an invalid response.'}
        if not response.ok or not data.get('status'):
            raise RuntimeError(data.get('message', f'Paystack request failed ({response.status_code}).'))
        return data.get('data')

    batch = PaymentBatch.objects.create(
        payroll_period=period,
        total_amount=sum((p.net_pay for p in payslips), Decimal('0')),
        initiated_by_id=initiated_by_id,
        status='processing',
    )
    transfers = []
    records = {}

    for payslip in payslips:
        employee = payslip.employee
        reference = f'pay_{payslip.id}'[:50]
        record = PaymentRecord.objects.create(
            batch=batch, payslip=payslip, employee=employee,
            amount=payslip.net_pay,
            payment_method=employee.payment_method,
            account_number=employee.account_number or employee.mobile_money_number,
            bank_name=employee.bank_name,
            transfer_reference=reference,
        )

        try:
            if employee.payment_method != 'bank':
                raise RuntimeError('Only bank transfers are supported by the bulk bank-transfer integration.')
            if not employee.account_number or not employee.bank_code:
                raise RuntimeError('Bank account number and Paystack bank code are required.')

            recipient_code = employee.paystack_recipient_code
            if not recipient_code:
                recipient = paystack_post('/transferrecipient', {
                    'type': 'ghipss',
                    'name': employee.account_name or employee.get_full_name(),
                    'account_number': employee.account_number,
                    'bank_code': employee.bank_code,
                    'currency': 'GHS',
                })
                recipient_code = recipient.get('recipient_code')
                if not recipient_code:
                    raise RuntimeError('Paystack did not return a recipient code.')
                employee.paystack_recipient_code = recipient_code
                employee.save(update_fields=['paystack_recipient_code', 'updated_at'])

            record.recipient_code = recipient_code
            transfers.append({
                'amount': int(Decimal(payslip.net_pay) * 100),
                'reference': reference,
                'recipient': recipient_code,
                'reason': f'Salary - {period.name}',
            })
            records[reference] = record
            record.save(update_fields=['transfer_reference', 'recipient_code'])
        except Exception as exc:
            record.status = PaymentRecord.Status.FAILED
            record.failure_reason = str(exc)
            record.save(update_fields=['transfer_reference', 'status', 'failure_reason'])

    if transfers:
        result = paystack_post('/transfer/bulk', {
            'currency': 'GHS',
            'source': 'balance',
            'transfers': transfers,
        })
        for item in result or []:
            record = records.get(item.get('reference'))
            if not record:
                continue
            transfer_status = item.get('status', 'pending').lower()
            record.provider_reference = item.get('transfer_code', '')
            record.status = PaymentRecord.Status.SUCCESS if transfer_status == 'success' else PaymentRecord.Status.SENT
            record.save(update_fields=['provider_reference', 'status'])

    failed = batch.payments.filter(status=PaymentRecord.Status.FAILED).count()
    sent_or_success = batch.payments.filter(status__in=[PaymentRecord.Status.SENT, PaymentRecord.Status.SUCCESS]).count()
    batch.status = 'completed' if sent_or_success == len(payslips) and all(r.status == PaymentRecord.Status.SUCCESS for r in batch.payments.all()) else ('partial' if failed else 'processing')
    if batch.status == 'completed':
        batch.completed_at = timezone.now()
        period.status = PayrollPeriod.Status.PAID
        period.paid_at = timezone.now()
        period.save(update_fields=['status', 'paid_at', 'updated_at'])
    batch.save(update_fields=['status', 'completed_at'])
    return {'batch_id': str(batch.id), 'success': batch.payments.filter(status=PaymentRecord.Status.SUCCESS).count(), 'queued': batch.payments.filter(status=PaymentRecord.Status.SENT).count(), 'failed': failed}


@shared_task
def run_ai_anomaly_detection(period_id: str = None):
    """Scheduled AI anomaly detection"""
    from .models import PayrollPeriod
    from .ai import PayrollAnomalyDetector

    if period_id:
        periods = PayrollPeriod.objects.filter(id=period_id)
    else:
        from django.utils import timezone
        today = timezone.now().date()
        periods = PayrollPeriod.objects.filter(
            status='review',
            period_start__month=today.month,
            period_start__year=today.year,
        )

    for period in periods:
        detector = PayrollAnomalyDetector(period)
        anomalies = detector.detect()
        if anomalies:
            period.ai_anomalies_detected = anomalies
            period.save(update_fields=['ai_anomalies_detected'])
            logger.info(f"Detected {len(anomalies)} anomalies in period {period.name}")


@shared_task
def auto_process_monthly_payroll():
    """Auto-trigger payroll on configured payroll day"""
    from apps.companies.models import Company
    from .models import PayrollPeriod
    from django.utils import timezone
    import calendar

    today = timezone.now().date()
    companies = Company.objects.filter(
        status='active'
    ).prefetch_related('settings')

    for company in companies:
        # Check if payroll day
        if not hasattr(company, 'settings') or today.day != company.payroll_day:
            continue

        # Check if period already exists
        period_start = today.replace(day=1)
        _, last_day = calendar.monthrange(today.year, today.month)
        period_end = today.replace(day=last_day)

        period, created = PayrollPeriod.objects.get_or_create(
            company=company, period_start=period_start, period_end=period_end,
            defaults={
                'name': today.strftime('%B %Y'),
                'pay_date': today,
                'status': 'draft',
            }
        )

        if created:
            process_payroll_period_task.delay(str(period.id))
            logger.info(f"Auto-started payroll for {company.name}: {period.name}")
