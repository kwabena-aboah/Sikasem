"""
Accounts App - Middleware
"""
from .models import AuditLog


class AuditLogMiddleware:
    """Auto-log sensitive data access"""
    SENSITIVE_PATHS = ['/api/payroll/', '/api/employees/', '/api/reports/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log exports
        if request.path.endswith('/export/') and hasattr(request, 'user') and request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action=AuditLog.Action.EXPORT,
                resource_type=request.path,
                ip_address=request.META.get('REMOTE_ADDR'),
                company=request.user.company,
            )
        return response
