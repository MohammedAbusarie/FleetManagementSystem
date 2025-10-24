"""RBAC-related business logic"""
from django.contrib.auth.models import User
from django.utils import timezone
from .base import BaseService
from ..models import UserProfile, ModulePermission, UserPermission, LoginLog, ActionLog


class UserProfileService(BaseService):
    """Service for UserProfile operations"""
    model = UserProfile

    def get_user_profile(self, user):
        """Get or create user profile"""
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'user_type': 'normal',
                'is_active': True
            }
        )
        return profile

    def get_user_type(self, user):
        """Get user type with fallback to current system"""
        try:
            profile = user.profile
            return profile.get_user_type()
        except UserProfile.DoesNotExist:
            # Fallback to current system
            if user.groups.filter(name='Admin').exists() or user.is_superuser:
                return 'admin'
            return 'normal'

    def is_super_admin(self, user):
        """Check if user is super admin"""
        try:
            profile = user.profile
            return profile.is_super_admin()
        except UserProfile.DoesNotExist:
            return user.is_superuser

    def is_admin_user(self, user):
        """Check if user is admin (including super admin)"""
        try:
            profile = user.profile
            return profile.is_admin_user()
        except UserProfile.DoesNotExist:
            return user.groups.filter(name='Admin').exists() or user.is_superuser

    def create_user_profile(self, user, user_type='normal', created_by=None):
        """Create new user profile"""
        return UserProfile.objects.create(
            user=user,
            user_type=user_type,
            created_by=created_by,
            is_active=True
        )

    def update_user_profile(self, user, **kwargs):
        """Update user profile"""
        try:
            profile = user.profile
            for key, value in kwargs.items():
                setattr(profile, key, value)
            profile.save()
            return profile
        except UserProfile.DoesNotExist:
            return None

    def get_active_users(self):
        """Get all active users with profiles"""
        return User.objects.filter(
            profile__is_active=True
        ).select_related('profile')

    def get_users_by_type(self, user_type):
        """Get users by type"""
        return User.objects.filter(
            profile__user_type=user_type,
            profile__is_active=True
        ).select_related('profile')


class PermissionService(BaseService):
    """Service for permission operations"""
    model = ModulePermission

    def get_module_permissions(self, module_name):
        """Get all permissions for a module"""
        return ModulePermission.objects.filter(module_name=module_name)

    def get_user_permissions(self, user):
        """Get all permissions for a user"""
        return UserPermission.objects.filter(user=user).select_related('module_permission')

    def has_permission(self, user, module_name, permission_type):
        """Check if user has specific permission"""
        # Check if user is super admin
        if UserProfileService().is_super_admin(user):
            return True

        # Check if user is admin (has all permissions)
        if UserProfileService().is_admin_user(user):
            return True

        # Check specific permission
        try:
            user_permission = UserPermission.objects.get(
                user=user,
                module_permission__module_name=module_name,
                module_permission__permission_type=permission_type
            )
            return user_permission.granted
        except UserPermission.DoesNotExist:
            return False

    def grant_permission(self, user, module_name, permission_type):
        """Grant permission to user"""
        module_permission, created = ModulePermission.objects.get_or_create(
            module_name=module_name,
            permission_type=permission_type
        )

        user_permission, created = UserPermission.objects.get_or_create(
            user=user,
            module_permission=module_permission,
            defaults={'granted': True}
        )

        if not created:
            user_permission.granted = True
            user_permission.save()

        return user_permission

    def revoke_permission(self, user, module_name, permission_type):
        """Revoke permission from user"""
        try:
            user_permission = UserPermission.objects.get(
                user=user,
                module_permission__module_name=module_name,
                module_permission__permission_type=permission_type
            )
            user_permission.granted = False
            user_permission.save()
            return user_permission
        except UserPermission.DoesNotExist:
            return None

    def get_user_module_permissions(self, user, module_name):
        """Get all permissions for a user in a specific module"""
        return UserPermission.objects.filter(
            user=user,
            module_permission__module_name=module_name
        ).select_related('module_permission')


class LoggingService(BaseService):
    """Service for logging operations"""
    model = ActionLog

    def log_login(self, user, ip_address, user_agent, success=True):
        """Log user login"""
        return LoginLog.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )

    def log_logout(self, user, ip_address=None):
        """Log user logout"""
        try:
            login_log = LoginLog.objects.filter(
                user=user,
                logout_time__isnull=True
            ).order_by('-login_time').first()

            if login_log:
                login_log.logout_time = timezone.now()
                login_log.save()
                return login_log
        except Exception:
            pass
        return None

    def log_action(self, user, action_type, module_name=None, object_id=None, description="", ip_address=None):
        """Log user action"""
        return ActionLog.objects.create(
            user=user,
            action_type=action_type,
            module_name=module_name,
            object_id=object_id,
            description=description,
            ip_address=ip_address
        )

    def get_user_login_history(self, user, limit=50):
        """Get user login history"""
        return LoginLog.objects.filter(user=user).order_by('-login_time')[:limit]

    def get_user_action_history(self, user, limit=50):
        """Get user action history"""
        return ActionLog.objects.filter(user=user).order_by('-timestamp')[:limit]

    def get_recent_logins(self, limit=100):
        """Get recent login attempts"""
        return LoginLog.objects.select_related('user').order_by('-login_time')[:limit]

    def get_recent_actions(self, limit=100):
        """Get recent system actions"""
        return ActionLog.objects.select_related('user').order_by('-timestamp')[:limit]
