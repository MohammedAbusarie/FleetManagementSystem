"""Mixins for common functionality"""
from django.contrib.auth.mixins import UserPassesTestMixin
from .helpers import is_admin_user, is_super_admin, has_permission, get_user_type


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin privileges for class-based views - BACKWARD COMPATIBLE"""
    
    def test_func(self):
        return is_admin_user(self.request.user)


class SuperAdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require super admin privileges for class-based views"""
    
    def test_func(self):
        return is_super_admin(self.request.user)


class PermissionRequiredMixin(UserPassesTestMixin):
    """Mixin to require specific module permission for class-based views"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = None
        self.permission_type = None
    
    def test_func(self):
        if not self.module_name or not self.permission_type:
            return False
        return has_permission(self.request.user, self.module_name, self.permission_type)


class AdminOrPermissionRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin privileges OR specific permission for class-based views"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = None
        self.permission_type = None
    
    def test_func(self):
        # Admin users have all permissions
        if is_admin_user(self.request.user):
            return True
        
        # Check specific permission
        if not self.module_name or not self.permission_type:
            return False
        return has_permission(self.request.user, self.module_name, self.permission_type)


class RBACRequiredMixin(UserPassesTestMixin):
    """Flexible mixin for RBAC requirements"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_user_types = None
        self.required_permissions = None
    
    def test_func(self):
        user = self.request.user
        
        # Check user types if specified
        if self.allowed_user_types:
            user_type = get_user_type(user)
            if user_type not in self.allowed_user_types:
                return False
        
        # Check permissions if specified
        if self.required_permissions:
            for module_name, permission_type in self.required_permissions:
                if not has_permission(user, module_name, permission_type):
                    return False
        
        return True


class UserTypeRequiredMixin(UserPassesTestMixin):
    """Mixin to require specific user types for class-based views"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_user_types = ['admin']  # Default to admin only
    
    def test_func(self):
        user_type = get_user_type(self.request.user)
        return user_type in self.allowed_user_types


class ModulePermissionMixin(UserPassesTestMixin):
    """Mixin to check module-specific permissions"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = None
        self.permissions = []  # List of permission types ['create', 'read', 'update', 'delete']
    
    def test_func(self):
        if not self.module_name or not self.permissions:
            return False
        
        user = self.request.user
        
        # Admin users have all permissions
        if is_admin_user(user):
            return True
        
        # Check if user has any of the required permissions
        for permission_type in self.permissions:
            if has_permission(user, self.module_name, permission_type):
                return True
        
        return False
