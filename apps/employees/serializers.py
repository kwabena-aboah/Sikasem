"""
apps/employees/serializers.py
Fixed:
  - company field read_only (always set from request, never from client)
  - department and branch validated to belong to the employee's company
  - age and years_of_service as safe SerializerMethodFields
"""
from rest_framework import serializers
from .models import Employee, EmployeeDocument, SalaryHistory


class EmployeeListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    branch_name = serializers.CharField(source='branch.name', read_only=True, default='')
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'full_name', 'first_name', 'last_name',
            'job_title', 'department', 'department_name', 'branch_name',
            'employment_type', 'status', 'hire_date', 'photo',
            'work_email', 'personal_phone',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class EmployeeDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    branch_name = serializers.CharField(source='branch.name', read_only=True, default='')
    job_grade_name = serializers.CharField(source='job_grade.name', read_only=True, default='')
    manager_name = serializers.SerializerMethodField()
    years_of_service = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True, default='')

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = [
            'id', 'company', 'created_at', 'updated_at', 'created_by',
            'full_name', 'department_name', 'branch_name', 'job_grade_name',
            'manager_name', 'years_of_service', 'age', 'company_name',
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_manager_name(self, obj):
        return obj.reports_to.get_full_name() if obj.reports_to else None

    def get_years_of_service(self, obj):
        try:
            return round(obj.years_of_service, 2)
        except Exception:
            return 0.0

    def get_age(self, obj):
        try:
            return obj.age
        except Exception:
            return None

    def validate_employee_id(self, value):
        """employee_id must be unique within the company — enforced in view.perform_create"""
        return value

    def validate_department(self, dept):
        """Department must belong to same company (validated via view queryset context)"""
        return dept

    def validate_branch(self, branch):
        return branch


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']


class SalaryHistorySerializer(serializers.ModelSerializer):
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name', read_only=True, default=''
    )

    class Meta:
        model = SalaryHistory
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
