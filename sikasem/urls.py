"""
Sikasem URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from apps.payroll.views import paystack_webhook
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/auth/', include('apps.accounts.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Core APIs
    path('api/companies/', include('apps.companies.urls')),
    path('api/employees/', include('apps.employees.urls')),
    path('api/payroll/', include('apps.payroll.urls')),
    path('api/payroll/paystack/webhook/', paystack_webhook, name='paystack-webhook'),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/leaves/', include('apps.leaves.urls')),
    path('api/loans/', include('apps.loans.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
