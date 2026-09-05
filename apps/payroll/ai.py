"""
Sikasem AI Features
- Payroll anomaly detection
- Compliance advisory
- Payroll forecasting
- Salary benchmarking insights
"""
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class PayrollAnomalyDetector:
    """
    AI-powered anomaly detection for payroll data.
    Uses statistical analysis + OpenAI GPT for explanation.
    """

    THRESHOLDS = {
        'salary_change_pct': 0.30,     # >30% salary change is suspicious
        'gross_vs_previous_pct': 0.25,  # >25% variation from last month
        'paye_vs_gross_min': 0.00,      # Ensure PAYE is calculated
        'overtime_hours_max': 80,        # >80 hours overtime in a month
        'deduction_vs_gross_max': 0.85,  # Deductions >85% of gross is unusual
    }

    def __init__(self, period):
        self.period = period
        self.company = period.company
        self.anomalies = []

    def detect(self) -> list:
        """Run all anomaly checks, return list of anomalies"""
        from .models import Payslip

        payslips = Payslip.objects.filter(
            payroll_period=self.period
        ).select_related('employee')

        for payslip in payslips:
            self._check_payslip(payslip)

        return self.anomalies

    def _check_payslip(self, payslip):
        """Run anomaly checks on individual payslip"""
        issues = []

        # 1. Net pay is negative
        if payslip.net_pay < 0:
            issues.append({
                'type': 'negative_net_pay',
                'severity': 'critical',
                'message': f'Net pay is negative: GHS {payslip.net_pay}'
            })

        # 2. Deductions exceed gross pay
        if payslip.gross_pay > 0:
            deduction_ratio = payslip.total_deductions / payslip.gross_pay
            if deduction_ratio > Decimal(str(self.THRESHOLDS['deduction_vs_gross_max'])):
                issues.append({
                    'type': 'excessive_deductions',
                    'severity': 'high',
                    'message': f'Deductions are {deduction_ratio*100:.1f}% of gross pay'
                })

        # 3. No PAYE on taxable income > threshold
        monthly_personal_relief = Decimal('63.00')
        if payslip.gross_pay > monthly_personal_relief and payslip.paye_tax == 0:
            if not payslip.employee.is_exempt_paye:
                issues.append({
                    'type': 'missing_paye',
                    'severity': 'high',
                    'message': 'No PAYE deducted but employee has taxable income'
                })

        # 4. No SSNIT on non-exempt employee
        if payslip.ssnit_employee == 0 and not payslip.employee.is_exempt_ssnit:
            issues.append({
                'type': 'missing_ssnit',
                'severity': 'medium',
                'message': 'No SSNIT deducted for non-exempt employee'
            })

        # 5. Excessive overtime hours
        if payslip.overtime_hours > self.THRESHOLDS['overtime_hours_max']:
            issues.append({
                'type': 'excessive_overtime',
                'severity': 'medium',
                'message': f'Unusual overtime: {payslip.overtime_hours} hours'
            })

        # 6. Compare with previous month
        prev_payslip = self._get_previous_payslip(payslip)
        if prev_payslip and prev_payslip.gross_pay > 0:
            change = abs(payslip.gross_pay - prev_payslip.gross_pay) / prev_payslip.gross_pay
            if change > Decimal(str(self.THRESHOLDS['gross_vs_previous_pct'])):
                issues.append({
                    'type': 'large_pay_change',
                    'severity': 'medium',
                    'message': f'Gross pay changed by {change*100:.1f}% from last month'
                })

        if issues:
            payslip.is_anomaly = True
            payslip.anomaly_notes = '; '.join(i['message'] for i in issues)
            payslip.save(update_fields=['is_anomaly', 'anomaly_notes'])

            self.anomalies.append({
                'employee_id': str(payslip.employee_id),
                'employee_name': payslip.employee.get_full_name(),
                'payslip_id': str(payslip.id),
                'issues': issues
            })

    def _get_previous_payslip(self, payslip):
        """Get the previous month's payslip for comparison"""
        from .models import Payslip, PayrollPeriod
        prev_period = PayrollPeriod.objects.filter(
            company=self.company,
            period_start__lt=self.period.period_start,
            status__in=['approved', 'paid']
        ).order_by('-period_start').first()

        if prev_period:
            return Payslip.objects.filter(
                payroll_period=prev_period,
                employee=payslip.employee
            ).first()
        return None

    def generate_ai_summary(self) -> str:
        """Use OpenAI to generate a human-readable anomaly report"""
        if not settings.OPENAI_API_KEY or not self.anomalies:
            return ""

        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            anomaly_text = "\n".join([
                f"- {a['employee_name']}: {', '.join(i['message'] for i in a['issues'])}"
                for a in self.anomalies
            ])

            prompt = f"""You are a payroll compliance expert for Ghana. 
Analyze these payroll anomalies detected for {self.company.name}'s {self.period.name} payroll:

{anomaly_text}

Provide a concise summary (3-5 sentences) of:
1. The most critical issues to address immediately
2. Potential compliance risks (PAYE, SSNIT)
3. Recommended next steps

Keep the tone professional and actionable."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI anomaly summary failed: {e}")
            return f"{len(self.anomalies)} anomalies detected. Please review the detailed report."


class PayrollForecaster:
    """
    AI-powered payroll cost forecasting
    """

    def forecast_next_months(self, company, months: int = 3) -> dict:
        """Forecast payroll costs for next N months"""
        from .models import PayrollPeriod, Payslip
        from django.db.models import Avg, Sum
        import json

        # Get last 6 months of data
        recent_periods = PayrollPeriod.objects.filter(
            company=company,
            status__in=['approved', 'paid']
        ).order_by('-period_start')[:6]

        if not recent_periods:
            return {'error': 'Insufficient historical data'}

        historical = []
        for p in recent_periods:
            historical.append({
                'period': p.name,
                'total_gross': float(p.total_gross),
                'total_net': float(p.total_net),
                'employee_count': p.employee_count,
            })

        # Simple trend calculation (can be enhanced with ML)
        avg_gross = sum(h['total_gross'] for h in historical) / len(historical)
        avg_employee_count = sum(h['employee_count'] for h in historical) / len(historical)
        cost_per_employee = avg_gross / max(avg_employee_count, 1)

        # AI-enhanced forecast narrative
        forecast_narrative = self._get_ai_forecast_narrative(historical, company)

        current_employees = company.employees.filter(status='active').count()
        forecasts = []
        today = timezone.now().date()
        for i in range(1, months + 1):
            month = today.replace(day=1)
            # Simple linear projection
            projected_gross = avg_gross * (1 + 0.02 * i)  # Assume 2% monthly growth
            forecasts.append({
                'month_offset': i,
                'projected_gross': round(projected_gross, 2),
                'projected_employees': current_employees,
                'projected_cost_per_employee': round(projected_gross / max(current_employees, 1), 2),
            })

        return {
            'historical': historical,
            'forecasts': forecasts,
            'ai_narrative': forecast_narrative,
            'avg_monthly_cost': round(avg_gross, 2),
        }

    def _get_ai_forecast_narrative(self, historical: list, company) -> str:
        """Get AI narrative for payroll forecast"""
        if not settings.OPENAI_API_KEY:
            return "AI forecast narrative unavailable (API key not configured)."

        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = f"""As a payroll analyst, analyze this payroll cost trend for {company.name} (Ghana):

Historical data (last {len(historical)} months):
{chr(10).join(f"- {h['period']}: GHS {h['total_gross']:,.2f} gross, {h['employee_count']} employees" for h in historical)}

Provide a brief (2-3 sentence) professional analysis noting:
1. Trend direction (growing/stable/declining)
2. Key cost drivers to watch
3. Ghana-specific considerations (SSNIT annual increases, minimum wage changes)"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI forecast narrative failed: {e}")
            return "Forecast generated from historical payroll data."


class ComplianceAdvisor:
    """
    AI-powered Ghana payroll compliance advisor
    """

    SYSTEM_PROMPT = """You are Ama, an AI compliance advisor specializing in Ghana payroll law. 
You have deep knowledge of:
- Ghana Revenue Authority (GRA) PAYE regulations
- SSNIT Act 2008 (Act 766) and amendments
- National Pensions Act 2008 (Act 766)  
- Labour Act 2003 (Act 651) - overtime, leave, termination
- Income Tax Act 2015 (Act 896)
- Electronic Transactions Act

Always cite the relevant law/regulation when giving advice.
Keep answers concise, practical, and actionable.
Use GHS currency and Ghana-specific examples.
If unsure, recommend consulting a qualified Ghanaian tax professional."""

    def ask(self, question: str, company_context: dict = None) -> str:
        """Answer a compliance question"""
        if not settings.OPENAI_API_KEY:
            return "AI compliance advisor unavailable. Please configure OPENAI_API_KEY."

        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            context = ""
            if company_context:
                context = f"\nCompany context: {company_context.get('name', 'N/A')}, " \
                          f"employees: {company_context.get('employee_count', 'N/A')}\n"

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"{context}{question}"}
                ],
                max_tokens=500,
                temperature=0.2
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Compliance advisor error: {e}")
            return "Unable to process compliance query at this time."
