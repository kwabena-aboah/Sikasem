"""reports/urls.py - Analytics, exports, compliance reports"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
import datetime


class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Main dashboard KPIs"""
        from apps.employees.models import Employee
        from apps.payroll.models import PayrollPeriod, Payslip
        from apps.leaves.models import LeaveApplication
        from apps.loans.models import Loan

        company = request.user.company
        today = timezone.now().date()

        # Employee stats
        employee_stats = Employee.objects.filter(company=company).aggregate(
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
                'name': latest_period.name,
                'total_gross': float(latest_period.total_gross),
                'total_net': float(latest_period.total_net),
                'employee_count': latest_period.employee_count,
                'status': latest_period.status,
                'pay_date': latest_period.pay_date.isoformat(),
            }

        # Pending leaves
        pending_leaves = LeaveApplication.objects.filter(
            employee__company=company, status='pending'
        ).count()

        # Active loans
        active_loans = Loan.objects.filter(
            employee__company=company, status='active'
        ).aggregate(count=Count('id'), total=Sum('outstanding_balance'))

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
            company=company, status='active'
        ).values('department__name').annotate(count=Count('id')).order_by('-count')

        return Response({
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

    @action(detail=False, methods=['get'])
    def payroll_summary(self, request):
        """Detailed payroll summary for a period"""
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
