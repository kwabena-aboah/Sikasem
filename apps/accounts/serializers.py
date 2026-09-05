"""
apps/accounts/serializers.py
Fixed: employee_profile_id added to UserSerializer output so the
       frontend can look up leave balances for the logged-in employee.
"""
from rest_framework import serializers
from .models import User, AuditLog


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, default='')
    branch_name = serializers.CharField(source='branch.name', read_only=True, default='')
    employee_profile_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'company', 'company_name', 'branch', 'branch_name',
            'is_active', 'date_joined', 'profile_photo', 'phone',
            'must_change_password', 'two_factor_enabled',
            'employee_profile_id',
        ]
        read_only_fields = ['id', 'date_joined', 'must_change_password', 'employee_profile_id']

    def get_employee_profile_id(self, obj):
        try:
            return str(obj.employee_profile.id)
        except Exception:
            return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name',
            'role', 'company', 'branch', 'phone'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.must_change_password = True
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, default='')

    class Meta:
        model = AuditLog
        fields = '__all__'
