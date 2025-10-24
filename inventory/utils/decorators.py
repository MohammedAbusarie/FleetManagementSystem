"""Custom decorators"""
from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
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


# =============================================================================
# USER-FRIENDLY PERMISSION DECORATORS
# =============================================================================

def permission_required_with_message(module_name, permission_type, message=None):
    """
    Decorator to require specific permission with user-friendly message
    Shows permission denied message instead of redirecting to login
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Check if user has permission
            if has_permission(user, module_name, permission_type):
                return function(request, *args, **kwargs)
            
            # User doesn't have permission - show message
            error_message = message
            if not error_message:
                module_display = {
                    'cars': 'السيارات',
                    'equipment': 'المعدات', 
                    'generic_tables': 'الجداول العامة'
                }.get(module_name, module_name)
                
                permission_display = {
                    'create': 'إنشاء',
                    'read': 'عرض',
                    'update': 'تعديل',
                    'delete': 'حذف'
                }.get(permission_type, permission_type)
                
                error_message = f'ليس لديك صلاحية {permission_display} {module_display}. يرجى التواصل مع المدير للحصول على الصلاحيات المطلوبة.'
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': error_message,
                    'permission_denied': True
                }, status=403)
            
            # Regular request - show message and redirect to dashboard
            messages.error(request, error_message)
            return redirect('dashboard')
        
        return wrapper
    return decorator


def admin_or_permission_required_with_message(module_name, permission_type, message=None):
    """
    Decorator to require admin privileges OR specific permission with user-friendly message
    Shows permission denied message instead of redirecting to login
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Admin users have all permissions
            if is_admin_user(user):
                return function(request, *args, **kwargs)
            
            # Check specific permission
            if has_permission(user, module_name, permission_type):
                return function(request, *args, **kwargs)
            
            # User doesn't have permission - show message
            error_message = message
            if not error_message:
                module_display = {
                    'cars': 'السيارات',
                    'equipment': 'المعدات',
                    'generic_tables': 'الجداول العامة'
                }.get(module_name, module_name)
                
                permission_display = {
                    'create': 'إنشاء',
                    'read': 'عرض',
                    'update': 'تعديل',
                    'delete': 'حذف'
                }.get(permission_type, permission_type)
                
                error_message = f'ليس لديك صلاحية {permission_display} {module_display}. يرجى التواصل مع المدير للحصول على الصلاحيات المطلوبة.'
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': error_message,
                    'permission_denied': True
                }, status=403)
            
            # Regular request - show message and redirect to dashboard
            messages.error(request, error_message)
            return redirect('dashboard')
        
        return wrapper
    return decorator


def admin_required_with_message(message=None):
    """
    Decorator to require admin privileges with user-friendly message
    Shows permission denied message instead of redirecting to login
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            if is_admin_user(user):
                return function(request, *args, **kwargs)
            
            # User is not admin - show message
            error_message = message
            if not error_message:
                error_message = 'ليس لديك صلاحية للوصول إلى هذه الصفحة. يجب أن تكون مديراً للوصول إلى هذه الميزة.'
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': error_message,
                    'permission_denied': True
                }, status=403)
            
            # Regular request - show message and redirect to dashboard
            messages.error(request, error_message)
            return redirect('dashboard')
        
        return wrapper
    return decorator


def super_admin_required_with_message(message=None):
    """
    Decorator to require super admin privileges with user-friendly message
    Shows permission denied message instead of redirecting to login
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            if is_super_admin(user):
                return function(request, *args, **kwargs)
            
            # User is not super admin - show message
            error_message = message
            if not error_message:
                error_message = 'ليس لديك صلاحية للوصول إلى هذه الصفحة. يجب أن تكون مديراً عاماً للوصول إلى هذه الميزة.'
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'message': error_message,
                    'permission_denied': True
                }, status=403)
            
            # Regular request - show message and redirect to dashboard
            messages.error(request, error_message)
            return redirect('dashboard')
        
        return wrapper
    return decorator
