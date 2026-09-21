"""
Payroll API Views
"""
import hmac
import hashlib
import json

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.db import IntegrityError, transaction
from kombu.exceptions import OperationalError as BrokerOperationalError
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import PayrollPeriod, Payslip, SalaryStructure, SalaryComponent, EmployeeSalary, CustomPayrollRule, PaymentBatch, PaymentRecord
from .serializers import (
    PayrollPeriodSerializer, PayslipSerializer, PayslipDetailSerializer,
    SalaryStructureSerializer, SalaryComponentSerializer,
    EmployeeSalarySerializer, CustomPayrollRuleSerializer
)
from .calculator import run_payroll_period
from .ai import PayrollAnomalyDetector
from .tasks import generate_payslip_pdf_task, generate_all_payslip_pdfs
from apps.accounts.permissions import IsPayrollOfficer, IsHRManager


def _require_company(user):
    """Raise ValidationError if user has no linked company."""
    from rest_framework.exceptions import ValidationError
    if not user.company_id:
        raise ValidationError(
            'Your account is not linked to a company. '
            'Please contact your system administrator.'
        )
    return user.company



class SalaryComponentViewSet(viewsets.ModelViewSet):
    serializer_class = SalaryComponentSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        return SalaryComponent.objects.filter(
            company=self.request.user.company
        )

    def perform_create(self, serializer):
        company = _require_company(self.request.user)
        serializer.save(company=company)


class SalaryStructureViewSet(viewsets.ModelViewSet):
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        return SalaryStructure.objects.filter(
            company=self.request.user.company
        ).prefetch_related('components')

    def perform_create(self, serializer):
        company = _require_company(self.request.user)
        serializer.save(company=company)


class EmployeeSalaryViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSalarySerializer
    permission_classes = [permissions.IsAuthenticated, IsPayrollOfficer]

    def get_queryset(self):
        qs = EmployeeSalary.objects.filter(
            employee__company=self.request.user.company
        ).select_related('employee', 'structure')

        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        return qs


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPeriodSerializer
    permission_classes = [permissions.IsAuthenticated, IsPayrollOfficer]

    def get_queryset(self):
        return PayrollPeriod.objects.filter(
            company=self.request.user.company
        ).order_by('-period_start')

    def perform_create(self, serializer):
        company = _require_company(self.request.user)
        try:
            serializer.save(
                company=company,
                created_by=self.request.user
            )
        except IntegrityError as exc:
            # Protect against a race where another request creates the same
            # period after serializer validation but before this insert.
            if 'payroll_periods' in str(exc) and 'company_id' in str(exc):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'period_start': 'A payroll period already exists for these dates.',
                    'period_end': 'Use the existing period or choose different dates.',
                }) from exc
            raise

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process payroll immediately without Celery
        """

        period = self.get_object()

        if period.status != PayrollPeriod.Status.DRAFT:
            return Response(
                {'error': 'Only draft payrolls can be processed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # The calculator selects employees belonging to this period's company.
            # It also returns the selected and skipped employees for auditability.
            result = run_payroll_period(str(period.id))

            return Response({
                'message': 'Payroll processed successfully',
                'period_id': str(period.id),
                'result': result
            })

        except Exception as e:
            return Response(
                {
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """Clear a failed, unapproved run so it can be processed again."""
        period = self.get_object()

        if period.status not in (
            PayrollPeriod.Status.PROCESSING,
            PayrollPeriod.Status.REVIEW,
        ):
            return Response(
                {'error': 'Only processing or under-review payrolls can be reset.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            payslips = period.payslips.all()
            payslip_count = payslips.count()

            # A failed run may already have marked loan installments as
            # deducted. Restore them before removing the payslips so a retry
            # can apply those deductions exactly once.
            from apps.loans.models import LoanRepayment
            LoanRepayment.objects.filter(deducted_in__in=payslips).update(
                status=LoanRepayment.Status.PENDING,
                deducted_in=None,
            )
            payslips.delete()
            period.status = PayrollPeriod.Status.DRAFT
            period.processed_at = None
            period.total_gross = 0
            period.total_deductions = 0
            period.total_net = 0
            period.total_employer_costs = 0
            period.employee_count = 0
            period.ai_anomalies_detected = []
            period.save(update_fields=[
                'status', 'processed_at', 'total_gross', 'total_deductions',
                'total_net', 'total_employer_costs', 'employee_count',
                'ai_anomalies_detected', 'updated_at',
            ])

        return Response({
            'message': 'Payroll reset successfully and ready to process again.',
            'period_id': str(period.id),
            'deleted_payslips': payslip_count,
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a payroll period"""
        period = self.get_object()

        if not request.user.can_approve_payroll():
            return Response(
                {'error': 'You do not have permission to approve payroll'},
                status=status.HTTP_403_FORBIDDEN
            )

        if period.status != PayrollPeriod.Status.REVIEW:
            return Response(
                {'error': 'Only payrolls under review can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Run AI anomaly check before approval
        detector = PayrollAnomalyDetector(period)
        anomalies = detector.detect()
        ai_summary = detector.generate_ai_summary() if anomalies else ''

        period.status = PayrollPeriod.Status.APPROVED
        period.approved_by = request.user
        period.approved_at = timezone.now()
        period.ai_anomalies_detected = anomalies
        period.save()

        return Response({
            'message': 'Payroll approved',
            'anomalies_found': len(anomalies),
            'ai_summary': ai_summary,
            'period': PayrollPeriodSerializer(period).data
        })

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get payroll period summary statistics"""
        period = self.get_object()
        stats = Payslip.objects.filter(payroll_period=period).aggregate(
            total_gross=Sum('gross_pay'),
            total_net=Sum('net_pay'),
            total_paye=Sum('paye_tax'),
            total_ssnit=Sum('ssnit_employee'),
            total_ssnit_employer=Sum('ssnit_employer'),
            total_loans=Sum('loan_repayment'),
            avg_net=Avg('net_pay'),
            count=Count('id'),
            anomalies=Count('id', filter=Q(is_anomaly=True)),
        )

        return Response({
            'period': PayrollPeriodSerializer(period).data,
            'statistics': stats
        })

    @action(detail=True, methods=['post'])
    def disburse(self, request, pk=None):
        """Initiate payment disbursement via Paystack"""
        period = self.get_object()

        if period.status != PayrollPeriod.Status.APPROVED:
            return Response(
                {'error': 'Only approved payrolls can be disbursed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        approved_payslips = period.payslips.filter(
            status=Payslip.Status.APPROVED,
        )
        if not approved_payslips.exists():
            # Compatibility for periods approved before approval also locked
            # their generated payslips. Do not promote disputed/paid slips.
            approved_payslips = period.payslips.filter(
                status=Payslip.Status.GENERATED,
            )
            if approved_payslips.exists():
                approved_payslips.update(status=Payslip.Status.APPROVED)
            else:
                return Response({
                    'error': 'No approved payslips are available for disbursement. Approve the payroll period first.'
                }, status=status.HTTP_400_BAD_REQUEST)

        from .tasks import disburse_payroll_task
        task_args = [str(period.id), str(request.user.id)]

        # Development uses eager Celery execution so Redis is not required. The
        # explicit branch also handles local servers started with a different
        # settings module, which would otherwise try to contact localhost:6379.
        if settings.DEBUG or getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            result = disburse_payroll_task.apply(args=task_args)
            if result.failed():
                return Response({
                    'error': str(result.result),
                }, status=status.HTTP_400_BAD_REQUEST)
            task_result = result.result or {}
            if task_result.get('batch_status') == 'failed':
                return Response({
                    'error': 'No employee payments were submitted.',
                    'details': task_result.get('error_message', 'Check each employee payment method and account details.'),
                    'result': task_result,
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'message': 'Payment disbursement completed',
                'result': task_result,
            })

        try:
            task = disburse_payroll_task.delay(*task_args)
        except BrokerOperationalError:
            return Response({
                'error': 'Payment disbursement is temporarily unavailable because the Celery broker is offline.',
                'detail': 'Start Redis/Celery or retry after the broker becomes available.',
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            'message': 'Payment disbursement initiated',
            'task_id': task.id,
        })

    @action(detail=True, methods=['get'])
    def anomalies(self, request, pk=None):
        """Get AI-detected anomalies for this period"""
        period = self.get_object()
        # Re-run detection so the review screen never shows stale flags from
        # an earlier payroll calculation.
        detected = PayrollAnomalyDetector(period).detect()

        return Response({
            'count': len(detected),
            'anomalies': detected,
            'can_approve': True,
            'message': (
                'Review the recommended resolutions before approval. '
                'Warnings do not block payment once the payroll is approved.'
            ),
        })

    @action(detail=True, methods=['post'])
    def generate_pdfs(self, request, pk=None):
        """Bulk generate payslip PDFs for this period"""
        period = self.get_object()
        result = generate_all_payslip_pdfs(str(period.id))
        return Response({
            'message': 'Payslip PDF generation queued',
            'period_id': str(period.id),
            'result': result
        })


class PayslipViewSet(viewsets.ModelViewSet):
    serializer_class = PayslipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Payslip.objects.select_related('employee', 'payroll_period')

        # Employees can only see their own payslips
        if user.role == 'employee':
            if hasattr(user, 'employee_profile'):
                qs = qs.filter(employee=user.employee_profile)
            else:
                return Payslip.objects.none()
        elif user.role == 'branch_manager' and user.branch_id:
            qs = qs.filter(employee__branch_id=user.branch_id)
        else:
            qs = qs.filter(payroll_period__company=user.company)

        # Filters
        employee_id = self.request.query_params.get('employee_id')
        period_id = self.request.query_params.get('period_id')
        year = self.request.query_params.get('year')

        if employee_id and user.role != 'employee':
            qs = qs.filter(employee_id=employee_id)
        if period_id:
            qs = qs.filter(payroll_period_id=period_id)
        if year:
            qs = qs.filter(payroll_period__period_start__year=year)

        return qs.order_by('-payroll_period__period_start')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PayslipDetailSerializer
        return PayslipSerializer

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download payslip as PDF"""
        payslip = self.get_object()

        # Check access
        if request.user.role == 'employee':
            if not hasattr(request.user, 'employee_profile') or \
               request.user.employee_profile != payslip.employee:
                return Response(status=status.HTTP_403_FORBIDDEN)

        if payslip.pdf_file:
            response = HttpResponse(payslip.pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.id}.pdf"'
            return response

        # Generate on-demand
        from .pdf_generator import generate_payslip_pdf
        pdf_content = generate_payslip_pdf(payslip)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payslip_{payslip.employee.employee_id}_{payslip.payroll_period.name}.pdf"'
        return response



class CustomPayrollRuleViewSet(viewsets.ModelViewSet):
    serializer_class = CustomPayrollRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        return CustomPayrollRule.objects.filter(
            company=self.request.user.company
        ).select_related('component')

    def perform_create(self, serializer):
        company = _require_company(self.request.user)
        serializer.save(
            company=company,
            created_by=self.request.user
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def paystack_webhook(request):
    """Reconcile Paystack transfer status notifications safely."""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

    event = payload.get('event', '')
    transfer = payload.get('data') or {}
    reference = transfer.get('reference')
    if not reference:
        return Response({'received': True})

    from .models import PaymentRecord
    record = PaymentRecord.objects.filter(
        transfer_reference=reference
    ).select_related('batch__payroll_period__company__settings').first()
    if not record:
        return Response({'received': True})

    company_settings = getattr(record.batch.payroll_period.company, 'settings', None)
    configured_key = (
        getattr(company_settings, 'paystack_secret_key', '')
        or getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    )
    signature = request.headers.get('x-paystack-signature', '')
    expected = hmac.new(
        configured_key.encode(), request.body, hashlib.sha512
    ).hexdigest()
    if not configured_key or not hmac.compare_digest(signature, expected):
        return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)

    status_map = {
        'transfer.success': PaymentRecord.Status.SUCCESS,
        'transfer.failed': PaymentRecord.Status.FAILED,
        'transfer.reversed': PaymentRecord.Status.REVERSED,
    }
    new_status = status_map.get(event)
    if not new_status:
        return Response({'received': True})

    record.status = new_status
    record.provider_reference = transfer.get('transfer_code', record.provider_reference)
    record.failure_reason = transfer.get('failures') or (transfer.get('gateway_response') or '')
    if new_status == PaymentRecord.Status.SUCCESS:
        record.completed_at = timezone.now()
    record.save(update_fields=['status', 'provider_reference', 'failure_reason', 'completed_at'])

    batch = record.batch
    records = batch.payments.all()
    if records.filter(status__in=[PaymentRecord.Status.FAILED, PaymentRecord.Status.REVERSED]).exists():
        batch.status = PaymentBatch.Status.PARTIAL
    elif records.exists() and not records.exclude(status=PaymentRecord.Status.SUCCESS).exists():
        batch.status = PaymentBatch.Status.COMPLETED
        batch.completed_at = timezone.now()
        period = batch.payroll_period
        period.status = period.Status.PAID
        period.paid_at = timezone.now()
        period.save(update_fields=['status', 'paid_at', 'updated_at'])
    else:
        batch.status = PaymentBatch.Status.PROCESSING
    batch.save(update_fields=['status', 'completed_at'])
    return Response({'received': True})
