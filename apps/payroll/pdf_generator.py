"""
Payslip PDF Generator
Generates branded, professional payslips using WeasyPrint
"""
from django.template.loader import render_to_string
from django.conf import settings
import io

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False


PAYSLIP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
  
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  body {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 10px;
    color: #1a1a2e;
    background: white;
  }
  
  .payslip {
    width: 210mm;
    min-height: 297mm;
    padding: 12mm 14mm;
  }
  
  /* Header */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 3px solid #0d47a1;
    padding-bottom: 8px;
    margin-bottom: 12px;
  }
  
  .company-name {
    font-size: 18px;
    font-weight: 600;
    color: #0d47a1;
    letter-spacing: -0.3px;
  }
  
  .company-details { font-size: 8.5px; color: #555; line-height: 1.6; }
  
  .payslip-title {
    text-align: right;
  }
  
  .payslip-title h2 {
    font-size: 14px;
    font-weight: 600;
    color: #0d47a1;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .payslip-title .period {
    font-size: 11px;
    color: #555;
    margin-top: 2px;
  }
  
  .payslip-id {
    font-size: 8px;
    color: #888;
    margin-top: 4px;
    font-family: monospace;
  }
  
  /* Employee info */
  .employee-section {
    background: #f0f4ff;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 14px;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
  }
  
  .info-item label {
    font-size: 7.5px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: block;
  }
  
  .info-item value {
    font-size: 10px;
    font-weight: 500;
    color: #1a1a2e;
    display: block;
    margin-top: 1px;
  }
  
  /* Earnings / Deductions table */
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
  }
  
  .section-title {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 5px 8px;
    border-radius: 4px 4px 0 0;
    margin-bottom: 0;
  }
  
  .earnings .section-title { background: #e8f5e9; color: #1b5e20; }
  .deductions .section-title { background: #fce4ec; color: #880e4f; }
  
  .line-items { width: 100%; border-collapse: collapse; }
  
  .line-items td {
    padding: 4px 8px;
    font-size: 9.5px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .line-items .amount { text-align: right; font-weight: 500; }
  .line-items .total-row td {
    font-weight: 600;
    font-size: 10px;
    border-top: 2px solid #ddd;
    border-bottom: none;
    padding-top: 6px;
  }
  
  .earnings .total-row td { color: #1b5e20; }
  .deductions .total-row td { color: #880e4f; }
  
  /* Net pay box */
  .net-pay-box {
    background: #0d47a1;
    color: white;
    border-radius: 8px;
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }
  
  .net-pay-box .label {
    font-size: 11px;
    font-weight: 500;
    opacity: 0.85;
  }
  
  .net-pay-box .amount {
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.5px;
  }
  
  .net-pay-box .currency { font-size: 13px; opacity: 0.7; }
  
  /* Attendance */
  .attendance-section {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-bottom: 14px;
  }
  
  .att-item {
    text-align: center;
    background: #f8f9fa;
    border-radius: 6px;
    padding: 8px 4px;
  }
  
  .att-item .num {
    font-size: 16px;
    font-weight: 600;
    color: #0d47a1;
  }
  
  .att-item .lbl {
    font-size: 7.5px;
    color: #888;
    text-transform: uppercase;
    margin-top: 2px;
  }
  
  /* Employer contributions */
  .employer-section {
    background: #fff8e1;
    border: 1px solid #ffecb3;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 12px;
  }
  
  .employer-section h4 {
    font-size: 9px;
    color: #f57f17;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  
  .employer-row {
    display: flex;
    justify-content: space-between;
    font-size: 9.5px;
    padding: 2px 0;
  }
  
  /* Footer */
  .footer {
    border-top: 1px solid #eee;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    font-size: 8px;
    color: #aaa;
  }
  
  .confidential {
    text-align: center;
    font-size: 7.5px;
    color: #ccc;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }
</style>
</head>
<body>
<div class="payslip">
  
  <!-- Header -->
  <div class="header">
    <div>
      <div class="company-name">{{ company_name }}</div>
      <div class="company-details">
        {{ company_address }}<br>
        TIN: {{ company_tin }} | SSNIT Employer Code: {{ ssnit_code }}
      </div>
    </div>
    <div class="payslip-title">
      <h2>Pay Slip</h2>
      <div class="period">{{ period_start }} – {{ period_end }}</div>
      <div class="payslip-id">REF: {{ payslip_id }}</div>
    </div>
  </div>
  
  <!-- Employee Info -->
  <div class="employee-section">
    <div class="info-item"><label>Employee Name</label><value>{{ employee_name }}</value></div>
    <div class="info-item"><label>Employee ID</label><value>{{ employee_id }}</value></div>
    <div class="info-item"><label>Department</label><value>{{ department }}</value></div>
    <div class="info-item"><label>Job Title</label><value>{{ job_title }}</value></div>
    <div class="info-item"><label>TIN</label><value>{{ employee_tin }}</value></div>
    <div class="info-item"><label>SSNIT Number</label><value>{{ employee_ssnit }}</value></div>
    <div class="info-item"><label>Bank</label><value>{{ bank_name }}</value></div>
    <div class="info-item"><label>Account</label><value>{{ account_number }}</value></div>
    <div class="info-item"><label>Pay Date</label><value>{{ pay_date }}</value></div>
  </div>
  
  <!-- Attendance Summary -->
  <div class="attendance-section">
    <div class="att-item">
      <div class="num">{{ working_days }}</div>
      <div class="lbl">Working Days</div>
    </div>
    <div class="att-item">
      <div class="num">{{ days_present }}</div>
      <div class="lbl">Present</div>
    </div>
    <div class="att-item">
      <div class="num">{{ days_absent }}</div>
      <div class="lbl">Absent</div>
    </div>
    <div class="att-item">
      <div class="num">{{ leave_days }}</div>
      <div class="lbl">Leave</div>
    </div>
    <div class="att-item">
      <div class="num">{{ overtime_hours }}</div>
      <div class="lbl">OT Hours</div>
    </div>
  </div>
  
  <!-- Earnings and Deductions -->
  <div class="columns">
    <div class="earnings">
      <div class="section-title">Earnings</div>
      <table class="line-items">
        {% for item in earnings %}
        <tr>
          <td>{{ item.name }}</td>
          <td class="amount">GHS {{ item.amount }}</td>
        </tr>
        {% endfor %}
        <tr class="total-row">
          <td>GROSS PAY</td>
          <td class="amount">GHS {{ gross_pay }}</td>
        </tr>
      </table>
    </div>
    
    <div class="deductions">
      <div class="section-title">Deductions</div>
      <table class="line-items">
        <tr><td>PAYE Tax</td><td class="amount">GHS {{ paye_tax }}</td></tr>
        <tr><td>SSNIT (5.5%)</td><td class="amount">GHS {{ ssnit_employee }}</td></tr>
        {% if tier3_employee %}<tr><td>Tier 3 Pension</td><td class="amount">GHS {{ tier3_employee }}</td></tr>{% endif %}
        {% if loan_repayment %}<tr><td>Loan Repayment</td><td class="amount">GHS {{ loan_repayment }}</td></tr>{% endif %}
        {% if late_penalty %}<tr><td>Late Penalty</td><td class="amount">GHS {{ late_penalty }}</td></tr>{% endif %}
        {% for item in other_deductions %}
        <tr><td>{{ item.name }}</td><td class="amount">GHS {{ item.amount }}</td></tr>
        {% endfor %}
        <tr class="total-row">
          <td>TOTAL DEDUCTIONS</td>
          <td class="amount">GHS {{ total_deductions }}</td>
        </tr>
      </table>
    </div>
  </div>
  
  <!-- Net Pay -->
  <div class="net-pay-box">
    <div>
      <div class="label">Net Pay</div>
      <div style="font-size: 8.5px; opacity: 0.6; margin-top: 2px;">Payment to: {{ bank_name }} • {{ account_number }}</div>
    </div>
    <div>
      <span class="currency">GHS </span>
      <span class="amount">{{ net_pay }}</span>
    </div>
  </div>
  
  <!-- Employer Contributions (informational) -->
  <div class="employer-section">
    <h4>Employer Contributions (Not deducted from your pay)</h4>
    <div class="employer-row"><span>SSNIT Employer (10.5%)</span><span>GHS {{ ssnit_employer }}</span></div>
    <div class="employer-row"><span>Tier 2 Employer (2.5%)</span><span>GHS {{ tier2_employer }}</span></div>
    <div class="employer-row" style="font-weight:600; border-top: 1px solid #ffecb3; padding-top:4px; margin-top:4px;">
      <span>Total Employer Cost</span><span>GHS {{ total_employer_cost }}</span>
    </div>
  </div>
  
  <!-- Footer -->
  <div class="confidential">Confidential — For Recipient Eyes Only</div>
  <div class="footer">
    <span>Generated by Sikasem Payroll System | Sikaba Systems</span>
    <span>{{ generated_at }}</span>
  </div>
  
</div>
</body>
</html>
"""


def generate_payslip_pdf(payslip) -> bytes:
    """Generate a PDF payslip and return as bytes"""
    from decimal import Decimal
    from datetime import datetime

    def fmt(val):
        return f"{float(val):,.2f}"

    context = {
        'company_name': payslip.payroll_period.company.name,
        'company_address': payslip.payroll_period.company.address or 'Ghana',
        'company_tin': payslip.payroll_period.company.tin or 'N/A',
        'ssnit_code': payslip.payroll_period.company.ssnit_employer_code or 'N/A',
        'payslip_id': str(payslip.id)[:8].upper(),
        'period_start': payslip.payroll_period.period_start.strftime('%d %b %Y'),
        'period_end': payslip.payroll_period.period_end.strftime('%d %b %Y'),
        'pay_date': payslip.payroll_period.pay_date.strftime('%d %b %Y'),
        'employee_name': payslip.employee.get_full_name(),
        'employee_id': payslip.employee.employee_id,
        'department': payslip.employee.department.name if payslip.employee.department else 'N/A',
        'job_title': payslip.employee.job_title,
        'employee_tin': payslip.employee.tin or 'N/A',
        'employee_ssnit': payslip.employee.ssnit_number or 'N/A',
        'bank_name': payslip.employee.bank_name or 'Mobile Money',
        'account_number': payslip.employee.account_number or payslip.employee.mobile_money_number or 'N/A',
        'working_days': payslip.working_days,
        'days_present': payslip.days_present,
        'days_absent': payslip.days_absent,
        'leave_days': payslip.leave_days,
        'overtime_hours': float(payslip.overtime_hours),
        'earnings': payslip.earnings_breakdown,
        'gross_pay': fmt(payslip.gross_pay),
        'paye_tax': fmt(payslip.paye_tax),
        'ssnit_employee': fmt(payslip.ssnit_employee),
        'tier3_employee': fmt(payslip.tier3_employee) if payslip.tier3_employee > 0 else None,
        'loan_repayment': fmt(payslip.loan_repayment) if payslip.loan_repayment > 0 else None,
        'late_penalty': fmt(payslip.late_penalty) if payslip.late_penalty > 0 else None,
        'other_deductions': [d for d in payslip.deductions_breakdown if d.get('code') not in ('PAYE', 'SSNIT_EMP', 'TIER3', 'LOAN', 'LATE')],
        'total_deductions': fmt(payslip.total_deductions),
        'net_pay': fmt(payslip.net_pay),
        'ssnit_employer': fmt(payslip.ssnit_employer),
        'tier2_employer': fmt(payslip.tier2_employer),
        'total_employer_cost': fmt(payslip.ssnit_employer + payslip.tier2_employer),
        'generated_at': datetime.now().strftime('%d %b %Y %H:%M'),
    }

    # Render HTML with Django Template engine to properly execute {% for %}, {% if %}, etc.
    from django.template import Template, Context
    template = Template(PAYSLIP_HTML_TEMPLATE)
    html_content = template.render(Context(context))

    if WEASYPRINT_AVAILABLE:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    else:
        # Return HTML as fallback (for dev without WeasyPrint)
        return html_content.encode('utf-8')
