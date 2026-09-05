from django.contrib import admin
from .models import LoanType, Loan, LoanRepayment

@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_amount', 'max_months', 'interest_type', 'company']
    list_filter  = ['company', 'interest_type']

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display  = ['loan_number', 'employee', 'principal_amount', 'status', 'outstanding_balance']
    list_filter   = ['status', 'loan_type__company']
    search_fields = ['loan_number', 'employee__first_name', 'employee__last_name']

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'installment_number', 'due_date', 'amount', 'status']
    list_filter  = ['status']
