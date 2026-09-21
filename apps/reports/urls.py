"""reports/urls.py - Analytics, exports, compliance reports"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
import datetime


from rest_framework.exceptions import PermissionDenied
from apps.accounts.models import User


class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Main dashboard KPIs - role tailored"""
        from apps.employees.models import Employee
        from apps.payroll.models import PayrollPeriod, Payslip
        from apps.leaves.models import LeaveApplication, LeaveBalance
        from apps.loans.models import Loan
        from apps.attendance.models import AttendanceRecord

        user = request.user
        company = user.company
        today = timezone.now().date()

        # ── EMPLOYEE SELF-SERVICE DASHBOARD ─────────────────────────
        if user.role == User.Role.EMPLOYEE:
            employee = getattr(user, 'employee_profile', None)
            if not employee:
                return Response({
                    'role': 'employee',
                    'has_profile': False,
                    'message': 'No employee profile linked to your user account.',
                    'latest_payslip': None,
                    'leave_balances': [],
                    'total_leave_available': 0,
                    'pending_leaves': 0,
                    'active_loans': {'count': 0, 'total_outstanding': 0.0, 'monthly_deduction': 0.0},
                    'attendance': {'present': 0, 'absent': 0, 'late': 0, 'leave': 0, 'overtime': 0.0},
                    'payroll_trend': [],
                    'recent_payslips': [],
                    'recent_leaves': [],
                })

            # Latest payslip
            latest_ps = Payslip.objects.filter(
                employee=employee,
                payroll_period__status__in=['approved', 'paid']
            ).select_related('payroll_period').order_by('-payroll_period__period_start').first()

            latest_payroll = None
            if latest_ps:
                latest_payroll = {
                    'id': str(latest_ps.id),
                    'name': latest_ps.payroll_period.name,
                    'gross_pay': float(latest_ps.gross_pay),
                    'net_pay': float(latest_ps.net_pay),
                    'total_deductions': float(latest_ps.total_deductions),
                    'pay_date': latest_ps.payroll_period.pay_date.isoformat() if latest_ps.payroll_period.pay_date else None,
                    'status': latest_ps.status,
                }

            # Leave balances (current year)
            balances = LeaveBalance.objects.filter(
                employee=employee,
                year=today.year
            ).select_related('leave_type')

            leave_balance_list = [
                {
                    'leave_type': b.leave_type.name,
                    'leave_type_id': str(b.leave_type_id),
                    'entitled': float(b.entitled),
                    'taken': float(b.taken),
                    'pending': float(b.pending),
                    'available': float(b.available),
                }
                for b in balances
            ]
            total_leave_available = sum(b['available'] for b in leave_balance_list)

            # Pending leaves
            my_pending_leaves = LeaveApplication.objects.filter(
                employee=employee, status='pending'
            ).count()

            # Active loans
            my_loans = Loan.objects.filter(
                employee=employee, status='active'
            ).aggregate(
                count=Count('id'),
                total=Sum('outstanding_balance'),
                monthly=Sum('monthly_repayment')
            )

            # Attendance this month
            att_summary = AttendanceRecord.objects.filter(
                employee=employee,
                date__year=today.year,
                date__month=today.month
            ).aggregate(
                present=Count('id', filter=Q(status='present')),
                absent=Count('id', filter=Q(status='absent')),
                late=Count('id', filter=Q(status='late')),
                leave=Count('id', filter=Q(status='leave')),
                overtime=Sum('overtime_hours'),
            )

            # Personal 6-month earnings trend
            ps_history = list(Payslip.objects.filter(
                employee=employee,
                payroll_period__status__in=['approved', 'paid']
            ).select_related('payroll_period').order_by('-payroll_period__period_start')[:6])
            ps_history.reverse()

            personal_trend = [
                {
                    'name': ps.payroll_period.name,
                    'period_start': ps.payroll_period.period_start.isoformat(),
                    'gross': float(ps.gross_pay),
                    'net': float(ps.net_pay),
                    'deductions': float(ps.total_deductions),
                }
                for ps in ps_history
            ]

            # Recent payslips (last 5)
            recent_payslips = [
                {
                    'id': str(ps.id),
                    'period_name': ps.payroll_period.name,
                    'basic_salary': float(ps.basic_salary),
                    'gross_pay': float(ps.gross_pay),
                    'total_deductions': float(ps.total_deductions),
                    'net_pay': float(ps.net_pay),
                    'status': ps.status,
                    'pay_date': ps.payroll_period.pay_date.isoformat() if ps.payroll_period.pay_date else None,
                }
                for ps in reversed(ps_history)
            ]

            # Recent leave applications
            recent_leaves = list(LeaveApplication.objects.filter(
                employee=employee
            ).select_related('leave_type').order_by('-applied_at')[:5].values(
                'id', 'leave_type__name', 'start_date', 'end_date', 'days_requested', 'status', 'applied_at'
            ))

            return Response({
                'role': 'employee',
                'has_profile': True,
                'employee': {
                    'id': str(employee.id),
                    'employee_id': employee.employee_id,
                    'full_name': employee.get_full_name(),
                    'job_title': employee.job_title,
                    'department': employee.department.name if employee.department else '',
                    'status': employee.status,
                },
                'latest_payroll': latest_payroll,
                'leave_balances': leave_balance_list,
                'total_leave_available': total_leave_available,
                'pending_leaves': my_pending_leaves,
                'active_loans': {
                    'count': my_loans['count'] or 0,
                    'total_outstanding': float(my_loans['total'] or 0),
                    'monthly_deduction': float(my_loans['monthly'] or 0),
                },
                'attendance': {
                    'present': att_summary['present'] or 0,
                    'absent': att_summary['absent'] or 0,
                    'late': att_summary['late'] or 0,
                    'leave': att_summary['leave'] or 0,
                    'overtime': float(att_summary['overtime'] or 0),
                },
                'payroll_trend': personal_trend,
                'recent_payslips': recent_payslips,
                'recent_leaves': recent_leaves,
            })

        # ── MANAGEMENT / ADMIN / HR / PAYROLL DASHBOARD ──────────────
        emp_filter = Q(company=company)
        leave_filter = Q(employee__company=company, status='pending')
        loan_filter = Q(employee__company=company, status='active')

        # Branch Manager Scoping
        if user.role == User.Role.BRANCH_MANAGER and user.branch_id:
            emp_filter &= Q(branch_id=user.branch_id)
            leave_filter &= Q(employee__branch_id=user.branch_id)
            loan_filter &= Q(employee__branch_id=user.branch_id)

        # Employee stats
        employee_stats = Employee.objects.filter(emp_filter).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            on_leave=Count('id', filter=Q(status='on_leave')),
            probation=Count('id', filter=Q(status='probation')),
        )

        # Latest payroll
        latest_period = PayrollPeriod.objects.filter(
            company=company, status__in=['approved', 'paid']
        ).order_by('-period_start').first()

        latest_payroll = None
        if latest_period:
            latest_payroll = {
                'id': str(latest_period.id),
                'name': latest_period.name,
                'total_gross': float(latest_period.total_gross),
                'total_net': float(latest_period.total_net),
                'employee_count': latest_period.employee_count,
                'status': latest_period.status,
                'pay_date': latest_period.pay_date.isoformat() if latest_period.pay_date else None,
            }

        # Pending leaves
        pending_leaves = LeaveApplication.objects.filter(leave_filter).count()

        # Active loans
        active_loans = Loan.objects.filter(loan_filter).aggregate(
            count=Count('id'), total=Sum('outstanding_balance')
        )

        # Payroll trend (last 6 months)
        six_months_ago = today - datetime.timedelta(days=180)
        payroll_trend = PayrollPeriod.objects.filter(
            company=company,
            period_start__gte=six_months_ago,
            status__in=['approved', 'paid']
        ).values('name', 'period_start').annotate(
            gross=Sum('total_gross'),
            net=Sum('total_net'),
            count=Sum('employee_count'),
        ).order_by('period_start')

        # Department headcount
        dept_headcount = Employee.objects.filter(
            emp_filter & Q(status='active')
        ).values('department__name').annotate(count=Count('id')).order_by('-count')

        return Response({
            'role': user.role,
            'employees': employee_stats,
            'latest_payroll': latest_payroll,
            'pending_leaves': pending_leaves,
            'active_loans': {
                'count': active_loans['count'] or 0,
                'total_outstanding': float(active_loans['total'] or 0),
            },
            'payroll_trend': list(payroll_trend),
            'department_headcount': list(dept_headcount),
        })

    def _require_management_role(self, request):
        if request.user.role == User.Role.EMPLOYEE:
            raise PermissionDenied("Employees are not authorized to access company reports.")

    @action(detail=False, methods=['get'])
    def payroll_summary(self, request):
        """Detailed payroll summary for a period"""
        self._require_management_role(request)
        from apps.payroll.models import PayrollPeriod, Payslip
        period_id = request.query_params.get('period_id')

        if not period_id:
            return Response({'error': 'period_id required'}, status=400)

        period = PayrollPeriod.objects.get(id=period_id, company=request.user.company)
        payslips = Payslip.objects.filter(payroll_period=period)

        summary = payslips.aggregate(
            total_basic=Sum('basic_salary'),
            total_allowances=Sum('total_allowances'),
            total_overtime=Sum('overtime_pay'),
            total_bonus=Sum('bonus'),
            total_gross=Sum('gross_pay'),
            total_paye=Sum('paye_tax'),
            total_ssnit_emp=Sum('ssnit_employee'),
            total_ssnit_empr=Sum('ssnit_employer'),
            total_tier2=Sum('tier2_employer'),
            total_loans=Sum('loan_repayment'),
            total_deductions=Sum('total_deductions'),
            total_net=Sum('net_pay'),
            count=Count('id'),
        )

        # By department
        by_dept = payslips.values('employee__department__name').annotate(
            gross=Sum('gross_pay'), net=Sum('net_pay'), count=Count('id')
        ).order_by('employee__department__name')

        return Response({
            'period': {'id': str(period.id), 'name': period.name, 'status': period.status},
            'summary': {k: float(v) if v else 0 for k, v in summary.items()},
            'by_department': list(by_dept),
        })

    @action(detail=False, methods=['get'])
    def tax_report(self, request):
        """PAYE and SSNIT compliance report"""
        self._require_management_role(request)
        from apps.payroll.models import Payslip, PayrollPeriod
        year = int(request.query_params.get('year', timezone.now().year))

        periods = PayrollPeriod.objects.filter(
            company=request.user.company,
            period_start__year=year,
            status__in=['approved', 'paid']
        )

        monthly = []
        for period in periods.order_by('period_start'):
            totals = Payslip.objects.filter(payroll_period=period).aggregate(
                paye=Sum('paye_tax'),
                ssnit_emp=Sum('ssnit_employee'),
                ssnit_empr=Sum('ssnit_employer'),
                tier2=Sum('tier2_employer'),
                gross=Sum('gross_pay'),
                count=Count('id'),
            )
            monthly.append({
                'period': period.name,
                'month': period.period_start.month,
                **{k: float(v or 0) for k, v in totals.items()}
            })

        annual_totals = {
            'paye': sum(m['paye'] for m in monthly),
            'ssnit_employee': sum(m['ssnit_emp'] for m in monthly),
            'ssnit_employer': sum(m['ssnit_empr'] for m in monthly),
            'tier2_employer': sum(m['tier2'] for m in monthly),
            'total_gross': sum(m['gross'] for m in monthly),
        }

        return Response({'year': year, 'monthly': monthly, 'annual_totals': annual_totals})

    @action(detail=False, methods=['get'])
    def headcount_report(self, request):
        """Headcount movements: hires, terminations"""
        self._require_management_role(request)
        from apps.employees.models import Employee
        year = int(request.query_params.get('year', timezone.now().year))
        company = request.user.company

        monthly = []
        for month in range(1, 13):
            hires = Employee.objects.filter(
                company=company, hire_date__year=year, hire_date__month=month
            ).count()
            terminations = Employee.objects.filter(
                company=company, termination_date__year=year, termination_date__month=month
            ).count()
            monthly.append({'month': month, 'hires': hires, 'terminations': terminations})

        return Response({'year': year, 'monthly': monthly})

    @action(detail=False, methods=['get'])
    def leave_report(self, request):
        """Leave utilisation report"""
        self._require_management_role(request)
        from apps.leaves.models import LeaveApplication, LeaveBalance
        year = int(request.query_params.get('year', timezone.now().year))
        company = request.user.company

        by_type = LeaveApplication.objects.filter(
            employee__company=company,
            start_date__year=year,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Sum('days_requested'),
            applications=Count('id'),
        ).order_by('-total_days')

        return Response({'year': year, 'by_leave_type': list(by_type)})

    @action(detail=False, methods=['get'])
    def export_payroll_csv(self, request):
        """Export payroll data as CSV"""
        self._require_management_role(request)
        import csv
        from django.http import HttpResponse
        from apps.payroll.models import Payslip
        period_id = request.query_params.get('period_id')

        payslips = Payslip.objects.filter(
            payroll_period_id=period_id,
            payroll_period__company=request.user.company
        ).select_related('employee', 'payroll_period')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payroll_{period_id}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'Name', 'Department', 'Basic Salary', 'Allowances',
            'Overtime', 'Bonus', 'Gross Pay', 'PAYE', 'SSNIT Employee',
            'Loan Repayment', 'Total Deductions', 'Net Pay', 'Bank', 'Account'
        ])

        for p in payslips:
            writer.writerow([
                p.employee.employee_id, p.employee.get_full_name(),
                p.employee.department.name if p.employee.department else '',
                p.basic_salary, p.total_allowances, p.overtime_pay, p.bonus,
                p.gross_pay, p.paye_tax, p.ssnit_employee, p.loan_repayment,
                p.total_deductions, p.net_pay, p.employee.bank_name, p.employee.account_number
            ])

        return response


router = DefaultRouter()
router.register(r'', ReportsViewSet, basename='reports')
urlpatterns = [path('', include(router.urls))]
