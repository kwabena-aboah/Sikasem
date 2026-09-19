"""
apps/companies/views.py
Fixed: serializers inline, proper company-scoped querysets,
       company resolved from request.user for all mutations.
"""
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Company, Branch, Department, JobGrade, CompanySettings
from apps.accounts.permissions import IsHRManager, IsCompanyAdmin


# ── Serializers ────────────────────────────────────────────────────────────────

class CompanySettingsSerializer(serializers.ModelSerializer):
    # Never send credentials back to the browser after they are saved.
    paystack_secret_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    paystack_secret_key_configured = serializers.SerializerMethodField()

    class Meta:
        model = CompanySettings
        exclude = ['company']
        read_only_fields = ['paystack_secret_key_configured']

    def get_paystack_secret_key_configured(self, obj):
        return bool(obj.paystack_secret_key)

    def update(self, instance, validated_data):
        # An empty password field means “keep the existing secret”, not clear it.
        if not validated_data.get('paystack_secret_key'):
            validated_data.pop('paystack_secret_key', None)
        return super().update(instance, validated_data)


class CompanySerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = '__all__'

    def get_employee_count(self, obj):
        return obj.employees.filter(status__in=['active', 'probation', 'on_leave']).count()


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ['id', 'company']


class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['id', 'company']

    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None

    def get_employee_count(self, obj):
        return obj.employees.filter(status__in=['active', 'probation', 'on_leave']).count()


class JobGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = '__all__'
        read_only_fields = ['id', 'company']


# ── ViewSets ───────────────────────────────────────────────────────────────────

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Only company/super admins may change payment credentials or settings.
        if self.action == 'company_settings' and self.request.method != 'GET':
            return [permissions.IsAuthenticated(), IsCompanyAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        from apps.accounts.models import User
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return Company.objects.all()
        if user.company_id:
            return Company.objects.filter(id=user.company_id)
        return Company.objects.none()

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='settings')
    def company_settings(self, request, pk=None):
        company = self.get_object()
        try:
            s = company.settings
        except CompanySettings.DoesNotExist:
            s = CompanySettings.objects.create(company=company)
        if request.method == 'GET':
            return Response(CompanySettingsSerializer(s).data)
        serializer = CompanySettingsSerializer(s, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return Branch.objects.none()
        return Branch.objects.filter(company_id=user.company_id, is_active=True).order_by('name')

    def perform_create(self, serializer):
        user = self.request.user
        if not user.company:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Your account is not linked to a company.')
        serializer.save(company=user.company)


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return Department.objects.none()
        return Department.objects.filter(
            company_id=user.company_id
        ).select_related('branch', 'head', 'parent').order_by('name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class JobGradeViewSet(viewsets.ModelViewSet):
    serializer_class = JobGradeSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return JobGrade.objects.none()
        return JobGrade.objects.filter(company_id=user.company_id, is_active=True).order_by('name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
