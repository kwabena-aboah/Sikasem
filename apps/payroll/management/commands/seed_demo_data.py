"""
Management command: seed_demo_data
Seeds sample company, departments, employees, and payroll data for demo/testing.
Run: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import datetime


class Command(BaseCommand):
    help = 'Seed demo data for Sikasem'

    def handle(self, *args, **options):
        from apps.companies.models import Company, Branch, Department, JobGrade, CompanySettings
        from apps.accounts.models import User
        from apps.employees.models import Employee
        from apps.payroll.models import SalaryComponent, SalaryStructure, SalaryStructureComponent

        self.stdout.write('Seeding demo data...')

        # ── Company ───────────────────────────────────────────────
        company, _ = Company.objects.get_or_create(
            name='Akosua Tech Ltd',
            defaults={
                'trading_name': 'AkosuaTech',
                'registration_number': 'CS-2018-123456',
                'tin': 'C0012345678',
                'ssnit_employer_code': 'EC-0012345',
                'email': 'hr@akosuatech.gh',
                'phone': '+233302000001',
                'address': '14 Independence Avenue, Accra',
                'city': 'Accra',
                'region': 'Greater Accra',
                'country': 'GH',
                'currency': 'GHS',
                'status': 'active',
                'payroll_day': 25,
            }
        )

        CompanySettings.objects.get_or_create(
            company=company,
            defaults={
                'enable_paye': True,
                'enable_ssnit': True,
                'enable_tier2': True,
                'enable_tier3': False,
                'overtime_rate_multiplier': Decimal('1.5'),
                'annual_leave_days': 15,
                'sick_leave_days': 14,
                'maternity_leave_days': 84,
                'paternity_leave_days': 5,
            }
        )

        # ── Branch ────────────────────────────────────────────────
        hq, _ = Branch.objects.get_or_create(
            company=company, code='HQ',
            defaults={'name': 'Headquarters', 'city': 'Accra', 'is_headquarters': True}
        )
        kumasi, _ = Branch.objects.get_or_create(
            company=company, code='KSI',
            defaults={'name': 'Kumasi Branch', 'city': 'Kumasi'}
        )

        # ── Departments ───────────────────────────────────────────
        depts = {}
        for code, name in [('ENG', 'Engineering'), ('HR', 'Human Resources'), ('FIN', 'Finance'), ('OPS', 'Operations'), ('SALES', 'Sales')]:
            dept, _ = Department.objects.get_or_create(
                company=company, code=code,
                defaults={'name': name, 'branch': hq}
            )
            depts[code] = dept

        # ── Job Grades ────────────────────────────────────────────
        grades = {}
        for code, name, min_s, max_s in [
            ('JR', 'Junior', 1500, 2500),
            ('MID', 'Mid-Level', 2500, 4000),
            ('SR', 'Senior', 4000, 7000),
            ('MGR', 'Manager', 6000, 12000),
            ('DIR', 'Director', 10000, 25000),
        ]:
            grade, _ = JobGrade.objects.get_or_create(
                company=company, code=code,
                defaults={'name': name, 'min_salary': min_s, 'max_salary': max_s}
            )
            grades[code] = grade

        # ── Admin user ────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            email='admin@akosuatech.gh',
            defaults={
                'first_name': 'Kwame',
                'last_name': 'Mensah',
                'role': User.Role.COMPANY_ADMIN,
                'company': company,
                'branch': hq,
                'is_active': True,
                'must_change_password': False,
            }
        )
        if created:
            admin.set_password('Admin@1234')
            admin.save()

        hr_user, created = User.objects.get_or_create(
            email='hr@akosuatech.gh',
            defaults={
                'first_name': 'Abena',
                'last_name': 'Asante',
                'role': User.Role.HR_MANAGER,
                'company': company,
                'branch': hq,
                'is_active': True,
                'must_change_password': False,
            }
        )
        if created:
            hr_user.set_password('HR@12345')
            hr_user.save()

        # ── Salary Components ─────────────────────────────────────
        components = {}
        comp_defs = [
            ('BASIC', 'Basic Salary', 'earning', 'fixed', True, True),
            ('HOUSING', 'Housing Allowance', 'earning', 'pct_basic', False, False),
            ('TRANSPORT', 'Transport Allowance', 'earning', 'fixed', False, False),
            ('MEDICAL', 'Medical Allowance', 'earning', 'fixed', False, False),
            ('OVERTIME', 'Overtime Pay', 'earning', 'fixed', True, True),
        ]
        for code, name, ctype, method, taxable, pensionable in comp_defs:
            comp, _ = SalaryComponent.objects.get_or_create(
                company=company, code=code,
                defaults={
                    'name': name,
                    'component_type': ctype,
                    'calculation_method': method,
                    'is_taxable': taxable,
                    'is_pensionable': pensionable,
                }
            )
            components[code] = comp

        # ── Salary Structures ─────────────────────────────────────
        standard, _ = SalaryStructure.objects.get_or_create(
            company=company, code='STD',
            defaults={'name': 'Standard Monthly', 'is_default': True}
        )

        structure_comps = [
            (components['BASIC'], Decimal('0'), 'fixed'),
            (components['HOUSING'], Decimal('0.25'), 'pct_basic'),
            (components['TRANSPORT'], Decimal('400'), 'fixed'),
            (components['MEDICAL'], Decimal('200'), 'fixed'),
        ]
        for comp, val, method in structure_comps:
            SalaryStructureComponent.objects.get_or_create(
                structure=standard, component=comp,
                defaults={'value': val, 'calculation_method': method}
            )

        # ── Employees ─────────────────────────────────────────────
        employee_data = [
            ('EMP001', 'Kofi', 'Boateng', 'M', depts['ENG'], grades['SR'], Decimal('5500'), 'full_time'),
            ('EMP002', 'Ama', 'Owusu', 'F', depts['HR'], grades['MID'], Decimal('3200'), 'full_time'),
            ('EMP003', 'Yaw', 'Darko', 'M', depts['FIN'], grades['MGR'], Decimal('8000'), 'full_time'),
            ('EMP004', 'Akua', 'Frimpong', 'F', depts['ENG'], grades['JR'], Decimal('1800'), 'full_time'),
            ('EMP005', 'Kwesi', 'Asare', 'M', depts['OPS'], grades['MID'], Decimal('2800'), 'full_time'),
            ('EMP006', 'Efua', 'Mensah', 'F', depts['SALES'], grades['MID'], Decimal('3500'), 'full_time'),
            ('EMP007', 'Kojo', 'Amponsah', 'M', depts['ENG'], grades['SR'], Decimal('6000'), 'full_time'),
            ('EMP008', 'Abena', 'Kyei', 'F', depts['HR'], grades['JR'], Decimal('1600'), 'full_time'),
        ]

        from apps.payroll.models import EmployeeSalary
        hire_date = datetime.date(2022, 1, 15)

        for emp_id, fname, lname, gender, dept, grade, basic, emp_type in employee_data:
            emp, created = Employee.objects.get_or_create(
                company=company, employee_id=emp_id,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'gender': gender,
                    'date_of_birth': datetime.date(1990, 1, 1),
                    'department': dept,
                    'branch': hq,
                    'job_grade': grade,
                    'job_title': f'{grade.name} {dept.name} Officer',
                    'employment_type': emp_type,
                    'status': 'active',
                    'hire_date': hire_date,
                    'confirmation_date': hire_date + datetime.timedelta(days=90),
                    'tax_treatment': 'resident',
                    'payment_method': 'bank',
                    'bank_name': 'GCB Bank',
                    'account_number': f'100{emp_id[3:]}0000001',
                    'work_email': f'{fname.lower()}.{lname.lower()}@akosuatech.gh',
                    'created_by': admin,
                }
            )
            if created:
                EmployeeSalary.objects.get_or_create(
                    employee=emp, is_current=True,
                    defaults={
                        'structure': standard,
                        'basic_salary': basic,
                        'effective_from': hire_date,
                        'approved_by': admin,
                    }
                )

        # ── Leave Types ───────────────────────────────────────────
        from apps.leaves.models import LeaveType, LeaveBalance
        leave_types_data = [
            ('ANNUAL', 'Annual Leave', 15, True),
            ('SICK', 'Sick Leave', 14, True),
            ('MATERNITY', 'Maternity Leave', 84, True),
            ('PATERNITY', 'Paternity Leave', 5, True),
            ('STUDY', 'Study Leave', 5, False),
        ]
        for code, name, days, paid in leave_types_data:
            lt, _ = LeaveType.objects.get_or_create(
                company=company, code=code,
                defaults={'name': name, 'days_per_year': days, 'is_paid': paid}
            )
            # Seed balances for all active employees
            for emp in Employee.objects.filter(company=company, status='active'):
                LeaveBalance.objects.get_or_create(
                    employee=emp, leave_type=lt, year=timezone.now().year,
                    defaults={'entitled': days, 'taken': 0, 'pending': 0}
                )

        # ── Loan Types ────────────────────────────────────────────
        from apps.loans.models import LoanType
        loan_type_defs = [
            ('SALARY_ADV', 'Salary Advance', 5000, 3, 'none', 0),
            ('PERSONAL', 'Personal Loan', 20000, 24, 'none', 0),
            ('EMERGENCY', 'Emergency Loan', 3000, 6, 'none', 0),
        ]
        for code, name, max_amt, max_months, int_type, rate in loan_type_defs:
            LoanType.objects.get_or_create(
                company=company, code=code,
                defaults={'name': name, 'max_amount': max_amt, 'max_months': max_months, 'interest_type': int_type, 'interest_rate': rate}
            )

        # ── Public Holidays ───────────────────────────────────────
        from apps.attendance.models import PublicHoliday
        year = timezone.now().year
        holidays = [
            (f'{year}-01-01', "New Year's Day"),
            (f'{year}-03-06', 'Independence Day'),
            (f'{year}-05-01', 'Workers Day'),
            (f'{year}-07-01', 'Republic Day'),
            (f'{year}-12-25', 'Christmas Day'),
            (f'{year}-12-26', 'Boxing Day'),
        ]
        for date_str, name in holidays:
            PublicHoliday.objects.get_or_create(
                date=datetime.date.fromisoformat(date_str),
                country='GH',
                defaults={'name': name, 'is_national': True}
            )

        # ── Link admin user to first employee, hr_user to second ──────────────
        employees_qs = Employee.objects.filter(company=company).order_by('employee_id')
        emp_list = list(employees_qs)

        # Create a user account for each employee (for self-service portal demo)
        from django.contrib.auth.hashers import make_password
        for i, emp in enumerate(emp_list):
            if emp.user_id:
                continue  # already linked
            emp_email = emp.work_email or f"{emp.employee_id.lower()}@akosuatech.gh"
            emp_user, created_u = User.objects.get_or_create(
                email=emp_email,
                defaults={
                    'first_name': emp.first_name,
                    'last_name':  emp.last_name,
                    'role':       User.Role.EMPLOYEE,
                    'company':    company,
                    'branch':     hq,
                    'is_active':  True,
                    'must_change_password': False,
                }
            )
            if created_u:
                emp_user.set_password('Employee@1234')
                emp_user.save()
            emp.user = emp_user
            emp.save(update_fields=['user'])

        # Link admin to a senior employee so they can test self-service too
        if emp_list:
            emp_list[0].user = admin
            emp_list[0].save(update_fields=['user'])

        if len(emp_list) > 1:
            emp_list[1].user = hr_user
            emp_list[1].save(update_fields=['user'])

        self.stdout.write(self.style.SUCCESS(
            '\n✓ Demo data seeded successfully!\n'
            '  Company : Akosua Tech Ltd\n'
            '  Admin   : admin@akosuatech.gh / Admin@1234\n'
            '  HR      : hr@akosuatech.gh / HR@12345\n'
            '  Employees: Each employee also has a portal login (Employee@1234)\n'
            f'  Total employees: {Employee.objects.filter(company=company).count()}\n'
        ))
