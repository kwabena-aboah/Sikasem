"""
Payroll Calculation Engine
Handles all Ghana-compliant payroll computations:
- PAYE tax (GRA tax bands)
- SSNIT Tier 1, Tier 2, Tier 3
- Overtime, bonuses, allowances
- Loan/advance deductions
- Late penalties
- Custom rules engine
"""
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import (
    Payslip, PayslipComponent, TaxTable, CustomPayrollRule,
    EmployeeSalary, SalaryStructureComponent
)
from apps.attendance.models import AttendanceRecord
from apps.loans.models import LoanRepayment
import logging

logger = logging.getLogger(__name__)


def quantize(value, places=2):
    """Round to specified decimal places"""
    exp = Decimal(10) ** -places
    return Decimal(str(value)).quantize(exp, rounding=ROUND_HALF_UP)


def calculate_paye_monthly(taxable_income: Decimal, year: int = None) -> Decimal:
    """
    Calculate monthly PAYE tax using GRA tax bands.
    
    Ghana PAYE is calculated on annual basis then divided by 12.
    Personal relief of GHS 756/year is always applied.
    """
    if taxable_income <= 0:
        return Decimal('0.00')

    if year is None:
        year = timezone.now().year

    # Try to get tax bands from DB (updatable), fall back to settings
    tax_bands = TaxTable.objects.filter(
        effective_year=year, country='GH', is_monthly=False
    ).order_by('min_amount')

    if tax_bands.exists():
        bands = [(b.min_amount, b.max_amount, b.rate) for b in tax_bands]
    else:
        # Default Ghana 2024 annual bands
        bands = [
            (Decimal('0'),      Decimal('4380'),   Decimal('0.00')),
            (Decimal('4380'),   Decimal('5580'),   Decimal('0.05')),
            (Decimal('5580'),   Decimal('6780'),   Decimal('0.10')),
            (Decimal('6780'),   Decimal('42780'),  Decimal('0.175')),
            (Decimal('42780'),  Decimal('240000'), Decimal('0.25')),
            (Decimal('240000'), None,               Decimal('0.30')),
        ]

    # Annualise monthly income
    annual_income = taxable_income * 12

    # Apply personal relief
    personal_relief = Decimal(str(settings.PERSONAL_RELIEF_ANNUAL))
    taxable_annual = max(annual_income - personal_relief, Decimal('0'))

    # Calculate annual tax
    annual_tax = Decimal('0')
    for i, (band_min, band_max, rate) in enumerate(bands):
        if taxable_annual <= band_min:
            break
        upper = min(taxable_annual, band_max) if band_max else taxable_annual
        band_income = upper - band_min
        if band_income > 0:
            annual_tax += band_income * rate

    # Return monthly tax
    monthly_tax = annual_tax / 12
    return quantize(monthly_tax)


def calculate_ssnit(basic_salary: Decimal, is_employee: bool = True,
                    include_tier2: bool = True) -> dict:
    """
    Calculate SSNIT contributions.
    
    Employee: 5.5% of basic salary
    Employer: 13% of basic salary (10.5% Tier 1 SSNIT + 2.5% Tier 2)
    """
    if basic_salary <= 0:
        return {
            'ssnit_employee': Decimal('0.00'),
            'tier2_employee': Decimal('0.00'),
            'ssnit_employer': Decimal('0.00'),
            'tier2_employer': Decimal('0.00'),
        }

    ssnit_emp_rate = Decimal(str(settings.SSNIT_EMPLOYEE_RATE))
    ssnit_empr_rate = Decimal('0.105')  # Employer's SSNIT share
    tier2_rate = Decimal(str(settings.SSNIT_TIER2_RATE))

    ssnit_employee = quantize(basic_salary * ssnit_emp_rate)
    ssnit_employer = quantize(basic_salary * ssnit_empr_rate)
    tier2_employer = quantize(basic_salary * tier2_rate) if include_tier2 else Decimal('0.00')

    return {
        'ssnit_employee': ssnit_employee,
        'tier2_employee': Decimal('0.00'),  # Tier 2 paid by employer on behalf of employee
        'ssnit_employer': ssnit_employer,
        'tier2_employer': tier2_employer,
    }


def calculate_tier3(basic_salary: Decimal, employee_rate: Decimal, employer_rate: Decimal) -> dict:
    """Calculate Tier 3 voluntary pension contributions"""
    return {
        'tier3_employee': quantize(basic_salary * employee_rate),
        'tier3_employer': quantize(basic_salary * employer_rate),
    }


def apply_payroll_rules(employee, component_values: dict, period_start, company) -> dict:
    """
    Apply custom rules engine to modify component values.
    Rules are evaluated in priority order.
    """
    rules = CustomPayrollRule.objects.filter(
        company=company,
        is_active=True
    ).filter(
        Q(valid_from__isnull=True) | Q(valid_from__lte=period_start)
    ).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gte=period_start)
    ).order_by('priority')

    for rule in rules:
        if not _rule_matches(rule, employee):
            continue

        comp_code = rule.component.code
        current_value = component_values.get(comp_code, Decimal('0'))

        try:
            if rule.action_type == 'add':
                component_values[comp_code] = current_value + rule.action_value
            elif rule.action_type == 'set':
                component_values[comp_code] = rule.action_value
            elif rule.action_type == 'multiply':
                component_values[comp_code] = current_value * rule.action_value
            elif rule.action_type == 'formula':
                # Safe formula evaluation
                ctx = {
                    'basic': float(component_values.get('BASIC', 0)),
                    'gross': float(sum(v for k, v in component_values.items() if v > 0)),
                    'value': float(current_value),
                    'years': float(employee.years_of_service),
                }
                result = eval(rule.action_formula, {"__builtins__": {}}, ctx)
                component_values[comp_code] = Decimal(str(result))

            logger.debug(f"Rule '{rule.name}' applied to {employee}: {comp_code} = {component_values[comp_code]}")
        except Exception as e:
            logger.error(f"Rule '{rule.name}' failed for {employee}: {e}")

    return component_values


def _rule_matches(rule: CustomPayrollRule, employee) -> bool:
    """Check if a payroll rule applies to this employee"""
    cond = rule.trigger_condition

    if rule.trigger_type == 'always':
        return True
    elif rule.trigger_type == 'dept':
        return str(employee.department_id) in cond.get('department_ids', [])
    elif rule.trigger_type == 'grade':
        return str(employee.job_grade_id) in cond.get('grade_ids', [])
    elif rule.trigger_type == 'emp_type':
        return employee.employment_type in cond.get('types', [])
    elif rule.trigger_type == 'tax':
        return employee.tax_treatment in cond.get('treatments', [])
    elif rule.trigger_type == 'tenure':
        years = employee.years_of_service
        return cond.get('min_years', 0) <= years <= cond.get('max_years', 999)
    elif rule.trigger_type == 'salary':
        basic = float(employee.salary_assignments.filter(is_current=True).first().basic_salary or 0)
        return cond.get('min_salary', 0) <= basic <= cond.get('max_salary', 9999999)

    return False


def calculate_overtime(base_daily_rate: Decimal, overtime_hours: Decimal,
                        multiplier: Decimal = Decimal('1.5')) -> Decimal:
    """Calculate overtime pay"""
    hourly_rate = base_daily_rate / 8  # 8-hour workday
    return quantize(hourly_rate * overtime_hours * multiplier)


def calculate_late_penalty(minutes_late: int, daily_rate: Decimal) -> Decimal:
    """Calculate penalty for lateness"""
    if minutes_late <= 0:
        return Decimal('0.00')
    minute_rate = daily_rate / (8 * 60)  # cost per minute
    return quantize(minute_rate * minutes_late)


class PayrollCalculator:
    """
    Main payroll calculator for a single employee in a period.
    
    Usage:
        calc = PayrollCalculator(payslip, period)
        payslip = calc.calculate()
    """

    def __init__(self, payslip: Payslip, period):
        self.payslip = payslip
        self.period = period
        self.employee = payslip.employee
        self.company = period.company
        self.settings = self.company.settings

    def calculate(self) -> Payslip:
        """Run full payroll calculation for this employee"""
        ps = self.payslip

        # 1. Get current salary assignment
        salary_assignment = self.employee.salary_assignments.filter(
            is_current=True,
            effective_from__lte=self.period.period_end,
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=self.period.period_start),
            structure__company=self.company,
        ).select_related('structure').first()

        if not salary_assignment:
            logger.warning('No valid salary assignment for %s in company %s', self.employee, self.company.id)
            raise ValueError('No valid salary assignment covers this employee and payroll period.')

        ps.basic_salary = salary_assignment.basic_salary

        # 2. Build component values from structure
        component_values = self._build_component_values(salary_assignment)

        # 3. Apply custom rules engine
        component_values = apply_payroll_rules(
            self.employee, component_values,
            self.period.period_start, self.company
        )

        # 4. Get attendance data
        attendance_data = self._get_attendance_data()
        ps.working_days = attendance_data['working_days']
        ps.days_present = attendance_data['days_present']
        ps.days_absent = attendance_data['days_absent']
        ps.leave_days = attendance_data['leave_days']
        ps.overtime_hours = attendance_data['overtime_hours']

        # 5. Calculate prorated salary if needed
        if ps.days_absent > 0 and ps.days_absent < ps.working_days:
            daily_rate = ps.basic_salary / ps.working_days
            prorate_factor = Decimal(str(ps.days_present + ps.leave_days)) / Decimal(str(ps.working_days))
            component_values['BASIC'] = quantize(ps.basic_salary * prorate_factor)

        # 6. Calculate overtime
        if attendance_data['overtime_hours'] > 0:
            daily_rate = ps.basic_salary / (Decimal('22'))  # avg working days
            ps.overtime_pay = calculate_overtime(
                daily_rate, Decimal(str(attendance_data['overtime_hours'])),
                Decimal(str(self.settings.overtime_rate_multiplier))
            )

        # 7. Separate earnings and deductions from components
        earnings = {}
        deductions = {}
        for comp_code, amount in component_values.items():
            comp_obj = salary_assignment.structure.components.filter(code=comp_code).first()
            if comp_obj:
                if comp_obj.component_type == 'earning':
                    earnings[comp_code] = amount
                elif comp_obj.component_type == 'deduction':
                    deductions[comp_code] = amount

        ps.total_allowances = quantize(sum(
            v for k, v in earnings.items() if k != 'BASIC'
        ))
        ps.gross_pay = quantize(
            ps.basic_salary + ps.total_allowances + ps.overtime_pay + ps.bonus
        )

        # 8. Statutory deductions
        if not self.employee.is_exempt_ssnit and self.settings.enable_ssnit:
            ssnit = calculate_ssnit(ps.basic_salary, include_tier2=self.settings.enable_tier2)
            ps.ssnit_employee = ssnit['ssnit_employee']
            ps.ssnit_employer = ssnit['ssnit_employer']
            ps.tier2_employer = ssnit['tier2_employer']

        if self.settings.enable_tier3:
            tier3 = calculate_tier3(
                ps.basic_salary,
                self.settings.tier3_employee_rate,
                self.settings.tier3_employer_rate
            )
            ps.tier3_employee = tier3['tier3_employee']

        # 9. PAYE tax
        if not self.employee.is_exempt_paye and self.settings.enable_paye:
            # Taxable income = gross - SSNIT employee - pension
            taxable_income = ps.gross_pay - ps.ssnit_employee - ps.tier2_employee - ps.tier3_employee
            ps.paye_tax = calculate_paye_monthly(taxable_income)

            # Non-resident: flat 25%
            if self.employee.tax_treatment == 'non_resident':
                ps.paye_tax = quantize(taxable_income * Decimal('0.25'))
            elif self.employee.tax_treatment == 'casual':
                ps.paye_tax = quantize(taxable_income * Decimal('0.05'))

        # 10. Late penalty
        if self.settings.enable_late_penalty and attendance_data['total_minutes_late'] > 0:
            daily_rate = ps.basic_salary / Decimal('22')
            ps.late_penalty = calculate_late_penalty(
                attendance_data['total_minutes_late'], daily_rate
            )

        # 11. Loan & advance repayments
        loan_repayments = self._get_loan_repayments()
        ps.loan_repayment = quantize(sum(lr['amount'] for lr in loan_repayments))

        # 12. Other deductions from salary structure
        ps.other_deductions = quantize(sum(deductions.values()))

        # 13. Final totals
        ps.calculate_totals()

        # 14. Store line-item breakdown
        ps.earnings_breakdown = [
            {'code': k, 'name': k, 'amount': float(v)}
            for k, v in {**earnings, 'overtime': float(ps.overtime_pay), 'bonus': float(ps.bonus)}.items()
            if v > 0
        ]
        ps.deductions_breakdown = [
            {'code': 'PAYE', 'name': 'PAYE Tax', 'amount': float(ps.paye_tax)},
            {'code': 'SSNIT_EMP', 'name': 'SSNIT (Employee)', 'amount': float(ps.ssnit_employee)},
            {'code': 'TIER3', 'name': 'Tier 3 Pension', 'amount': float(ps.tier3_employee)},
            {'code': 'LOAN', 'name': 'Loan Repayment', 'amount': float(ps.loan_repayment)},
            {'code': 'LATE', 'name': 'Late Penalty', 'amount': float(ps.late_penalty)},
            *[{'code': k, 'name': k, 'amount': float(v)} for k, v in deductions.items()],
        ]

        ps.generated_at = timezone.now()
        ps.status = Payslip.Status.GENERATED
        ps.save()

        # 15. Mark loan repayments as applied
        self._apply_loan_repayments(loan_repayments)

        return ps

    def _build_component_values(self, salary_assignment) -> dict:
        """Build initial component values from salary structure"""
        values = {'BASIC': salary_assignment.basic_salary}

        # Get structure defaults
        for sc in salary_assignment.structure.structure_components.select_related('component').all():
            comp = sc.component
            if sc.calculation_method == 'pct_basic' or comp.calculation_method == 'pct_basic':
                values[comp.code] = quantize(salary_assignment.basic_salary * sc.value)
            elif sc.calculation_method == 'pct_gross':
                # Will be recalculated after gross is known
                values[comp.code] = quantize(salary_assignment.basic_salary * sc.value)
            else:
                values[comp.code] = quantize(sc.value)

        # Apply employee-level overrides
        for override in salary_assignment.component_overrides.select_related('component').all():
            comp = override.component
            if override.override_method == 'pct_basic':
                values[comp.code] = quantize(salary_assignment.basic_salary * override.value)
            else:
                values[comp.code] = quantize(override.value)

        return values

    def _get_attendance_data(self) -> dict:
        """Aggregate attendance data for the pay period"""
        # Count working days (Mon-Fri) within the actual period start and end dates
        working_days = 0
        curr = self.period.period_start
        while curr <= self.period.period_end:
            if curr.weekday() < 5:  # Monday to Friday
                working_days += 1
            curr += datetime.timedelta(days=1)

        records = AttendanceRecord.objects.filter(
            employee=self.employee,
            date__range=[self.period.period_start, self.period.period_end]
        )

        days_present = records.filter(status='present').count()
        leave_days = records.filter(status='leave').count()
        overtime_hours = sum(
            r.overtime_hours or 0 for r in records if r.overtime_hours
        )
        total_minutes_late = sum(
            r.minutes_late or 0 for r in records if r.minutes_late
        )

        return {
            'working_days': working_days,
            'days_present': days_present,
            'days_absent': max(0, working_days - days_present - leave_days),
            'leave_days': leave_days,
            'overtime_hours': Decimal(str(overtime_hours)),
            'total_minutes_late': total_minutes_late,
        }

    def _get_loan_repayments(self) -> list:
        """Get pending loan repayments for this period"""
        from apps.loans.models import LoanRepayment
        repayments = LoanRepayment.objects.filter(
            loan__employee=self.employee,
            due_date__range=[self.period.period_start, self.period.period_end],
            status='pending'
        ).select_related('loan')

        return [{'id': r.id, 'amount': r.amount, 'loan_id': r.loan_id} for r in repayments]

    def _apply_loan_repayments(self, repayments: list):
        """Mark loan repayments as deducted"""
        from apps.loans.models import LoanRepayment
        ids = [r['id'] for r in repayments]
        LoanRepayment.objects.filter(id__in=ids).update(
            status='deducted', deducted_in=self.payslip
        )


def run_payroll_period(period_id: str) -> dict:
    """Process all eligible employees for a payroll period."""
    from .models import PayrollPeriod, Payslip
    from apps.employees.models import Employee
    from django.db.models import Sum

    period = PayrollPeriod.objects.get(id=period_id)
    period.status = PayrollPeriod.Status.PROCESSING
    period.save(update_fields=['status', 'updated_at'])

    employees = Employee.objects.filter(
        company=period.company,
        status__in=['active', 'on_leave', 'probation'],
    ).prefetch_related('salary_assignments')

    selected = []
    missing_salary = []
    errors = []
    processed = 0

    for employee in employees:
        salary_exists = employee.salary_assignments.filter(
            is_current=True,
            effective_from__lte=period.period_end,
            structure__company=period.company,
        ).filter(
            Q(effective_to__isnull=True) | Q(effective_to__gte=period.period_start)
        ).exists()

        if not salary_exists:
            missing_salary.append({
                'employee_id': str(employee.id),
                'employee_code': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'error': 'No valid salary assignment for this company and payroll period.',
            })
            continue

        selected.append({
            'employee_id': str(employee.id),
            'employee_code': employee.employee_id,
            'employee_name': employee.get_full_name(),
        })

        try:
            payslip, _ = Payslip.objects.get_or_create(
                payroll_period=period,
                employee=employee,
                defaults={'status': Payslip.Status.DRAFT},
            )
            PayrollCalculator(payslip, period).calculate()
            processed += 1
        except Exception as exc:
            logger.exception('Error processing payroll for %s', employee)
            errors.append({
                'employee_id': str(employee.id),
                'employee_code': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'error': str(exc),
            })

    totals = Payslip.objects.filter(payroll_period=period).aggregate(
        gross=Sum('gross_pay'),
        deductions=Sum('total_deductions'),
        net=Sum('net_pay'),
        employer_costs=Sum('ssnit_employer') + Sum('tier2_employer'),
    )

    period.total_gross = totals['gross'] or 0
    period.total_deductions = totals['deductions'] or 0
    period.total_net = totals['net'] or 0
    period.total_employer_costs = totals['employer_costs'] or 0
    period.employee_count = processed
    period.status = PayrollPeriod.Status.REVIEW
    period.processed_at = timezone.now()
    period.save()

    return {
        'period_id': str(period.id),
        'selected_count': len(selected),
        'selected_employees': selected,
        'processed': processed,
        'missing_salary_count': len(missing_salary),
        'errors': missing_salary + errors,
        'total_gross': float(period.total_gross),
        'total_net': float(period.total_net),
    }
