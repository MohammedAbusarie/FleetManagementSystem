"""Custom model managers"""
from django.db import models
from datetime import date, timedelta


class CarManager(models.Manager):
    """Custom manager for Car model"""

    def with_related(self):
        """Prefetch all related objects"""
        return self.select_related(
            'manufacturer', 'model', 'administrative_unit',
            'department_code', 'car_class', 'driver_name',
            'functional_location', 'room', 'notification_recipient',
            'contract_type', 'activity', 'sector', 'department', 'division'
        ).prefetch_related('visited_regions')

    def by_status(self, status):
        """Filter by status with optimizations"""
        return self.with_related().filter(status=status)

    def expiring_inspections(self, days=30):
        """Get cars with inspections expiring in X days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)

        # Get cars with their current inspection records
        cars_with_inspections = self.with_related().prefetch_related(
            'inspection_records'
        )

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
            'manufacturer', 'model', 'location', 'sector', 'department', 'division'
        ).prefetch_related('calibration_certificates')

    def by_status(self, status):
        """Filter by status with optimizations"""
        return self.with_related().filter(status=status)

    def expiring_inspections(self, days=30):
        """Get equipment with inspections expiring in X days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)

        # Get equipment with their current inspection records
        equipment_with_inspections = self.with_related().prefetch_related(
            'inspection_records'
        )

        expiring_equipment = []
        for equipment in equipment_with_inspections:
            current_inspection = equipment.current_inspection_record
            if (current_inspection and
                    current_inspection.end_date >= today and
                    current_inspection.end_date <= expiry_date):
                expiring_equipment.append(equipment)

        return expiring_equipment


# =============================================================================
# RBAC SYSTEM MANAGERS - Following Project Pattern
# =============================================================================

class UserProfileManager(models.Manager):
    """Custom manager for UserProfile model"""

    def active(self):
        """Get active user profiles"""
        return self.filter(is_active=True)

    def by_user_type(self, user_type):
        """Filter by user type"""
        return self.filter(user_type=user_type, is_active=True)

    def super_admins(self):
        """Get super admin profiles"""
        return self.filter(user_type='super_admin', is_active=True)

    def admins(self):
        """Get admin profiles"""
        return self.filter(user_type='admin', is_active=True)

    def normal_users(self):
        """Get normal user profiles"""
        return self.filter(user_type='normal', is_active=True)

    def with_user_info(self):
        """Prefetch user information"""
        return self.select_related('user', 'created_by')


class ModulePermissionManager(models.Manager):
    """Custom manager for ModulePermission model"""

    def by_module(self, module_name):
        """Get permissions for specific module"""
        return self.filter(module_name=module_name)

    def by_permission_type(self, permission_type):
        """Get permissions by type"""
        return self.filter(permission_type=permission_type)

    def crud_permissions(self):
        """Get all CRUD permissions"""
        return self.filter(
            permission_type__in=['create', 'read', 'update', 'delete']
        )


class UserPermissionManager(models.Manager):
    """Custom manager for UserPermission model"""

    def granted(self):
        """Get granted permissions"""
        return self.filter(granted=True)

    def revoked(self):
        """Get revoked permissions"""
        return self.filter(granted=False)

    def by_user(self, user):
        """Get permissions for specific user"""
        return self.filter(user=user)

    def by_module(self, module_name):
        """Get permissions for specific module"""
        return self.filter(module_permission__module_name=module_name)

    def with_related(self):
        """Prefetch related objects"""
        return self.select_related('user', 'module_permission')


class LoginLogManager(models.Manager):
    """Custom manager for LoginLog model"""

    def successful(self):
        """Get successful logins"""
        return self.filter(success=True)

    def failed(self):
        """Get failed logins"""
        return self.filter(success=False)

    def by_user(self, user):
        """Get login logs for specific user"""
        return self.filter(user=user)

    def recent(self, days=30):
        """Get recent login logs"""
        from django.utils import timezone
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(login_time__gte=cutoff_date)

    def with_user_info(self):
        """Prefetch user information"""
        return self.select_related('user')


class ActionLogManager(models.Manager):
    """Custom manager for ActionLog model"""

    def by_user(self, user):
        """Get action logs for specific user"""
        return self.filter(user=user)

    def by_module(self, module_name):
        """Get action logs for specific module"""
        return self.filter(module_name=module_name)

    def by_action_type(self, action_type):
        """Get action logs by action type"""
        return self.filter(action_type=action_type)

    def recent(self, days=30):
        """Get recent action logs"""
        from django.utils import timezone
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(timestamp__gte=cutoff_date)

    def with_user_info(self):
        """Prefetch user information"""
        return self.select_related('user')
