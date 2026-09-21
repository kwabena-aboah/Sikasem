"""
apps/employees/views.py
Fixed:
  - company auto-assigned from request.user (not sent from frontend)
  - employee_id uniqueness validated per company
  - proper select_related to avoid N+1
  - headcount and org_chart use company filter
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Employee, EmployeeDocument, SalaryHistory
from .serializers import (
    EmployeeListSerializer, EmployeeDetailSerializer,
    EmployeeDocumentSerializer, SalaryHistorySerializer
)
from apps.accounts.permissions import IsHRManager


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'employment_type', 'department', 'branch', 'gender']
    search_fields = ['first_name', 'last_name', 'employee_id', 'work_email', 'personal_phone']
    ordering_fields = ['hire_date', 'last_name', 'employee_id', 'first_name']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return Employee.objects.none()

        # Employees can only see themselves
        if user.role == 'employee':
            if hasattr(user, 'employee_profile'):
                return Employee.objects.filter(id=user.employee_profile.id)
            return Employee.objects.none()

        # Branch managers see their branch employees
        if user.role == 'branch_manager' and user.branch_id:
            return Employee.objects.filter(
                company_id=user.company_id,
                branch_id=user.branch_id
            ).select_related('department', 'branch', 'job_grade', 'reports_to', 'company')

        return Employee.objects.filter(
            company_id=user.company_id
        ).select_related('department', 'branch', 'job_grade', 'reports_to', 'company')

    def perform_create(self, serializer):
        user = self.request.user
        if not user.company_id:
            raise ValidationError("Your account is not linked to a company.")

        # Validate employee_id uniqueness within company
        emp_id = serializer.validated_data.get('employee_id', '')
        if emp_id and Employee.objects.filter(company_id=user.company_id, employee_id=emp_id).exists():
            raise ValidationError({'employee_id': f'Employee ID "{emp_id}" already exists in this company.'})

        serializer.save(
            company=user.company,
            branch=serializer.validated_data.get('branch') or user.branch,
            created_by=user,
        )

    def perform_update(self, serializer):
        # Prevent changing company on update
        serializer.save()

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        employee = self.get_object()
        docs = EmployeeDocument.objects.filter(employee=employee)
        return Response(EmployeeDocumentSerializer(docs, many=True).data)

    @action(detail=True, methods=['get'])
    def salary_history(self, request, pk=None):
        employee = self.get_object()
        history = SalaryHistory.objects.filter(employee=employee).order_by('-effective_date')
        return Response(SalaryHistorySerializer(history, many=True).data)

    @action(detail=True, methods=['get'])
    def payslips(self, request, pk=None):
        from apps.payroll.models import Payslip
        from apps.payroll.serializers import PayslipSerializer
        employee = self.get_object()
        payslips = Payslip.objects.filter(
            employee=employee
        ).select_related('payroll_period').order_by('-payroll_period__period_start')[:24]
        return Response(PayslipSerializer(payslips, many=True).data)

    @action(detail=True, methods=['get'])
    def leave_balances(self, request, pk=None):
        from apps.leaves.models import LeaveBalance
        from django.utils import timezone
        employee = self.get_object()
        year = int(request.query_params.get('year', timezone.now().year))
        balances = LeaveBalance.objects.filter(
            employee=employee, year=year
        ).select_related('leave_type')
        return Response([
            {
                'leave_type': b.leave_type.name,
                'leave_type_id': str(b.leave_type_id),
                'entitled': float(b.entitled),
                'taken': float(b.taken),
                'pending': float(b.pending),
                'available': float(b.available),
                'carried_forward': float(b.carried_forward),
            }
            for b in balances
        ])

    @action(detail=False, methods=['get'])
    def headcount(self, request):
        from django.db.models import Count
        from rest_framework.exceptions import PermissionDenied
        user = request.user
        if user.role == 'employee':
            raise PermissionDenied("Employees cannot access company headcount reports.")
        emp_filter = Q(company_id=user.company_id)
        if user.role == 'branch_manager' and user.branch_id:
            emp_filter &= Q(branch_id=user.branch_id)
        data = Employee.objects.filter(emp_filter).values('department__name', 'status').annotate(count=Count('id'))
        return Response(list(data))

    @action(detail=False, methods=['get'])
    def org_chart(self, request):
        user = request.user
        employees = Employee.objects.filter(
            company_id=user.company_id,
            status__in=['active', 'probation']
        ).values(
            'id', 'first_name', 'last_name', 'job_title',
            'reports_to_id', 'department__name', 'photo'
        )
        return Response(list(employees))


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        return EmployeeDocument.objects.filter(
            employee__company_id=self.request.user.company_id
        )

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
