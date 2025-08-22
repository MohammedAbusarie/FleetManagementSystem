"""
Custom error handlers for the fleet management system.
Provides user-friendly error pages with both user and developer information.
"""

from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils.translation import gettext as _
import logging
import traceback

logger = logging.getLogger(__name__)


def get_error_context(request, error_type, error_message, technical_details=None):
    """Get common context for error pages"""
    return {
        'error_type': error_type,
        'error_message': error_message,
        'technical_details': technical_details,
        'user': request.user if hasattr(request, 'user') else None,
        'request_path': request.path if hasattr(request, 'path') else '',
        'request_method': request.method if hasattr(request, 'method') else '',
    }


def custom_400_handler(request, exception=None):
    """Handle 400 Bad Request errors"""
    error_message = _("طلب غير صالح")
    technical_details = str(exception) if exception else "Bad Request"
    
    logger.warning(f"400 Error: {request.path} - {technical_details}")
    
    context = get_error_context(request, "400", error_message, technical_details)
    return render(request, 'inventory/errors/400.html', context, status=400)


def custom_403_handler(request, exception=None):
    """Handle 403 Forbidden errors"""
    error_message = _("ليس لديك صلاحية للوصول إلى هذه الصفحة")
    technical_details = str(exception) if exception else "Forbidden"
    
    logger.warning(f"403 Error: {request.path} - {technical_details}")
    
    context = get_error_context(request, "403", error_message, technical_details)
    return render(request, 'inventory/errors/403.html', context, status=403)


def custom_404_handler(request, exception=None):
    """Handle 404 Not Found errors"""
    error_message = _("الصفحة المطلوبة غير موجودة")
    technical_details = str(exception) if exception else "Not Found"
    
    logger.warning(f"404 Error: {request.path} - {technical_details}")
    
    context = get_error_context(request, "404", error_message, technical_details)
    return render(request, 'inventory/errors/404.html', context, status=404)


def custom_500_handler(request):
    """Handle 500 Internal Server errors"""
    error_message = _("حدث خطأ في الخادم")
    technical_details = "Internal Server Error"
    
    logger.error(f"500 Error: {request.path}")
    
    context = get_error_context(request, "500", error_message, technical_details)
    return render(request, 'inventory/errors/500.html', context, status=500)


def handle_database_error(request, exception):
    """Handle database-related errors with user-friendly messages"""
    from django.db import IntegrityError
    from django.db.models.deletion import ProtectedError
    
    if isinstance(exception, ProtectedError):
        # Handle protected foreign key errors
        error_message = "لا يمكن حذف هذا العنصر لأنه مرتبط بعناصر أخرى في النظام"
        
        # Extract related objects from the error with detailed information
        related_objects = []
        model_counts = {}
        
        if hasattr(exception, 'protected_objects'):
            for obj in exception.protected_objects:
                model_name = obj.__class__.__name__
                model_counts[model_name] = model_counts.get(model_name, 0) + 1
                
                # Get Arabic model name for better user experience
                arabic_model_name = get_arabic_model_name(model_name)
                
                related_objects.append({
                    'model': model_name,
                    'arabic_model': arabic_model_name,
                    'pk': obj.pk,
                    'str': str(obj)[:100],  # Limit string length
                    'admin_url': f"/admin/inventory/{model_name.lower()}/{obj.pk}/change/" if hasattr(obj, 'pk') else None
                })
        
        # Create detailed error message with counts
        if related_objects:
            detailed_message = f"هذا العنصر مرتبط بـ {len(related_objects)} عنصر آخر في النظام:\n"
            for model_name, count in model_counts.items():
                arabic_name = get_arabic_model_name(model_name)
                detailed_message += f"• {arabic_name}: {count} عنصر\n"
            
            # Add specific guidance based on the model being deleted
            deleted_model_name = get_model_name_from_request(request)
            if deleted_model_name:
                arabic_deleted_name = get_arabic_model_name(deleted_model_name)
                detailed_message += f"\nلاستكمال عملية حذف {arabic_deleted_name}، يجب أولاً حذف أو تعديل العناصر المرتبطة بها."
        else:
            detailed_message = "هذا العنصر مرتبط بعناصر أخرى في النظام ولا يمكن حذفه."
        
        technical_details = {
            'error_type': 'ProtectedError',
            'message': str(exception),
            'detailed_message': detailed_message,
            'related_objects': related_objects,
            'model_counts': model_counts,
            'total_count': len(related_objects),
            'deleted_model': get_model_name_from_request(request)
        }
        
        logger.warning(f"ProtectedError: {request.path} - {str(exception)}")
        
    elif isinstance(exception, IntegrityError):
        # Handle other integrity errors
        error_message = "خطأ في قاعدة البيانات - قد يكون هناك تضارب في البيانات"
        technical_details = {
            'error_type': 'IntegrityError',
            'message': str(exception)
        }
        
        logger.error(f"IntegrityError: {request.path} - {str(exception)}")
        
    else:
        # Handle other database errors
        error_message = "خطأ في قاعدة البيانات"
        technical_details = {
            'error_type': 'DatabaseError',
            'message': str(exception)
        }
        
        logger.error(f"DatabaseError: {request.path} - {str(exception)}")
    
    context = get_error_context(request, "database_error", error_message, technical_details)
    return render(request, 'inventory/errors/database_error.html', context, status=400)


def get_model_name_from_request(request):
    """Extract model name from request path"""
    path = request.path
    if '/cars/' in path:
        return 'Car'
    elif '/equipment/' in path:
        return 'Equipment'
    elif '/generic-tables/' in path:
        # Extract model name from URL pattern
        parts = path.split('/')
        if len(parts) > 3:
            return parts[3].title()
    return None


def get_arabic_model_name(model_name):
    """Get Arabic name for model"""
    from .utils.translations import get_model_arabic_name
    return get_model_arabic_name(model_name)


def handle_validation_error(request, exception):
    """Handle validation errors"""
    error_message = _("البيانات المدخلة غير صحيحة")
    technical_details = {
        'error_type': 'ValidationError',
        'message': str(exception),
        'errors': getattr(exception, 'message_dict', None) or getattr(exception, 'messages', None)
    }
    
    logger.warning(f"ValidationError: {request.path} - {str(exception)}")
    
    context = get_error_context(request, "validation_error", error_message, technical_details)
    return render(request, 'inventory/errors/validation_error.html', context, status=400)


def handle_permission_error(request, exception):
    """Handle permission-related errors"""
    error_message = _("ليس لديك صلاحية لإجراء هذه العملية")
    technical_details = {
        'error_type': 'PermissionError',
        'message': str(exception)
    }
    
    logger.warning(f"PermissionError: {request.path} - {str(exception)}")
    
    context = get_error_context(request, "permission_error", error_message, technical_details)
    return render(request, 'inventory/errors/permission_error.html', context, status=403)


def handle_general_error(request, exception):
    """Handle general exceptions"""
    error_message = _("حدث خطأ غير متوقع")
    technical_details = {
        'error_type': type(exception).__name__,
        'message': str(exception),
        'traceback': traceback.format_exc()
    }
    
    logger.error(f"General Error: {request.path} - {str(exception)}")
    
    context = get_error_context(request, "general_error", error_message, technical_details)
    return render(request, 'inventory/errors/general_error.html', context, status=500)
