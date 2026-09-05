"""
apps/loans/urls.py
Fixed:
  - LoanSerializer: employee + loan_number in read_only_fields
  - LoanViewSet.perform_create: auto-sets employee from request.user.employee_profile
  - LoanTypeSerializer: company in read_only_fields
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import LoanType, Loan, LoanRepayment
from apps.accounts.permissions import IsHRManager


class LoanTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanType
        fields = '__all__'
        read_only_fields = ['id', 'company']  # company set via perform_create


class LoanSerializer(serializers.ModelSerializer):
    employee_name      = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_num    = serializers.CharField(source='employee.employee_id',   read_only=True)
    loan_type_name     = serializers.CharField(source='loan_type.name',         read_only=True)
    repayment_schedule = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = '__all__'
        read_only_fields = [
            'id',
            'loan_number',        # auto-generated in perform_create
            'employee',           # auto-set from request.user.employee_profile
            'created_at',
            'amount_paid',
            'outstanding_balance',
            'status',             # changed via dedicated actions
            'approved_by',
            'approved_date',
            'disbursement_date',
            'first_repayment_date',
            'rejection_reason',
        ]

    def get_repayment_schedule(self, obj):
        if self.context.get('include_schedule') and obj.status in ['active', 'disbursed']:
            try:
                return obj.generate_repayment_schedule()
            except Exception:
                return []
        return None


class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = '__all__'


class LoanTypeViewSet(viewsets.ModelViewSet):
    serializer_class = LoanTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return LoanType.objects.none()
        return LoanType.objects.filter(company_id=user.company_id).order_by('name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'loan_type']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        # Employees see only their own loans
        if user.role == 'employee' and hasattr(user, 'employee_profile'):
            return Loan.objects.filter(
                employee=user.employee_profile
            ).select_related('employee', 'loan_type').order_by('-created_at')

        if not user.company_id:
            return Loan.objects.none()

        qs = Loan.objects.filter(
            employee__company_id=user.company_id
        ).select_related('employee', 'loan_type').order_by('-created_at')

        # Allow HR to filter by specific employee
        employee_filter = self.request.query_params.get('employee')
        if employee_filter:
            qs = qs.filter(employee_id=employee_filter)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def perform_create(self, serializer):
        import secrets
        user = self.request.user

        # Resolve employee: must come from the logged-in user's profile
        employee = getattr(user, 'employee_profile', None)

        # HR/admins can submit on behalf of an employee (via employee field in payload)
        # but employee FK is read_only so it always comes from request context
        if not employee:
            # For HR staff creating loans for other employees, they should use a different flow
            # For self-service portal: employee must be linked to account
            raise ValidationError(
                'Your account is not linked to an employee profile. '
                'Please contact HR to link your account.'
            )

        loan_number = f"LN-{timezone.now().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"
        loan = serializer.save(
            employee=employee,
            loan_number=loan_number,
            status='pending',
        )
        loan.outstanding_balance = loan.total_amount
        loan.save(update_fields=['outstanding_balance'])

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LoanSerializer(instance, context={'include_schedule': True})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        loan = self.get_object()
        if loan.status != 'pending':
            return Response({'error': 'Only pending loans can be approved'}, status=400)
        loan.status       = Loan.Status.APPROVED
        loan.approved_by  = request.user
        loan.approved_date = timezone.now().date()
        loan.save()
        return Response(LoanSerializer(loan).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        loan = self.get_object()
        if loan.status != 'pending':
            return Response({'error': 'Only pending loans can be rejected'}, status=400)
        loan.status           = Loan.Status.REJECTED
        loan.rejection_reason = request.data.get('reason', '')
        loan.save()
        return Response(LoanSerializer(loan).data)

    @action(detail=True, methods=['post'])
    def disburse(self, request, pk=None):
        loan = self.get_object()
        if loan.status != 'approved':
            return Response({'error': 'Only approved loans can be disbursed'}, status=400)

        today = timezone.now().date()
        if today.month == 12:
            first_rep = today.replace(year=today.year + 1, month=1, day=25)
        else:
            first_rep = today.replace(month=today.month + 1, day=25)

        loan.status               = Loan.Status.ACTIVE
        loan.disbursement_date    = today
        loan.first_repayment_date = first_rep
        loan.save()

        schedule = loan.generate_repayment_schedule()
        LoanRepayment.objects.filter(loan=loan).delete()  # clear any old schedule
        for item in schedule:
            LoanRepayment.objects.create(
                loan=loan,
                installment_number=item['installment'],
                due_date=item['due_date'],
                amount=item['amount'],
                principal=item['principal'],
                interest=item['interest'],
            )
        return Response({'message': 'Loan disbursed', 'schedule_items': len(schedule)})

    @action(detail=True, methods=['get'])
    def repayments(self, request, pk=None):
        loan = self.get_object()
        repayments = LoanRepayment.objects.filter(loan=loan).order_by('installment_number')
        return Response(LoanRepaymentSerializer(repayments, many=True).data)


router = DefaultRouter()
router.register(r'types', LoanTypeViewSet, basename='loan-types')
router.register(r'',      LoanViewSet,     basename='loans')
urlpatterns = [path('', include(router.urls))]
