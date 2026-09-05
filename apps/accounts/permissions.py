"""
Accounts App - Permissions
"""
from rest_framework.permissions import BasePermission
from .models import User


class IsCompanyAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN
        ]


class IsHRManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN, User.Role.HR_MANAGER
        ]


class IsPayrollOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN,
            User.Role.HR_MANAGER, User.Role.PAYROLL_OFFICER,
            User.Role.FINANCE_MANAGER
        ]


class IsFinanceManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            User.Role.SUPER_ADMIN, User.Role.COMPANY_ADMIN, User.Role.FINANCE_MANAGER
        ]
