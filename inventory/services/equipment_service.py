"""Equipment-related business logic"""
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery, Q
from datetime import date, timedelta
from .base import BaseService
from ..models import Equipment, Maintenance


class EquipmentService(BaseService):
    """Service for Equipment operations"""
    model = Equipment
    
    def get_equipment_with_related(self):
        """Get equipment with all related objects prefetched"""
        return self.model.objects.select_related(
            'manufacturer', 'model', 'location', 'sector'
        ).prefetch_related('calibration_certificates')
    
    def get_equipment_with_maintenance(self):
        """Get equipment annotated with latest maintenance info"""
        equipment_ct = ContentType.objects.get_for_model(Equipment)
        latest_maintenance = Maintenance.objects.filter(
            content_type=equipment_ct,
            object_id=OuterRef('pk')
        ).order_by('-maintenance_date')
        
        return self.get_equipment_with_related().annotate(
            last_maintenance_date=Subquery(
                latest_maintenance.values('maintenance_date')[:1]
            ),
            last_maintenance_cost=Subquery(
                latest_maintenance.values('cost')[:1]
            )
        )
    
    def search_equipment(self, queryset, search_field, search_query):
        """Apply search filter to equipment queryset"""
        if not search_query:
            return queryset
        
        if search_field == 'door_no':
            return queryset.filter(door_no__icontains=search_query)
        elif search_field == 'plate_no':
            return queryset.filter(plate_no__icontains=search_query)
        elif search_field == 'manufacturer':
            return queryset.filter(manufacturer__name__icontains=search_query)
        else:
            # Fallback to base search method
            return self.search(queryset, search_field, search_query)
    
    def get_expiring_equipment(self, expiry_status='about_to_expire', days=30):
        """Get equipment with expiring inspections/licenses"""
        today = date.today()
        
        if expiry_status == 'expired':
            return self.get_equipment_with_related().filter(
                Q(annual_inspection_end_date__lt=today) |
                Q(equipment_license_end_date__lt=today) |
                Q(annual_inspection_end_date__isnull=True) |
                Q(equipment_license_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
        else:
            expiry_date = today + timedelta(days=days)
            return self.get_equipment_with_related().filter(
                Q(annual_inspection_end_date__gte=today) | Q(annual_inspection_end_date__isnull=True),
                Q(equipment_license_end_date__gte=today) | Q(equipment_license_end_date__isnull=True),
                Q(annual_inspection_end_date__lte=expiry_date) | Q(annual_inspection_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
