from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog, Permission, RolePermission

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'first_name', 'last_name', 'role', 'company', 'is_active']
    list_filter   = ['role', 'is_active', 'company']
    search_fields = ['email', 'first_name', 'last_name']
    ordering      = ['email']
    fieldsets     = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'profile_photo')}),
        ('Organization', {'fields': ('role', 'company', 'branch')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'must_change_password')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role', 'company')}),
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'resource_type', 'ip_address', 'timestamp']
    list_filter   = ['action', 'resource_type']
    search_fields = ['user__email', 'description']
    readonly_fields = ['user', 'action', 'resource_type', 'resource_id', 'ip_address', 'timestamp', 'changes']
