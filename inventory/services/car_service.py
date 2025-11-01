"""Car-related business logic"""
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery, Q
from datetime import date, timedelta
from .base import BaseService
from ..models import Car, Maintenance


class CarService(BaseService):
    """Service for Car operations"""
    model = Car
    
    def get_cars_with_related(self):
        """Get cars with all related objects prefetched"""
        return self.model.objects.select_related(
            'manufacturer', 'model', 'administrative_unit', 
            'department_code', 'car_class', 'driver_name',
            'functional_location', 'room', 'notification_recipient',
            'contract_type', 'activity'
        ).prefetch_related('visited_regions', 'car_images')
    
    def get_cars_with_maintenance(self):
        """Get cars annotated with latest maintenance info"""
        car_ct = ContentType.objects.get_for_model(Car)
        latest_maintenance = Maintenance.objects.filter(
            content_type=car_ct,
            object_id=OuterRef('pk')
        ).order_by('-maintenance_date')
        
        return self.get_cars_with_related().annotate(
            last_maintenance_date=Subquery(
                latest_maintenance.values('maintenance_date')[:1]
            ),
            last_maintenance_cost=Subquery(
                latest_maintenance.values('cost')[:1]
            )
        )
    
    def search_cars(self, queryset, search_field, search_query):
        """Apply search filter to cars queryset"""
        if not search_query:
            return queryset
        
        if search_field == 'fleet_no':
            return queryset.filter(fleet_no__icontains=search_query)
        elif search_field == 'plate_no_en':
            return queryset.filter(plate_no_en__icontains=search_query)
        elif search_field == 'plate_no_ar':
            return queryset.filter(plate_no_ar__icontains=search_query)
        elif search_field == 'manufacturer':
            return queryset.filter(manufacturer__name__icontains=search_query)
        else:
            # Fallback to base search method
            return self.search(queryset, search_field, search_query)
    
    def get_expiring_cars(self, expiry_status='about_to_expire', days=30):
        """Get cars with expiring inspections/licenses"""
        today = date.today()
        
        # Get cars with their current license and inspection records
        cars_with_records = self.get_cars_with_related().prefetch_related(
            'license_records', 'inspection_records'
        )
        
        if expiry_status == 'expired':
            # Filter cars where current records are expired or missing
            expired_cars = []
            for car in cars_with_records:
                current_license = car.current_license_record
                current_inspection = car.current_inspection_record
                
                # Check if license is expired or missing
                license_expired = (current_license and current_license.end_date < today) or not current_license
                # Check if inspection is expired or missing  
                inspection_expired = (current_inspection and current_inspection.end_date < today) or not current_inspection
                
                if license_expired or inspection_expired:
                    expired_cars.append(car)
            
            return expired_cars
        else:
            # Filter cars where current records are about to expire
            expiry_date = today + timedelta(days=days)
            about_to_expire_cars = []
            
            for car in cars_with_records:
                current_license = car.current_license_record
                current_inspection = car.current_inspection_record
                
                # Check if license is about to expire
                license_about_to_expire = (current_license and 
                                         current_license.end_date >= today and 
                                         current_license.end_date <= expiry_date)
                # Check if inspection is about to expire
                inspection_about_to_expire = (current_inspection and 
                                             current_inspection.end_date >= today and 
                                             current_inspection.end_date <= expiry_date)
                
                if license_about_to_expire or inspection_about_to_expire:
                    about_to_expire_cars.append(car)
            
            return about_to_expire_cars
