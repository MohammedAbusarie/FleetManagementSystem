"""Helper functions and utilities"""
from django.core.paginator import Paginator
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "BMP", "WEBP"}
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
}


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


def validate_image_files(files):
    """
    Validate that uploaded files are actual images with allowed formats.

    Returns:
        None if all files are valid images, otherwise an Arabic error message.
    """
    for uploaded_file in files:
        if not uploaded_file:
            continue

        content_type = getattr(uploaded_file, "content_type", "")
        if content_type and content_type.lower() not in ALLOWED_IMAGE_CONTENT_TYPES:
            return "الرجاء رفع ملفات صور فقط بصيغ JPG أو PNG أو GIF أو BMP أو WebP."

        try:
            image = Image.open(uploaded_file)
            image.verify()
            if image.format not in ALLOWED_IMAGE_FORMATS:
                return "الرجاء رفع ملفات صور فقط بصيغ JPG أو PNG أو GIF أو BMP أو WebP."
        except (UnidentifiedImageError, OSError):
            return "أحد الملفات المرفوعة ليس صورة صالحة، يرجى التحقق والمحاولة مرة أخرى."
        finally:
            try:
                uploaded_file.seek(0)
            except (AttributeError, OSError):
                pass

    return None


def ensure_maintenance_records_required(status, maintenance_formset):
    """
    Enforce that at least one maintenance record with a maintenance date exists
    when the car status is set to under maintenance.
    """
    if status != 'under_maintenance':
        return None

    message_missing_record = "يجب إضافة سجل صيانة واحد على الأقل عند اختيار حالة السيارة «تحت الصيانة»."
    message_missing_date = "يرجى استكمال بيانات سجلات الصيانة قبل الحفظ."

    non_deleted_forms = []
    for form in getattr(maintenance_formset, 'forms', []):
        cleaned_data = getattr(form, 'cleaned_data', {}) or {}
        if cleaned_data.get('DELETE'):
            continue
        has_values = any(
            cleaned_data.get(field)
            for field in ('maintenance_date', 'restoration_date', 'cost', 'description')
        )
        if has_values:
            non_deleted_forms.append(form)

    if not non_deleted_forms:
        maintenance_formset._non_form_errors = maintenance_formset.error_class([message_missing_record])
        return message_missing_record

    missing_date = False
    for form in non_deleted_forms:
        cleaned_data = form.cleaned_data
        if not cleaned_data.get('maintenance_date'):
            form.add_error('maintenance_date', "تاريخ الصيانة مطلوب عند اختيار حالة السيارة «تحت الصيانة».")
            missing_date = True

    if missing_date:
        return message_missing_date

    return None
