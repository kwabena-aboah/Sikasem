"""
Accounts App - Views (Auth, Users, Audit)
"""
from datetime import timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, AuditLog
from .serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer, AuditLogSerializer


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    email = request.data.get('email', '').lower().strip()
    password = request.data.get('password', '')

    user = authenticate(request, username=email, password=password)

    if not user:
        # Increment failed attempts
        try:
            u = User.objects.get(email=email)
            u.failed_login_attempts += 1
            if u.failed_login_attempts >= 5:
                u.locked_until = timezone.now() + timedelta(minutes=30)
            u.save(update_fields=['failed_login_attempts', 'locked_until'])
        except User.DoesNotExist:
            pass
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if user.is_locked:
        return Response({'error': 'Account locked. Try again later.'}, status=status.HTTP_403_FORBIDDEN)

    # Reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_ip = request.META.get('REMOTE_ADDR')
    user.save(update_fields=['failed_login_attempts', 'locked_until', 'last_login_ip'])

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    # Audit log
    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.LOGIN,
        resource_type='auth',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        company=user.company,
    )

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
        'must_change_password': user.must_change_password,
    })


@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass

    AuditLog.objects.create(
        user=request.user,
        action=AuditLog.Action.LOGOUT,
        resource_type='auth',
        ip_address=request.META.get('REMOTE_ADDR'),
        company=request.user.company,
    )
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
def me_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response({'error': 'Current password is incorrect'}, status=400)

    user.set_password(serializer.validated_data['new_password'])
    user.must_change_password = False
    user.save()

    return Response({'message': 'Password changed successfully'})


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return User.objects.all()
        return User.objects.filter(company=user.company)

    def perform_create(self, serializer):
        user = serializer.save()
        if self.request.user.company:
            user.company = self.request.user.company
            user.save()

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({'is_active': user.is_active})

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Admin reset password - sends email with temp password"""
        import secrets
        user = self.get_object()
        temp_password = secrets.token_urlsafe(10)
        user.set_password(temp_password)
        user.must_change_password = True
        user.save()
        # TODO: Send email with temp_password
        return Response({'message': f'Password reset. Temporary password: {temp_password}'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['action', 'resource_type', 'user']
    search_fields = ['description', 'resource_id']
    ordering_fields = ['timestamp']

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.SUPER_ADMIN:
            return AuditLog.objects.all().select_related('user')
        return AuditLog.objects.filter(company=user.company).select_related('user')
