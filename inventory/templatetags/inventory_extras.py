"""
Custom template filters and tags for the inventory app
"""

from django import template
from django.urls import reverse
import os

register = template.Library()


@register.filter
def arabic_model_name(model_name):
    """Get Arabic name for model"""
    from ..utils.translations import get_model_arabic_name
    return get_model_arabic_name(model_name)


@register.filter
def secure_media_url(media_file):
    """Convert media file URL to secure URL that requires authentication"""
    if not media_file:
        return None

    # Extract the relative path from the media file
    # media_file.url gives us something like '/media/cars/image.jpg'
    # We need to extract 'cars/image.jpg' part
    media_path = str(media_file)

    # Generate secure URL
    return reverse('secure_media', kwargs={'path': media_path})


@register.filter
def basename(file_path):
    """Extract filename from file path"""
    if not file_path:
        return ''
    return os.path.basename(str(file_path))


@register.filter
def is_admin_user(user):
    """Check if user is admin (including super admin)"""
    from ..utils.helpers import is_admin_user as check_admin_user
    return check_admin_user(user)


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None