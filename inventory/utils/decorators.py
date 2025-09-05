"""Custom decorators"""
from functools import wraps
from django.contrib.auth.decorators import user_passes_test


def admin_required(function):
    """Decorator to require admin privileges"""
    def check_admin(user):
        return user.groups.filter(name='Admin').exists() or user.is_superuser
    
    return user_passes_test(check_admin)(function)
