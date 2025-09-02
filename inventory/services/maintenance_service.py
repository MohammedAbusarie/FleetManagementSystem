"""Maintenance-related business logic"""
from django.contrib.contenttypes.models import ContentType
from .base import BaseService
from ..models import Maintenance


class MaintenanceService(BaseService):
    """Service for Maintenance operations"""
    model = Maintenance
    
    def get_maintenance_for_object(self, obj):
        """Get all maintenance records for a specific object"""
        content_type = ContentType.objects.get_for_model(obj)
        return self.model.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).order_by('-maintenance_date')
    
    def create_maintenance(self, content_object, **kwargs):
        """Create maintenance record for an object"""
        maintenance = self.model(content_object=content_object, **kwargs)
        maintenance.save()
        return maintenance
