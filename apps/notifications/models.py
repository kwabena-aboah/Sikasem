"""notifications/models.py"""
from django.db import models
import uuid


class Notification(models.Model):
    class NotifType(models.TextChoices):
        PAYSLIP = 'payslip', 'Payslip Ready'
        LEAVE = 'leave', 'Leave Update'
        LOAN = 'loan', 'Loan Update'
        PAYROLL = 'payroll', 'Payroll Update'
        SYSTEM = 'system', 'System'
        ALERT = 'alert', 'Alert'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=NotifType.choices, default=NotifType.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
