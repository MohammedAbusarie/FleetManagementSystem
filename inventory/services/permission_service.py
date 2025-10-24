"""Permission-related business logic"""
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Count
from .base import BaseService
from ..models import ModulePermission, UserPermission, UserProfile
from ..utils.helpers import log_user_action, get_client_ip


class PermissionService(BaseService):
    """Service for permission operations"""
    model = ModulePermission

    def get_module_permissions(self, module_name):
        """
        Get all permissions for a module
        
        Args:
            module_name: Name of the module
            
        Returns:
            QuerySet: Module permissions
        """
        try:
            return ModulePermission.objects.filter(module_name=module_name)
        except Exception:
            return ModulePermission.objects.none()

    def get_user_permissions(self, user):
        """
        Get all permissions for a user
        
        Args:
            user: User instance
            
        Returns:
            QuerySet: User permissions
        """
        try:
            return UserPermission.objects.filter(user=user).select_related('module_permission')
        except Exception:
            return UserPermission.objects.none()

    def has_permission(self, user, module_name, permission_type):
        """
        Check if user has specific permission with fallback to current system
        
        Args:
            user: User instance
            module_name: Name of the module
            permission_type: Type of permission
            
        Returns:
            bool: Has permission or not
        """
        try:
            # Check if user is super admin
            if self._is_super_admin(user):
                return True

            # Check if user is admin (has all permissions)
            if self._is_admin_user(user):
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
                
        except Exception:
            # Fallback to current system
            return user.groups.filter(name='Admin').exists() or user.is_superuser

    def grant_permission(self, user, module_name, permission_type, granted_by=None):
        """
        Grant permission to user
        
        Args:
            user: User instance
            module_name: Name of the module
            permission_type: Type of permission
            granted_by: User who granted the permission
            
        Returns:
            UserPermission: Created or updated permission
        """
        try:
            with transaction.atomic():
                # Get or create module permission
                module_permission, created = ModulePermission.objects.get_or_create(
                    module_name=module_name,
                    permission_type=permission_type
                )

                # Get or create user permission
                user_permission, created = UserPermission.objects.get_or_create(
                    user=user,
                    module_permission=module_permission,
                    defaults={'granted': True}
                )

                if not created:
                    user_permission.granted = True
                    user_permission.save()

                # Log the action
                if granted_by:
                    log_user_action(
                        user=granted_by,
                        action_type='permission_change',
                        module_name='permissions',
                        object_id=str(user_permission.id),
                        description=f"تم منح صلاحية {permission_type} للوحدة {module_name} للمستخدم {user.username}",
                        ip_address=get_client_ip(granted_by._request) if hasattr(granted_by, '_request') else None
                    )

                return user_permission
                
        except Exception as e:
            return None

    def revoke_permission(self, user, module_name, permission_type, revoked_by=None):
        """
        Revoke permission from user
        
        Args:
            user: User instance
            module_name: Name of the module
            permission_type: Type of permission
            revoked_by: User who revoked the permission
            
        Returns:
            UserPermission: Updated permission or None
        """
        try:
            with transaction.atomic():
                user_permission = UserPermission.objects.get(
                    user=user,
                    module_permission__module_name=module_name,
                    module_permission__permission_type=permission_type
                )
                
                user_permission.granted = False
                user_permission.save()

                # Log the action
                if revoked_by:
                    log_user_action(
                        user=revoked_by,
                        action_type='permission_change',
                        module_name='permissions',
                        object_id=str(user_permission.id),
                        description=f"تم سحب صلاحية {permission_type} للوحدة {module_name} من المستخدم {user.username}",
                        ip_address=get_client_ip(revoked_by._request) if hasattr(revoked_by, '_request') else None
                    )

                return user_permission
                
        except UserPermission.DoesNotExist:
            return None
        except Exception as e:
            return None

    def get_user_module_permissions(self, user, module_name):
        """
        Get all permissions for a user in a specific module
        
        Args:
            user: User instance
            module_name: Name of the module
            
        Returns:
            QuerySet: User permissions for the module
        """
        try:
            return UserPermission.objects.filter(
                user=user,
                module_permission__module_name=module_name
            ).select_related('module_permission')
        except Exception:
            return UserPermission.objects.none()

    def assign_module_permissions(self, user, module_name, permission_types, assigned_by=None):
        """
        Assign multiple permissions for a module to user
        
        Args:
            user: User instance
            module_name: Name of the module
            permission_types: List of permission types
            assigned_by: User who assigned permissions
            
        Returns:
            list: List of created/updated permissions
        """
        try:
            with transaction.atomic():
                permissions = []
                
                for permission_type in permission_types:
                    permission = self.grant_permission(
                        user, module_name, permission_type, assigned_by
                    )
                    if permission:
                        permissions.append(permission)
                
                return permissions
                
        except Exception:
            return []

    def revoke_module_permissions(self, user, module_name, permission_types, revoked_by=None):
        """
        Revoke multiple permissions for a module from user
        
        Args:
            user: User instance
            module_name: Name of the module
            permission_types: List of permission types
            revoked_by: User who revoked permissions
            
        Returns:
            list: List of updated permissions
        """
        try:
            with transaction.atomic():
                permissions = []
                
                for permission_type in permission_types:
                    permission = self.revoke_permission(
                        user, module_name, permission_type, revoked_by
                    )
                    if permission:
                        permissions.append(permission)
                
                return permissions
                
        except Exception:
            return []

    def get_user_permissions_summary(self, user):
        """
        Get user permissions summary by module
        
        Args:
            user: User instance
            
        Returns:
            dict: Permission summary by module
        """
        try:
            # Check user type first
            user_type = self._get_user_type(user)
            
            # Super admin and admin have all permissions
            if user_type in ['super_admin', 'admin']:
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

    def validate_permission_assignment(self, user, module_name, permission_types, assigned_by):
        """
        Validate permission assignment
        
        Args:
            user: User instance
            module_name: Name of the module
            permission_types: List of permission types
            assigned_by: User assigning permissions
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check if assigner has permission to assign permissions
            if not self._can_assign_permissions(assigned_by):
                return False, "ليس لديك صلاحية لتعيين الصلاحيات"
            
            # Check if target user can receive permissions
            if not self._can_receive_permissions(user):
                return False, "لا يمكن تعيين صلاحيات لهذا المستخدم"
            
            # Validate permission types
            valid_permissions = ['create', 'read', 'update', 'delete']
            for permission_type in permission_types:
                if permission_type not in valid_permissions:
                    return False, f"نوع صلاحية غير صحيح: {permission_type}"
            
            return True, ""
            
        except Exception as e:
            return False, "خطأ في التحقق من صحة البيانات"

    def get_permission_statistics(self):
        """
        Get permission statistics
        
        Returns:
            dict: Permission statistics
        """
        try:
            total_permissions = UserPermission.objects.count()
            granted_permissions = UserPermission.objects.filter(granted=True).count()
            revoked_permissions = UserPermission.objects.filter(granted=False).count()
            
            # Permissions by module
            permissions_by_module = UserPermission.objects.filter(
                granted=True
            ).values('module_permission__module_name').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Users with permissions
            users_with_permissions = UserPermission.objects.filter(
                granted=True
            ).values('user').distinct().count()
            
            return {
                'total_permissions': total_permissions,
                'granted_permissions': granted_permissions,
                'revoked_permissions': revoked_permissions,
                'permissions_by_module': list(permissions_by_module),
                'users_with_permissions': users_with_permissions
            }
            
        except Exception:
            return {
                'total_permissions': 0,
                'granted_permissions': 0,
                'revoked_permissions': 0,
                'permissions_by_module': [],
                'users_with_permissions': 0
            }

    def search_user_permissions(self, queryset, search_field, search_query):
        """
        Apply search filter to user permissions queryset
        
        Args:
            queryset: User permissions queryset
            search_field: Field to search in
            search_query: Search query
            
        Returns:
            QuerySet: Filtered queryset
        """
        if not search_query:
            return queryset
        
        if search_field == 'username':
            return queryset.filter(user__username__icontains=search_query)
        elif search_field == 'module_name':
            return queryset.filter(module_permission__module_name__icontains=search_query)
        elif search_field == 'permission_type':
            return queryset.filter(module_permission__permission_type__icontains=search_query)
        elif search_field == 'granted':
            granted_value = search_query.lower() in ['true', '1', 'yes', 'ممنوح', 'نعم']
            return queryset.filter(granted=granted_value)
        else:
            # Fallback to base search method
            return self.search(queryset, search_field, search_query)

    def _is_super_admin(self, user):
        """Check if user is super admin"""
        try:
            profile = user.profile
            return profile.is_super_admin()
        except Exception:
            return user.is_superuser

    def _is_admin_user(self, user):
        """Check if user is admin (including super admin)"""
        try:
            profile = user.profile
            return profile.is_admin_user()
        except Exception:
            return user.groups.filter(name='Admin').exists() or user.is_superuser

    def _get_user_type(self, user):
        """Get user type with fallback to current system"""
        try:
            profile = user.profile
            return profile.get_user_type()
        except Exception:
            if user.groups.filter(name='Admin').exists() or user.is_superuser:
                return 'admin'
            return 'normal'

    def _can_assign_permissions(self, user):
        """Check if user can assign permissions"""
        try:
            user_type = self._get_user_type(user)
            return user_type in ['super_admin', 'admin']
        except Exception:
            return False

    def _can_receive_permissions(self, user):
        """Check if user can receive permissions"""
        try:
            user_type = self._get_user_type(user)
            return user_type == 'normal'  # Only normal users need specific permissions
        except Exception:
            return True  # Fallback for users without profiles

    def get_all_module_permissions(self):
        """
        Get all available module permissions
        
        Returns:
            dict: All module permissions organized by module
        """
        try:
            permissions = {}
            
            # Get all module permissions
            module_permissions = ModulePermission.objects.all().order_by('module_name', 'permission_type')
            
            for permission in module_permissions:
                module_name = permission.module_name
                if module_name not in permissions:
                    permissions[module_name] = []
                permissions[module_name].append(permission.permission_type)
            
            return permissions
            
        except Exception:
            return {}

    def create_default_permissions(self):
        """
        Create default module permissions if they don't exist
        
        Returns:
            list: Created permissions
        """
        try:
            modules = ['cars', 'equipment', 'generic_tables']
            permission_types = ['create', 'read', 'update', 'delete']
            
            created_permissions = []
            
            for module_name in modules:
                for permission_type in permission_types:
                    permission, created = ModulePermission.objects.get_or_create(
                        module_name=module_name,
                        permission_type=permission_type,
                        defaults={
                            'description': f"صلاحية {permission_type} للوحدة {module_name}"
                        }
                    )
                    if created:
                        created_permissions.append(permission)
            
            return created_permissions
            
        except Exception:
            return []
