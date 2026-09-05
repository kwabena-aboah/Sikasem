"""apps/payroll/urls.py"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalaryComponentViewSet, SalaryStructureViewSet, EmployeeSalaryViewSet,
    PayrollPeriodViewSet, PayslipViewSet, CustomPayrollRuleViewSet,
)
from .ai_views import AIAdvisorViewSet

router = DefaultRouter()
router.register(r'components',        SalaryComponentViewSet, basename='salary-components')
router.register(r'structures',        SalaryStructureViewSet, basename='salary-structures')
router.register(r'employee-salaries', EmployeeSalaryViewSet,  basename='employee-salaries')
router.register(r'periods',           PayrollPeriodViewSet,   basename='payroll-periods')
router.register(r'payslips',          PayslipViewSet,         basename='payslips')
router.register(r'rules',             CustomPayrollRuleViewSet, basename='payroll-rules')
router.register(r'ai',                AIAdvisorViewSet,       basename='ai-advisor')

urlpatterns = [path('', include(router.urls))]
