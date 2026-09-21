"""apps/attendance/urls.py — Fixed: proper imports, no __import__ hacks"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from .models import AttendanceRecord, Shift, PublicHoliday
from apps.accounts.permissions import IsHRManager


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'
        read_only_fields = ['id', 'company']


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_num = serializers.CharField(source='employee.employee_id', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ['id']


class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = '__all__'
        read_only_fields = ['id', 'company']


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'date', 'status']
    ordering = ['-date']

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return AttendanceRecord.objects.none()

        qs = AttendanceRecord.objects.filter(
            employee__company_id=user.company_id
        ).select_related('employee', 'shift')

        # Role scoping
        if user.role == 'employee':
            if hasattr(user, 'employee_profile'):
                qs = qs.filter(employee=user.employee_profile)
            else:
                return AttendanceRecord.objects.none()
        elif user.role == 'branch_manager' and user.branch_id:
            qs = qs.filter(employee__branch_id=user.branch_id)

        employee_id = self.request.query_params.get('employee_id')
        month       = self.request.query_params.get('month')
        year        = self.request.query_params.get('year')

        if employee_id and user.role != 'employee':
            qs = qs.filter(employee_id=employee_id)
        if month and year:
            qs = qs.filter(date__month=int(month), date__year=int(year))

        return qs.order_by('-date')

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        from apps.employees.models import Employee
        from rest_framework.exceptions import PermissionDenied
        if request.user.role not in ['super_admin', 'company_admin', 'hr_manager']:
            raise PermissionDenied("Only HR and administrators can import attendance records.")

        records = request.data.get('records', [])
        created = 0
        errors  = []

        for r in records:
            try:
                emp_ident = str(r.get('employee_id', '')).strip()
                if not emp_ident:
                    errors.append({'record': r, 'error': 'Missing employee_id'})
                    continue

                employee = Employee.objects.filter(
                    Q(employee_id=emp_ident) | Q(id=emp_ident if len(emp_ident) == 36 else None),
                    company=request.user.company
                ).first()

                if not employee:
                    errors.append({'record': r, 'error': f"Employee '{emp_ident}' not found"})
                    continue

                AttendanceRecord.objects.update_or_create(
                    employee=employee,
                    date=r['date'],
                    defaults={
                        'status':    r.get('status', 'present'),
                        'clock_in':  r.get('clock_in') or None,
                        'clock_out': r.get('clock_out') or None,
                        'is_manual': True,
                    }
                )
                created += 1
            except Exception as e:
                errors.append({'record': r, 'error': str(e)})

        return Response({'imported': created, 'errors': errors})

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        import datetime
        user  = request.user
        if not user.company_id:
            return Response([])

        month = int(request.query_params.get('month', datetime.date.today().month))
        year  = int(request.query_params.get('year',  datetime.date.today().year))

        att_filter = Q(
            employee__company_id=user.company_id,
            date__month=month,
            date__year=year,
        )

        if user.role == 'employee':
            if hasattr(user, 'employee_profile'):
                att_filter &= Q(employee=user.employee_profile)
            else:
                return Response([])
        elif user.role == 'branch_manager' and user.branch_id:
            att_filter &= Q(employee__branch_id=user.branch_id)

        data = (
            AttendanceRecord.objects
            .filter(att_filter)
            .values('employee__id', 'employee__first_name', 'employee__last_name')
            .annotate(
                present=Count('id', filter=Q(status='present')),
                absent =Count('id', filter=Q(status='absent')),
                late   =Count('id', filter=Q(status='late')),
                leave  =Count('id', filter=Q(status='leave')),
                overtime_total=Sum('overtime_hours'),
            )
        )
        return Response(list(data))


class ShiftViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        if not user.company_id:
            return Shift.objects.none()
        return Shift.objects.filter(company_id=user.company_id).order_by('name')

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class PublicHolidayViewSet(viewsets.ModelViewSet):
    serializer_class = PublicHolidaySerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get_queryset(self):
        user = self.request.user
        return PublicHoliday.objects.filter(
            Q(is_national=True, country='GH') | Q(company_id=user.company_id)
        ).order_by('date')


router = DefaultRouter()
router.register(r'records',   AttendanceViewSet,    basename='attendance')
router.register(r'shifts',    ShiftViewSet,         basename='shifts')
router.register(r'holidays',  PublicHolidayViewSet, basename='holidays')
urlpatterns = [path('', include(router.urls))]
