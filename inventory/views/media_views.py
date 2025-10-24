"""Media views"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
import os
from .auth_views import is_admin


@login_required
@never_cache
@require_http_methods(["GET"])
def secure_media_view(request, path):
    """
    Secure media file serving view that requires authentication.
    All authenticated users can access uploaded images.
    """
    # Construct the full file path
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # Security checks
    if not os.path.exists(file_path):
        raise Http404("الملف غير موجود")
    
    # Ensure the file is within the media directory (prevent directory traversal)
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
        raise Http404("مسار الملف غير صحيح")
    
    # Get file extension to determine content type
    file_extension = os.path.splitext(file_path)[1].lower()
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    
    content_type = content_type_map.get(file_extension, 'application/octet-stream')
    
    # Read and serve the file
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            return response
    except IOError:
        raise Http404("خطأ في قراءة الملف")
