# Sikasem — Payroll Management System
### by Sikaba Systems

A full-featured, Ghana-compliant payroll management platform built with Django, Django REST Framework, Vue 3, and Bootstrap 5.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x + Django REST Framework |
| Frontend | Vue 3 (Composition API) + Bootstrap 5 |
| Database | PostgreSQL (recommended) / SQLite (dev) |
| Auth | JWT (djangorestframework-simplejwt) |
| Tasks | Celery + Redis |
| AI | OpenAI GPT-4 API (anomaly detection, payroll advisory) |
| PDF | WeasyPrint |
| Payments | Paystack API |

---

## Features

1. **Employee Management** — Full employee lifecycle, org charts, departments, job grades
2. **Salary Structure Setup** — Flexible components: basic, allowances, deductions
3. **Time & Attendance** — Clock-in/out, shifts, overtime, integrations
4. **Automated Payroll Calculation** — PAYE, SSNIT, pension, loans, penalties
5. **Tax & Compliance** — Ghana Revenue Authority tax tables, SSNIT Tier 1/2/3
6. **Payslip Generation** — PDF payslips with company branding
7. **Payment Processing** — Paystack integration, bulk bank transfers
8. **Reporting & Analytics** — Cost analysis, tax reports, dashboards
9. **Leave & Benefits Management** — Annual, sick, maternity leave; benefits tracking
10. **Security & Access Control** — Role-based permissions (RBAC), audit logs
11. **Employee Self-Service** — Portal for payslips, leave applications, profile updates
12. **Loan & Advance Management** — Loan applications, repayment schedules
13. **Multi-Company/Multi-Branch** — Full tenant isolation per company
14. **Custom Rules Engine** — Conditional bonuses, custom deductions, tax treatment rules
15. **AI Features** — Anomaly detection, payroll forecasting, compliance advisor

---

## Quick Start

```bash
# 1. Clone and setup
cd sikasem
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your DB, Redis, Paystack, OpenAI credentials

# 3. Database
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_ghana_tax_tables  # Load GRA tax tables
python manage.py seed_ssnit_rates       # Load SSNIT/pension rates

# 4. Run
python manage.py runserver

# 5. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Ghana Payroll Compliance

### PAYE Tax Bands (2024)
| Annual Income (GHS) | Rate |
|---|---|
| 0 – 4,380 | 0% |
| 4,381 – 5,580 | 5% |
| 5,581 – 6,780 | 10% |
| 6,781 – 42,780 | 17.5% |
| 42,781 – 240,000 | 25% |
| Above 240,000 | 30% |

### SSNIT Contributions
- **Employee:** 5.5% of basic salary
- **Employer:** 13% of basic salary (10% SSNIT + 2.5% Tier 2)
- **Tier 3 (voluntary):** Employer & employee negotiated rates

### Pension (NPRA)
- Tier 1: SSNIT (mandatory)
- Tier 2: Mandatory occupational pension (2.5% employer)
- Tier 3: Voluntary provident fund

---

## Project Structure

```
sikasem/
├── manage.py
├── requirements.txt
├── .env.example
├── sikasem/              # Django project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── accounts/         # Auth, users, roles, permissions
│   ├── companies/        # Multi-company, branches, departments
│   ├── employees/        # Employee profiles, contracts, documents
│   ├── payroll/          # Salary structures, payroll runs, payslips
│   ├── attendance/       # Time tracking, shifts, overtime
│   ├── leaves/           # Leave types, applications, balances
│   ├── loans/            # Loan management, repayments
│   ├── reports/          # Analytics, exports, dashboards
│   └── notifications/    # Email, SMS, in-app notifications
└── frontend/             # Vue 3 SPA
    ├── src/
    │   ├── views/        # Page components
    │   ├── components/   # Reusable UI components
    │   ├── stores/       # Pinia stores
    │   └── utils/        # API client, formatters
    └── index.html
```
