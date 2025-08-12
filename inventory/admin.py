from django.contrib import admin
from .models import (
    Department, Driver, CarClass, Manufacturer, CarModel, EquipmentModel,
    FunctionalLocation, Room, Location, Sector, NotificationRecipient,
    ContractType, Activity, Region, Car, Equipment, CalibrationCertificateImage,
    Maintenance
)


# Register DDL models
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


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
    list_display = ['name', 'created_at']
    search_fields = ['name']


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


# Register main models
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['fleet_no', 'plate_no_en', 'plate_no_ar', 'manufacturer', 'model', 'ownership_type', 'created_at']
    search_fields = ['fleet_no', 'plate_no_en', 'plate_no_ar']
    list_filter = ['manufacturer', 'ownership_type', 'department_code', 'car_class']
    filter_horizontal = ['visited_regions']
    fieldsets = (
        ('Basic Information', {
            'fields': ('fleet_no', 'plate_no_en', 'plate_no_ar')
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
        ('Dates', {
            'fields': ('car_license_start_date', 'car_license_end_date', 
                      'annual_inspection_start_date', 'annual_inspection_end_date')
        }),
        ('Image & Regions', {
            'fields': ('car_image', 'visited_regions')
        }),
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['door_no', 'plate_no', 'manufacturer', 'model', 'status', 'location', 'sector', 'created_at']
    search_fields = ['door_no', 'plate_no']
    list_filter = ['manufacturer', 'status', 'location', 'sector', 'manufacture_year']
    fieldsets = (
        ('Basic Information', {
            'fields': ('door_no', 'plate_no', 'manufacture_year')
        }),
        ('Equipment Details', {
            'fields': ('manufacturer', 'model', 'location', 'sector', 'status')
        }),
        ('Dates', {
            'fields': ('equipment_license_start_date', 'equipment_license_end_date',
                      'annual_inspection_start_date', 'annual_inspection_end_date')
        }),
        ('Image', {
            'fields': ('equipment_image',)
        }),
    )


@admin.register(CalibrationCertificateImage)
class CalibrationCertificateImageAdmin(admin.ModelAdmin):
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
