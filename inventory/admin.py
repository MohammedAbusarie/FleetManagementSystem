from django.contrib import admin
from .models import (
    AdministrativeUnit, Department, Driver, CarClass, Manufacturer, CarModel, EquipmentModel,
    FunctionalLocation, Room, Location, Sector, Division, NotificationRecipient,
    ContractType, Activity, Region, Car, Equipment, CalibrationCertificateImage,
    Maintenance, CarImage, EquipmentImage, CarLicenseRecord, CarInspectionRecord,
    EquipmentLicenseRecord, EquipmentInspectionRecord, FireExtinguisherInspectionRecord,
    FireExtinguisherImage, UserProfile, ModulePermission, UserPermission,
    LoginLog, ActionLog
)


# Register DDL models
@admin.register(AdministrativeUnit)
class AdministrativeUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_dummy', 'created_at']
    search_fields = ['name']
    list_filter = ['is_dummy', 'created_at']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'division', 'get_administrative_unit', 'get_sector', 'is_dummy', 'created_at']
    search_fields = ['name']
    list_filter = ['division', 'division__administrative_unit', 'is_dummy', 'created_at']
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of protected default record"""
        if obj and obj.is_protected_default:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for protected default record"""
        if obj and obj.is_protected_default:
            return ['name', 'division', 'is_dummy', 'created_at', 'updated_at']
        return ['created_at', 'updated_at']

    @admin.display(description='الإدارة', ordering='division__administrative_unit__name')
    def get_administrative_unit(self, obj):
        return obj.administrative_unit

    @admin.display(description='القطاع', ordering='division__administrative_unit__sector__name')
    def get_sector(self, obj):
        sector = obj.sector
        return sector.name if sector else '-'


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number', 'phone', 'created_at']
    search_fields = ['name', 'license_number']


@admin.register(CarClass)
class CarClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'manufacturer', 'year', 'created_at']
    search_fields = ['name']
    list_filter = ['manufacturer', 'year']


@admin.register(EquipmentModel)
class EquipmentModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'manufacturer', 'created_at']
    search_fields = ['name']
    list_filter = ['manufacturer']


@admin.register(FunctionalLocation)
class FunctionalLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor', 'created_at']
    search_fields = ['name', 'building']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_dummy', 'created_at']
    search_fields = ['name']
    list_filter = ['is_dummy', 'created_at']
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of protected default record"""
        if obj and obj.is_protected_default:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for protected default record"""
        if obj and obj.is_protected_default:
            return ['name', 'is_dummy', 'created_at', 'updated_at']
        return ['created_at', 'updated_at']


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    search_fields = ['name', 'email']


@admin.register(ContractType)
class ContractTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'administrative_unit', 'is_dummy', 'created_at']
    search_fields = ['name']
    list_filter = ['administrative_unit', 'is_dummy', 'created_at']
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of protected default record"""
        if obj and obj.is_protected_default:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for protected default record"""
        if obj and obj.is_protected_default:
            return ['name', 'administrative_unit', 'is_dummy', 'created_at', 'updated_at']
        return ['created_at', 'updated_at']


# Register main models
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = [
        'fleet_no', 'plate_no_en', 'plate_no_ar', 'manufacturer', 'model',
        'ownership_type', 'sector', 'administrative_unit', 'department', 'division', 'created_at'
    ]
    search_fields = ['fleet_no', 'plate_no_en', 'plate_no_ar']
    list_filter = [
        'manufacturer', 'ownership_type', 'department_code', 'car_class',
        'sector', 'administrative_unit', 'department', 'division'
    ]
    filter_horizontal = ['visited_regions']
    fieldsets = (
        ('Basic Information', {
            'fields': ('fleet_no', 'plate_no_en', 'plate_no_ar')
        }),
        ('Organizational Hierarchy', {
            'fields': ('sector', 'administrative_unit', 'department', 'division')
        }),
        ('Vehicle Details', {
            'fields': ('department_code', 'driver_name', 'car_class', 'manufacturer', 'model',
                       'functional_location', 'ownership_type')
        }),
        ('Location', {
            'fields': ('room', 'location_description', 'address_details_1')
        }),
        ('Contract & Activity', {
            'fields': ('notification_recipient', 'contract_type', 'activity')
        }),
        ('Regions', {
            'fields': ('visited_regions',)
        }),
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'door_no', 'plate_no', 'manufacturer', 'model', 'status', 'location',
        'sector', 'administrative_unit', 'department', 'division', 'created_at'
    ]
    search_fields = ['door_no', 'plate_no']
    list_filter = [
        'manufacturer', 'status', 'location', 'sector',
        'administrative_unit', 'department', 'division', 'manufacture_year'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('door_no', 'plate_no', 'manufacture_year')
        }),
        ('Organizational Hierarchy', {
            'fields': ('sector', 'administrative_unit', 'department', 'division')
        }),
        ('Equipment Details', {
            'fields': ('manufacturer', 'model', 'location', 'status')
        }),
        # Dates are now handled by historical records
    )


@admin.register(CalibrationCertificateImage)
class CalibrationCertificateImageAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'uploaded_at']
    list_filter = ['equipment', 'uploaded_at']


@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display = ['car', 'uploaded_at']
    list_filter = ['car', 'uploaded_at']


@admin.register(EquipmentImage)
class EquipmentImageAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'uploaded_at']
    list_filter = ['equipment', 'uploaded_at']


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'maintenance_date', 'restoration_date', 'cost', 'created_at']
    list_filter = ['maintenance_date', 'restoration_date']
    search_fields = ['description']
    fieldsets = (
        ('Linked Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Maintenance Details', {
            'fields': ('maintenance_date', 'restoration_date', 'cost', 'description')
        }),
    )


@admin.register(CarLicenseRecord)
class CarLicenseRecordAdmin(admin.ModelAdmin):
    list_display = ['car', 'start_date', 'end_date', 'created_at']
    list_filter = ['start_date', 'end_date', 'created_at']
    search_fields = ['car__fleet_no', 'car__plate_no_en']
    fieldsets = (
        ('Car Information', {
            'fields': ('car',)
        }),
        ('License Details', {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(CarInspectionRecord)
class CarInspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['car', 'start_date', 'end_date', 'created_at']
    list_filter = ['start_date', 'end_date', 'created_at']
    search_fields = ['car__fleet_no', 'car__plate_no_en']
    fieldsets = (
        ('Car Information', {
            'fields': ('car',)
        }),
        ('Inspection Details', {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(EquipmentLicenseRecord)
class EquipmentLicenseRecordAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'start_date', 'end_date', 'created_at']
    list_filter = ['start_date', 'end_date', 'created_at']
    search_fields = ['equipment__door_no', 'equipment__plate_no']
    fieldsets = (
        ('Equipment Information', {
            'fields': ('equipment',)
        }),
        ('License Details', {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(EquipmentInspectionRecord)
class EquipmentInspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'start_date', 'end_date', 'created_at']
    list_filter = ['start_date', 'end_date', 'created_at']
    search_fields = ['equipment__door_no', 'equipment__plate_no']
    fieldsets = (
        ('Equipment Information', {
            'fields': ('equipment',)
        }),
        ('Inspection Details', {
            'fields': ('start_date', 'end_date')
        }),
    )


@admin.register(FireExtinguisherInspectionRecord)
class FireExtinguisherInspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'inspection_date', 'expiry_date', 'created_at']
    list_filter = ['inspection_date', 'expiry_date', 'created_at']
    search_fields = ['equipment__door_no', 'equipment__plate_no']
    fieldsets = (
        ('Equipment Information', {
            'fields': ('equipment',)
        }),
        ('Fire Extinguisher Details', {
            'fields': ('inspection_date', 'expiry_date')
        }),
    )


@admin.register(FireExtinguisherImage)
class FireExtinguisherImageAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'uploaded_at']
    list_filter = ['equipment', 'uploaded_at']


# =============================================================================
# RBAC SYSTEM ADMIN - Phase 1 Implementation
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['user_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('معلومات المستخدم', {
            'fields': ('user', 'user_type', 'is_active')
        }),
        ('معلومات الإنشاء', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
        ('الصلاحيات', {
            'fields': ('permissions_json',)
        }),
    )


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = ['module_name', 'permission_type', 'description', 'created_at']
    list_filter = ['module_name', 'permission_type', 'created_at']
    search_fields = ['module_name', 'permission_type', 'description']
    readonly_fields = ['created_at']
    fieldsets = (
        ('معلومات الصلاحية', {
            'fields': ('module_name', 'permission_type', 'description')
        }),
        ('معلومات النظام', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'module_permission', 'granted', 'created_at']
    list_filter = ['granted', 'module_permission__module_name', 'created_at']
    search_fields = ['user__username', 'module_permission__module_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('معلومات الصلاحية', {
            'fields': ('user', 'module_permission', 'granted')
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'ip_address', 'success', 'logout_time']
    list_filter = ['success', 'login_time', 'logout_time']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['login_time', 'logout_time']
    fieldsets = (
        ('معلومات تسجيل الدخول', {
            'fields': ('user', 'login_time', 'logout_time', 'success')
        }),
        ('معلومات الشبكة', {
            'fields': ('ip_address', 'user_agent')
        }),
    )


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'module_name', 'object_id', 'timestamp']
    list_filter = ['action_type', 'module_name', 'timestamp']
    search_fields = ['user__username', 'module_name', 'object_id', 'description']
    readonly_fields = ['timestamp']
    fieldsets = (
        ('معلومات العملية', {
            'fields': ('user', 'action_type', 'module_name', 'object_id', 'description')
        }),
        ('معلومات النظام', {
            'fields': ('timestamp', 'ip_address')
        }),
    )
