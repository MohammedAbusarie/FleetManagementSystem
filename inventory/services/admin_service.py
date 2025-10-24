"""Admin-related business logic"""
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from .base import BaseService
from ..models import UserProfile, ModulePermission, UserPermission
from ..utils.helpers import log_user_action, get_client_ip


class AdminService(BaseService):
    """Service for admin operations"""
    model = UserProfile

    def create_user(self, username, email, password, user_type='normal', created_by=None, **extra_fields):
        """
        Create new user with profile following project patterns
        
        Args:
            username: Username for the new user
            email: Email address
            password: Plain text password
            user_type: Type of user ('super_admin', 'admin', 'normal')
            created_by: User who created this user
            **extra_fields: Additional user fields
            
        Returns:
            tuple: (user, profile) or (None, None) if failed
        """
        try:
            with transaction.atomic():
                # Create Django User
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    **extra_fields
                )
                
                # Create UserProfile
                profile = UserProfile.objects.create(
                    user=user,
                    user_type=user_type,
                    created_by=created_by,
                    is_active=True
                )
                
                # Log the action
                if created_by:
                    log_user_action(
                        user=created_by,
                        action_type='create',
                        module_name='users',
                        object_id=str(user.id),
                        description=f"تم إنشاء مستخدم جديد: {username}",
                        ip_address=get_client_ip(created_by._request) if hasattr(created_by, '_request') else None
                    )
                
                return user, profile
                
        except Exception as e:
            # Log error if needed
            return None, None

    def update_user(self, user, **kwargs):
        """
        Update user and profile information
        
        Args:
            user: User instance to update
            **kwargs: Fields to update
            
        Returns:
            tuple: (user, profile) or (None, None) if failed
        """
        try:
            with transaction.atomic():
                # Update User fields
                user_fields = ['first_name', 'last_name', 'email', 'is_active']
                for field in user_fields:
                    if field in kwargs:
                        setattr(user, field, kwargs[field])
                user.save()
                
                # Update UserProfile fields
                profile_fields = ['user_type', 'is_active']
                profile = user.profile
                for field in profile_fields:
                    if field in kwargs:
                        setattr(profile, field, kwargs[field])
                profile.save()
                
                return user, profile
                
        except Exception as e:
            return None, None

    def soft_delete_user(self, user, deleted_by=None):
        """
        Soft delete user by deactivating profile
        
        Args:
            user: User instance to delete
            deleted_by: User who deleted this user
            
        Returns:
            bool: Success status
        """
        try:
            with transaction.atomic():
                # Deactivate profile instead of deleting
                profile = user.profile
                profile.is_active = False
                profile.save()
                
                # Deactivate Django user
                user.is_active = False
                user.save()
                
                # Log the action
                if deleted_by:
                    log_user_action(
                        user=deleted_by,
                        action_type='delete',
                        module_name='users',
                        object_id=str(user.id),
                        description=f"تم حذف مستخدم: {user.username}",
                        ip_address=get_client_ip(deleted_by._request) if hasattr(deleted_by, '_request') else None
                    )
                
                return True
                
        except Exception as e:
            return False

    def assign_permissions(self, user, permissions_data, assigned_by=None):
        """
        Assign permissions to user
        
        Args:
            user: User instance
            permissions_data: Dict of {module_name: [permission_types]}
            assigned_by: User who assigned permissions
            
        Returns:
            bool: Success status
        """
        try:
            with transaction.atomic():
                # Clear existing permissions
                UserPermission.objects.filter(user=user).delete()
                
                # Assign new permissions
                for module_name, permission_types in permissions_data.items():
                    for permission_type in permission_types:
                        module_permission, created = ModulePermission.objects.get_or_create(
                            module_name=module_name,
                            permission_type=permission_type
                        )
                        
                        UserPermission.objects.create(
                            user=user,
                            module_permission=module_permission,
                            granted=True
                        )
                
                # Log the action
                if assigned_by:
                    log_user_action(
                        user=assigned_by,
                        action_type='permission_change',
                        module_name='users',
                        object_id=str(user.id),
                        description=f"تم تعيين صلاحيات للمستخدم: {user.username}",
                        ip_address=get_client_ip(assigned_by._request) if hasattr(assigned_by, '_request') else None
                    )
                
                return True
                
        except Exception as e:
            return False

    def get_user_permissions_summary(self, user):
        """
        Get user permissions summary
        
        Args:
            user: User instance
            
        Returns:
            dict: Permission summary by module
        """
        try:
            profile = user.profile
            user_type = profile.user_type
            
            # Super admin has all permissions
            if user_type == 'super_admin':
                return {
                    'cars': ['create', 'read', 'update', 'delete'],
                    'equipment': ['create', 'read', 'update', 'delete'],
                    'generic_tables': ['create', 'read', 'update', 'delete']
                }
            
            # Admin has all permissions
            if user_type == 'admin':
                return {
                    'cars': ['create', 'read', 'update', 'delete'],
                    'equipment': ['create', 'read', 'update', 'delete'],
                    'generic_tables': ['create', 'read', 'update', 'delete']
                }
            
            # Normal user - get specific permissions
            permissions = {}
            user_permissions = UserPermission.objects.filter(
                user=user, granted=True
            ).select_related('module_permission')
            
            for user_permission in user_permissions:
                module_name = user_permission.module_permission.module_name
                permission_type = user_permission.module_permission.permission_type
                
                if module_name not in permissions:
                    permissions[module_name] = []
                permissions[module_name].append(permission_type)
            
            return permissions
            
        except Exception:
            return {}

    def validate_user_creation(self, username, email, user_type, created_by):
        """
        Validate user creation permissions
        
        Args:
            username: Username to validate
            email: Email to validate
            user_type: User type to validate
            created_by: User creating the new user
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check if creator has permission
            if not self._can_create_user_type(created_by, user_type):
                return False, "ليس لديك صلاحية لإنشاء هذا النوع من المستخدمين"
            
            # Check if username exists
            if User.objects.filter(username=username).exists():
                return False, "اسم المستخدم موجود بالفعل"
            
            # Check if email exists
            if User.objects.filter(email=email).exists():
                return False, "البريد الإلكتروني موجود بالفعل"
            
            return True, ""
            
        except Exception as e:
            return False, "خطأ في التحقق من صحة البيانات"

    def _can_create_user_type(self, creator, user_type):
        """
        Check if creator can create user of specific type
        
        Args:
            creator: User creating the new user
            user_type: Type of user to create
            
        Returns:
            bool: Can create or not
        """
        try:
            creator_profile = creator.profile
            creator_type = creator_profile.user_type
            
            # Super admin can create anyone
            if creator_type == 'super_admin':
                return True
            
            # Admin can only create normal users
            if creator_type == 'admin' and user_type == 'normal':
                return True
            
            return False
            
        except Exception:
            return False

    def get_users_with_profiles(self, user_type=None, is_active=True):
        """
        Get users with their profiles
        
        Args:
            user_type: Filter by user type
            is_active: Filter by active status
            
        Returns:
            QuerySet: Users with profiles
        """
        queryset = User.objects.select_related('profile')
        
        if is_active:
            queryset = queryset.filter(profile__is_active=True)
        
        if user_type:
            queryset = queryset.filter(profile__user_type=user_type)
        
        return queryset

    def get_user_statistics(self):
        """
        Get user statistics for admin panel
        
        Returns:
            dict: User statistics
        """
        try:
            total_users = UserProfile.objects.filter(is_active=True).count()
            super_admins = UserProfile.objects.filter(user_type='super_admin', is_active=True).count()
            admins = UserProfile.objects.filter(user_type='admin', is_active=True).count()
            normal_users = UserProfile.objects.filter(user_type='normal', is_active=True).count()
            
            return {
                'total_users': total_users,
                'super_admins': super_admins,
                'admins': admins,
                'normal_users': normal_users
            }
            
        except Exception:
            return {
                'total_users': 0,
                'super_admins': 0,
                'admins': 0,
                'normal_users': 0
            }

    def search_users(self, queryset, search_field, search_query):
        """
        Apply search filter to users queryset
        
        Args:
            queryset: Users queryset
            search_field: Field to search in
            search_query: Search query
            
        Returns:
            QuerySet: Filtered queryset
        """
        if not search_query:
            return queryset
        
        if search_field == 'username':
            return queryset.filter(username__icontains=search_query)
        elif search_field == 'email':
            return queryset.filter(email__icontains=search_query)
        elif search_field == 'first_name':
            return queryset.filter(first_name__icontains=search_query)
        elif search_field == 'last_name':
            return queryset.filter(last_name__icontains=search_query)
        elif search_field == 'user_type':
            return queryset.filter(profile__user_type__icontains=search_query)
        else:
            # Fallback to base search method
            return self.search(queryset, search_field, search_query)
