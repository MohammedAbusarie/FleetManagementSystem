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
        ).prefetch_related('visited_regions')
    
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
        
        if expiry_status == 'expired':
            return self.get_cars_with_related().filter(
                Q(annual_inspection_end_date__lt=today) |
                Q(car_license_end_date__lt=today) |
                Q(annual_inspection_end_date__isnull=True) |
                Q(car_license_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
        else:
            expiry_date = today + timedelta(days=days)
            return self.get_cars_with_related().filter(
                Q(annual_inspection_end_date__gte=today) | Q(annual_inspection_end_date__isnull=True),
                Q(car_license_end_date__gte=today) | Q(car_license_end_date__isnull=True),
                Q(annual_inspection_end_date__lte=expiry_date) | Q(annual_inspection_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
