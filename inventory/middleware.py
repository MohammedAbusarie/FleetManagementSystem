"""
Custom middleware for the inventory app
"""

from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
import os
import logging

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """
    Middleware to handle database errors and other exceptions gracefully.
    Provides user-friendly error messages for constraint violations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Handle exceptions that occur during request processing"""
        
        if isinstance(exception, ProtectedError):
            # Handle protected foreign key errors
            error_message = "لا يمكن حذف هذا العنصر لأنه مرتبط بعناصر أخرى في النظام"
            
            # Extract related objects from the error
            related_objects = []
            model_counts = {}
            
            if hasattr(exception, 'protected_objects'):
                for obj in exception.protected_objects:
                    model_name = obj.__class__.__name__
                    model_counts[model_name] = model_counts.get(model_name, 0) + 1
                    
                    related_objects.append({
                        'model': model_name,
                        'pk': obj.pk,
                        'str': str(obj)[:100],  # Limit string length
                    })
            
            # Create detailed error message
            detailed_message = ""
            if related_objects:
                detailed_message = f"هذا العنصر مرتبط بـ {len(related_objects)} عنصر آخر في النظام:\n"
                for model_name, count in model_counts.items():
                    detailed_message += f"• {model_name}: {count} عنصر\n"
            else:
                detailed_message = "هذا العنصر مرتبط بعناصر أخرى في النظام ولا يمكن حذفه."
            
            logger.warning(f"ProtectedError: {request.path} - {str(exception)}")
            
            # Use the styled error template
            context = {
                'error_type': 'خطأ في الحذف',
                'error_message': error_message,
                'technical_details': detailed_message,
                'user': request.user if hasattr(request, 'user') else None,
                'request_path': request.path if hasattr(request, 'path') else '',
                'request_method': request.method if hasattr(request, 'method') else '',
            }
            
            return render(request, 'inventory/errors/base_error.html', context, status=400)
            
        elif isinstance(exception, IntegrityError):
            # Handle other integrity errors
            error_message = "خطأ في قاعدة البيانات - قد يكون هناك تضارب في البيانات"
            logger.error(f"IntegrityError: {request.path} - {str(exception)}")
            
            context = {
                'error_type': 'خطأ في قاعدة البيانات',
                'error_message': error_message,
                'technical_details': str(exception),
                'user': request.user if hasattr(request, 'user') else None,
                'request_path': request.path if hasattr(request, 'path') else '',
                'request_method': request.method if hasattr(request, 'method') else '',
            }
            
            return render(request, 'inventory/errors/base_error.html', context, status=400)
            
        elif isinstance(exception, ValidationError):
            # Handle validation errors
            error_message = "البيانات المدخلة غير صحيحة"
            logger.warning(f"ValidationError: {request.path} - {str(exception)}")
            
            context = {
                'error_type': 'خطأ في البيانات',
                'error_message': error_message,
                'technical_details': str(exception),
                'user': request.user if hasattr(request, 'user') else None,
                'request_path': request.path if hasattr(request, 'path') else '',
                'request_method': request.method if hasattr(request, 'method') else '',
            }
            
            return render(request, 'inventory/errors/base_error.html', context, status=400)
            
        # Return None to let Django handle other exceptions normally
        return None


class SecureMediaMiddleware:
    """
    Middleware to block direct access to media files.
    All media files must be accessed through the secure_media_view.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for a media file
        if request.path.startswith(settings.MEDIA_URL):
            # Block direct access to media files - use styled error template
            from django.shortcuts import render
            from inventory.error_handlers import get_error_context
            
            error_message = "الوصول المباشر للملفات غير مسموح. يجب تسجيل الدخول أولاً."
            technical_details = f"Direct access to media files is not allowed. Requested path: {request.path}"
            
            logger.warning(f"Direct media access blocked: {request.path} - User: {getattr(request, 'user', 'Anonymous')}")
            
            context = get_error_context(request, "403", error_message, technical_details)
            return render(request, 'inventory/errors/403.html', context, status=403)
        
        response = self.get_response(request)
        return response