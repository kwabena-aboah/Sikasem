"""
apps/leaves/urls.py
Fixed:
  - LeaveApplicationSerializer: employee + related read_only fields declared properly
  - LeaveApplicationViewSet.perform_create: auto-sets employee, validates balance
  - LeaveTypeSerializer: company read-only
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import F
from .models import LeaveType, LeaveBalance, LeaveApplication, Benefit
from apps.accounts.permissions import IsHRManager


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ['id', 'company']  # company set via perform_create


class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefit
        fields = '__all__'
        read_only_fields = ['id', 'company']


class BenefitViewSet(viewsets.ModelViewSet):
    serializer_class = BenefitSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        return Benefit.objects.filter(company_id=user.company_id).order_by('name') if user.company_id else Benefit.objects.none()

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    available       = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = '__all__'

    def get_available(self, obj):
        return float(obj.available)


class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_name    = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_num  = serializers.CharField(source='employee.employee_id',   read_only=True)
    leave_type_name  = serializers.CharField(source='leave_type.name',        read_only=True)
    department       = serializers.SerializerMethodField()
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, default='')

    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = [
            'id',
            'employee',          # auto-set from request.user.employee_profile
            'applied_at',
            'updated_at',
            'status',            # changed via approve/reject actions
            'approved_by',
            'approved_at',
            'rejection_reason',
        ]

    def get_department(self, obj):
        try:
            return obj.employee.department.name if obj.employee_id and obj.employee.department else ''
        except Exception:
            return ''


class LeaveTypeViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return LeaveType.objects.none()
        return LeaveType.objects.filter(company_id=user.company_id).order_by('name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'leave_type']
    ordering = ['-applied_at']

    def get_queryset(self):
        user = self.request.user
        # Employees see only their own applications
        if user.role == 'employee' and hasattr(user, 'employee_profile'):
            return LeaveApplication.objects.filter(
                employee=user.employee_profile
            ).select_related('leave_type', 'employee', 'approved_by').order_by('-applied_at')

        if not user.company_id:
            return LeaveApplication.objects.none()

        qs = LeaveApplication.objects.filter(
            employee__company_id=user.company_id
        ).select_related('leave_type', 'employee', 'employee__department', 'approved_by')

        employee_filter = self.request.query_params.get('employee') or self.request.query_params.get('employee_id')
        if employee_filter:
            qs = qs.filter(employee_id=employee_filter)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs.order_by('-applied_at')

    def perform_create(self, serializer):
        user     = self.request.user
        employee = getattr(user, 'employee_profile', None)

        if not employee:
            raise ValidationError(
                'Your account is not linked to an employee profile. '
                'Please contact HR to link your account.'
            )

        leave_type      = serializer.validated_data['leave_type']
        days_requested  = serializer.validated_data['days_requested']
        start_date      = serializer.validated_data['start_date']

        # Check leave balance
        balance = LeaveBalance.objects.filter(
            employee=employee,
            leave_type=leave_type,
            year=start_date.year,
        ).first()

        if balance and balance.available < days_requested:
            raise ValidationError(
                f'Insufficient leave balance. Available: {balance.available} days, '
                f'requested: {days_requested} days.'
            )

        application = serializer.save(employee=employee, status='pending')

        # Add to pending balance
        LeaveBalance.objects.filter(
            employee=employee,
            leave_type=leave_type,
            year=start_date.year,
        ).update(pending=F('pending') + days_requested)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'error': 'Only pending leaves can be approved'}, status=400)

        leave.status      = LeaveApplication.Status.APPROVED
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()

        # Move pending → taken
        LeaveBalance.objects.filter(
            employee=leave.employee,
            leave_type=leave.leave_type,
            year=leave.start_date.year,
        ).update(
            taken=F('taken') + leave.days_requested,
            pending=F('pending') - leave.days_requested,
        )
        return Response(LeaveApplicationSerializer(leave).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status != 'pending':
            return Response({'error': 'Only pending leaves can be rejected'}, status=400)

        reason = request.data.get('reason', '')
        leave.status           = LeaveApplication.Status.REJECTED
        leave.rejection_reason = reason
        leave.approved_by      = request.user
        leave.approved_at      = timezone.now()
        leave.save()

        # Remove from pending
        LeaveBalance.objects.filter(
            employee=leave.employee,
            leave_type=leave.leave_type,
            year=leave.start_date.year,
        ).update(pending=F('pending') - leave.days_requested)

        return Response(LeaveApplicationSerializer(leave).data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        user = request.user
        if not user.company_id:
            return Response([])
        qs = LeaveApplication.objects.filter(
            employee__company_id=user.company_id,
            status='approved',
        ).values(
            'employee__first_name', 'employee__last_name',
            'leave_type__name', 'start_date', 'end_date', 'days_requested'
        )
        return Response(list(qs))


router = DefaultRouter()
router.register(r'types',        LeaveTypeViewSet,        basename='leave-types')
router.register(r'benefits',     BenefitViewSet,           basename='benefits')
router.register(r'applications', LeaveApplicationViewSet, basename='leave-applications')
urlpatterns = [path('', include(router.urls))]
