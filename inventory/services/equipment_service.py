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
        expiry_date = today + timedelta(days=days)
        
        # Get equipment with their current inspection and license records
        equipment_with_records = self.get_equipment_with_related().prefetch_related(
            'inspection_records', 'license_records'
        )
        
        expiring_equipment = []
        for equipment in equipment_with_records:
            current_inspection = equipment.current_inspection_record
            current_license = equipment.current_license_record
            
            if expiry_status == 'expired':
                # Check if inspection or license is expired
                inspection_expired = (not current_inspection or 
                                   not current_inspection.end_date or 
                                   current_inspection.end_date < today)
                license_expired = (not current_license or 
                                 not current_license.end_date or 
                                 current_license.end_date < today)
                
                if inspection_expired or license_expired:
                    expiring_equipment.append(equipment)
            else:
                # Check if inspection or license is about to expire
                inspection_expiring = (current_inspection and 
                                     current_inspection.end_date and
                                     current_inspection.end_date >= today and 
                                     current_inspection.end_date <= expiry_date)
                license_expiring = (current_license and 
                                  current_license.end_date and
                                  current_license.end_date >= today and 
                                  current_license.end_date <= expiry_date)
                
                if inspection_expiring or license_expiring:
                    expiring_equipment.append(equipment)
        
        return expiring_equipment
