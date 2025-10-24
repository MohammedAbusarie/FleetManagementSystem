"""Custom model managers"""
from django.db import models
from django.db.models import Q, OuterRef, Subquery
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta


class CarManager(models.Manager):
    """Custom manager for Car model"""
    
    def with_related(self):
        """Prefetch all related objects"""
        return self.select_related(
            'manufacturer', 'model', 'administrative_unit',
            'department_code', 'car_class', 'driver_name',
            'functional_location', 'room', 'notification_recipient',
            'contract_type', 'activity'
        ).prefetch_related('visited_regions')
    
    def by_status(self, status):
        """Filter by status with optimizations"""
        return self.with_related().filter(status=status)
    
    def expiring_inspections(self, days=30):
        """Get cars with inspections expiring in X days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)
        
        # Get cars with their current inspection records
        cars_with_inspections = self.with_related().prefetch_related('inspection_records')
        
        expiring_cars = []
        for car in cars_with_inspections:
            current_inspection = car.current_inspection_record
            if (current_inspection and 
                current_inspection.end_date >= today and 
                current_inspection.end_date <= expiry_date):
                expiring_cars.append(car)
        
        return expiring_cars


class EquipmentManager(models.Manager):
    """Custom manager for Equipment model"""
    
    def with_related(self):
        """Prefetch all related objects"""
        return self.select_related(
            'manufacturer', 'model', 'location', 'sector'
        ).prefetch_related('calibration_certificates')
    
    def by_status(self, status):
        """Filter by status with optimizations"""
        return self.with_related().filter(status=status)
    
    def expiring_inspections(self, days=30):
        """Get equipment with inspections expiring in X days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)
        return self.with_related().filter(
            Q(annual_inspection_end_date__gte=today),
            Q(annual_inspection_end_date__lte=expiry_date)
        )
