"""Custom decorators"""
from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import redirect
from .helpers import is_admin_user, is_super_admin, has_permission


def admin_required(function):
    """Decorator to require admin privileges - BACKWARD COMPATIBLE"""
    def check_admin(user):
        return is_admin_user(user)
    
    return user_passes_test(check_admin)(function)


def super_admin_required(function):
    """Decorator to require super admin privileges"""
    def check_super_admin(user):
        return is_super_admin(user)
    
    return user_passes_test(check_super_admin)(function)


def permission_required(module_name, permission_type):
    """Decorator to require specific module permission"""
    def decorator(function):
        def check_permission(user):
            return has_permission(user, module_name, permission_type)
        
        return user_passes_test(check_permission)(function)
    return decorator


def admin_or_permission_required(module_name, permission_type):
    """Decorator to require admin privileges OR specific permission"""
    def decorator(function):
        def check_admin_or_permission(user):
            # Admin users have all permissions
            if is_admin_user(user):
                return True
            # Check specific permission
            return has_permission(user, module_name, permission_type)
        
        return user_passes_test(check_admin_or_permission)(function)
    return decorator


def rbac_required(user_types=None, permissions=None):
    """
    Flexible decorator for RBAC requirements
    Args:
        user_types: List of allowed user types ['super_admin', 'admin', 'normal']
        permissions: List of (module_name, permission_type) tuples
    """
    def decorator(function):
        def check_rbac(user):
            # Check user types if specified
            if user_types:
                user_type = get_user_type(user)
                if user_type not in user_types:
                    return False
            
            # Check permissions if specified
            if permissions:
                for module_name, permission_type in permissions:
                    if not has_permission(user, module_name, permission_type):
                        return False
            
            return True
        
        return user_passes_test(check_rbac)(function)
    return decorator


def get_user_type(user):
    """Helper function to get user type"""
    try:
        profile = user.profile
        return profile.get_user_type()
    except Exception:
        # Fallback to current system
        if user.groups.filter(name='Admin').exists() or user.is_superuser:
            return 'admin'
        return 'normal'
