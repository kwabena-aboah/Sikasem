"""apps/payroll/tasks.py - Celery async tasks"""
from celery import shared_task
import logging
import requests as _requests

logger = logging.getLogger(__name__)

_PAYSTACK_BANKS = None


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
    global _PAYSTACK_BANKS
    """Create Paystack recipients and initiate one bulk Ghana bank transfer."""
    from decimal import Decimal
    import requests
    from django.conf import settings
    from django.utils import timezone
    from .models import PayrollPeriod, Payslip, PaymentBatch, PaymentRecord

    period = PayrollPeriod.objects.get(id=period_id)
    company_settings = getattr(period.company, 'settings', None)
    secret_key = (
        getattr(company_settings, 'paystack_secret_key', '')
        or getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    )
    if not secret_key:
        raise RuntimeError(
            'Paystack is not configured. An administrator must add the Paystack secret key '
            'in System Settings > Payment Settings before salary payments can be made.'
        )

    # Reuse an existing batch on retries. A partial batch may already contain
    # successful transfers, so creating a new batch would reuse the same
    # references and can trigger Paystack/DB duplicate-reference errors.
    candidate_batches = PaymentBatch.objects.filter(
        payroll_period=period,
        status__in=['pending', 'processing', 'partial'],
    )
    # Prefer the batch that already owns payment records. A failed retry may
    # have left behind an empty processing batch after the original partial
    # batch was created.
    batch = candidate_batches.filter(
        payments__isnull=False,
    ).distinct().order_by('-initiated_at').first()
    batch = batch or candidate_batches.order_by('-initiated_at').first()
    completed_batch = PaymentBatch.objects.filter(
        payroll_period=period, status='completed'
    ).order_by('-initiated_at').first()
    if completed_batch:
        return {
            'batch_id': str(completed_batch.id),
            'message': 'A disbursement already completed for this payroll period.',
        }

    payslips = list(Payslip.objects.filter(
        payroll_period=period, status='approved'
    ).select_related('employee'))
    if batch is None:
        batch = PaymentBatch.objects.create(
            payroll_period=period,
            total_amount=sum((p.net_pay for p in payslips), Decimal('0')),
            initiated_by_id=initiated_by_id,
            status='processing',
        )
    else:
        batch.status = PaymentBatch.Status.PROCESSING
        batch.total_amount = sum((p.net_pay for p in payslips), Decimal('0'))
        batch.save(update_fields=['status', 'total_amount'])
    if not payslips:
        raise RuntimeError('No approved payslips are available for disbursement.')

    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json',
    }
    base_url = getattr(
        company_settings, 'paystack_base_url', ''
    ) or getattr(settings, 'PAYSTACK_BASE_URL', 'https://api.paystack.co')
    base_url = base_url.rstrip('/')

    def paystack_post(path, payload):
        response = requests.post(f'{base_url}{path}', json=payload, headers=headers, timeout=30)
        try:
            data = response.json()
        except ValueError:
            data = {'message': response.text or 'Paystack returned an invalid response.'}
        if not response.ok or not data.get('status'):
            raise RuntimeError(data.get('message', f'Paystack request failed ({response.status_code}).'))
        return data.get('data')

    transfers = []
    records = {}

    for payslip in payslips:
        employee = payslip.employee
        reference = f'pay_{payslip.id}'[:50]
        record, _ = PaymentRecord.objects.update_or_create(
            payslip=payslip,
            defaults={
                'batch': batch,
                'employee': employee,
                'amount': payslip.net_pay,
                'payment_method': employee.payment_method,
                'account_number': employee.account_number or employee.mobile_money_number,
                'mobile_number': employee.mobile_money_number,
                'bank_name': employee.bank_name,
                'transfer_reference': reference,
            }
        )

        if record.status == PaymentRecord.Status.SUCCESS:
            continue

        try:
            # Skip non-electronic methods (cash, cheque) – mark as successful offline
            if employee.payment_method not in ['bank', 'mobile_money']:
                record.status = PaymentRecord.Status.SUCCESS
                record.save(update_fields=['transfer_reference', 'status'])
                continue

            if employee.payment_method == 'bank':
                recipient_type = 'ghipss'
                account_number = employee.account_number
                bank_code = employee.bank_code
                if not account_number:
                    raise RuntimeError('Bank account number is required.')

                from apps.employees.constants import resolve_bank_code, GHANA_PAYSTACK_BANKS, PAYSTACK_MOMO_PROVIDERS
                if _PAYSTACK_BANKS is None:
                    try:
                        resp = _requests.get(f'{base_url}/bank', params={'currency': 'GHS', 'perPage': 500}, headers=headers, timeout=30)
                        if resp.ok:
                            _PAYSTACK_BANKS = resp.json().get('data') or []
                        else:
                            _PAYSTACK_BANKS = GHANA_PAYSTACK_BANKS
                    except Exception:
                        _PAYSTACK_BANKS = GHANA_PAYSTACK_BANKS

                if not bank_code:
                    bank_code = resolve_bank_code(employee.bank_name)
                    if not bank_code and _PAYSTACK_BANKS:
                        matched = next(
                            (b for b in _PAYSTACK_BANKS
                             if employee.bank_name.lower() in b.get('name', '').lower()
                             or b.get('name', '').lower() in employee.bank_name.lower()),
                            None
                        )
                        if matched:
                            bank_code = matched.get('code')
                if not bank_code:
                    raise RuntimeError(f"Unable to resolve Paystack bank code for bank '{employee.bank_name}'. Please select a supported bank.")

                if not employee.bank_code or employee.bank_code != bank_code:
                    employee.bank_code = bank_code
                    employee.save(update_fields=['bank_code'])

            elif employee.payment_method == 'mobile_money':
                from apps.employees.constants import PAYSTACK_MOMO_PROVIDERS
                recipient_type = 'mobile_money'
                account_number = employee.mobile_money_number
                provider_clean = (employee.mobile_money_provider or '').lower().strip()
                bank_code = PAYSTACK_MOMO_PROVIDERS.get(provider_clean, provider_clean.upper())
                if not account_number or not bank_code:
                    raise RuntimeError(
                        'Mobile money number and a supported provider (MTN, Telecel/Vodafone, or AirtelTigo) are required.'
                    )

            recipient_code = employee.paystack_recipient_code
            if not recipient_code:
                recipient = paystack_post('/transferrecipient', {
                    'type': recipient_type,
                    'name': employee.account_name or employee.get_full_name(),
                    'account_number': account_number,
                    'bank_code': bank_code,
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
        try:
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
        except Exception as exc:
            logger.error(f'Paystack bulk transfer failed: {exc}')
            err_msg = str(exc)
            for ref, record in records.items():
                if record.status != PaymentRecord.Status.SUCCESS:
                    record.status = PaymentRecord.Status.FAILED
                    record.failure_reason = err_msg
                    record.save(update_fields=['status', 'failure_reason'])
            batch.error_message = err_msg

    failed_records = batch.payments.filter(status=PaymentRecord.Status.FAILED)
    failed = failed_records.count()
    sent_or_success = batch.payments.filter(status__in=[PaymentRecord.Status.SENT, PaymentRecord.Status.SUCCESS]).count()
    if sent_or_success == len(payslips) and all(r.status == PaymentRecord.Status.SUCCESS for r in batch.payments.all()):
        batch.status = PaymentBatch.Status.COMPLETED
    elif sent_or_success:
        batch.status = PaymentBatch.Status.PARTIAL
    else:
        batch.status = PaymentBatch.Status.FAILED
        batch.error_message = '; '.join(
            f'{r.employee.get_full_name()}: {r.failure_reason}'
            for r in failed_records
        )[:5000]
    if batch.status == PaymentBatch.Status.COMPLETED:
        batch.completed_at = timezone.now()
        period.status = PayrollPeriod.Status.PAID
        period.paid_at = timezone.now()
        period.save(update_fields=['status', 'paid_at', 'updated_at'])
    batch.save(update_fields=['status', 'completed_at', 'error_message'])

    # ── Create in-app notifications ─────────────────────────────────────────
    try:
        from apps.notifications.models import Notification
        from apps.accounts.models import User

        # Notify company admins and payroll staff
        admin_users = User.objects.filter(
            company=period.company,
            role__in=['company_admin', 'hr_manager', 'payroll_officer', 'finance_manager'],
            is_active=True,
        )
        success_count = batch.payments.filter(status=PaymentRecord.Status.SUCCESS).count()
        sent_count = batch.payments.filter(status=PaymentRecord.Status.SENT).count()
        failed_count = batch.payments.filter(status=PaymentRecord.Status.FAILED).count()
        total_sent = success_count + sent_count

        if batch.status == PaymentBatch.Status.COMPLETED:
            notif_title = f'Payroll Disbursed: {period.name}'
            notif_msg = f'All {total_sent} salary payments for {period.name} have been sent successfully via Paystack.'
        elif batch.status == PaymentBatch.Status.PARTIAL:
            notif_title = f'Payroll Partially Disbursed: {period.name}'
            notif_msg = f'{total_sent} payments sent, {failed_count} failed for {period.name}. Review payment records for details.'
        else:
            notif_title = f'Payroll Disbursement Failed: {period.name}'
            notif_msg = f'Disbursement failed for {period.name}. {batch.error_message[:200]}'

        notifications_to_create = []
        for user in admin_users:
            notifications_to_create.append(Notification(
                recipient=user,
                notif_type=Notification.NotifType.PAYROLL,
                title=notif_title,
                message=notif_msg,
                link=f'/payroll/periods/{period.id}',
            ))

        # Also notify each employee whose payslip was paid and has an active user account
        paid_payslips = Payslip.objects.filter(
            payroll_period=period,
            status='approved',
            employee__user__isnull=False,
        ).select_related('employee__user')
        for ps in paid_payslips:
            emp_record = batch.payments.filter(employee=ps.employee).first()
            if emp_record and emp_record.status in [PaymentRecord.Status.SUCCESS, PaymentRecord.Status.SENT]:
                notifications_to_create.append(Notification(
                    recipient=ps.employee.user,
                    notif_type=Notification.NotifType.PAYSLIP,
                    title=f'Salary Disbursed: {period.name}',
                    message=f'Your salary for {period.name} (GHS {ps.net_pay:,.2f}) has been sent via {ps.employee.get_payment_method_display() if hasattr(ps.employee, "get_payment_method_display") else ps.employee.payment_method}.',
                    link=f'/payroll/payslips/{ps.id}',
                ))

        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
            logger.info(f'Created {len(notifications_to_create)} notifications for {period.name} disbursement')
    except Exception as notif_exc:
        logger.warning(f'Failed to create disbursement notifications: {notif_exc}')

    return {
        'batch_id': str(batch.id),
        'success': batch.payments.filter(status=PaymentRecord.Status.SUCCESS).count(),
        'queued': batch.payments.filter(status=PaymentRecord.Status.SENT).count(),
        'failed': failed,
        'batch_status': batch.status,
        'error_message': batch.error_message,
    }


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
