"""Helper functions and utilities"""
from django.core.paginator import Paginator


def paginate_queryset(queryset, page_number, per_page=20):
    """Helper function to paginate a queryset"""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)


def apply_search_filter(queryset, search_field, search_query):
    """Apply search filter to queryset"""
    if not search_query or not search_field:
        return queryset
    filter_kwargs = {f"{search_field}__icontains": search_query}
    return queryset.filter(**filter_kwargs)


def apply_sorting(queryset, sort_by, sort_order='asc'):
    """Apply sorting to queryset"""
    if sort_by:
        prefix = '-' if sort_order == 'desc' else ''
        return queryset.order_by(f"{prefix}{sort_by}")
    return queryset


# =============================================================================
# RBAC HELPER FUNCTIONS - Following Project Pattern
# =============================================================================

def get_user_type(user):
    """Get user type with fallback to current system"""
    try:
        profile = user.profile
        return profile.get_user_type()
    except Exception:
        # Fallback to current system
        if user.groups.filter(name='Admin').exists() or user.is_superuser:
            return 'admin'
        return 'normal'


def is_super_admin(user):
    """Check if user is super admin"""
    try:
        profile = user.profile
        return profile.is_super_admin()
    except Exception:
        return user.is_superuser


def is_admin_user(user):
    """Check if user is admin (including super admin)"""
    try:
        profile = user.profile
        return profile.is_admin_user()
    except Exception:
        return user.groups.filter(name='Admin').exists() or user.is_superuser


def has_permission(user, module_name, permission_type):
    """Check if user has specific permission"""
    from ..models import UserPermission

    # Check if user is super admin
    if is_super_admin(user):
        return True

    # Check if user is admin (has all permissions)
    if is_admin_user(user):
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


def get_user_permissions(user):
    """Get all permissions for a user"""
    from ..models import UserPermission

    return UserPermission.objects.filter(user=user).select_related('module_permission')


def get_module_permissions(module_name):
    """Get all permissions for a module"""
    from ..models import ModulePermission

    return ModulePermission.objects.filter(module_name=module_name)


def log_user_action(user, action_type, module_name=None, object_id=None, description="", ip_address=None):
    """Log user action"""
    from ..models import ActionLog

    return ActionLog.objects.create(
        user=user,
        action_type=action_type,
        module_name=module_name,
        object_id=object_id,
        description=description,
        ip_address=ip_address
    )


def log_user_login(user, ip_address, user_agent, success=True):
    """Log user login"""
    from ..models import LoginLog

    return LoginLog.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')
