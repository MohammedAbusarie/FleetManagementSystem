"""Forms package - maintains backward compatibility"""
from .base import Select2Widget
from .car_forms import CarForm, CarMaintenanceFormSet, CarLicenseRecordFormSet, CarInspectionRecordFormSet
from .equipment_forms import (
    EquipmentForm,
    CalibrationCertificateImageForm,
    EquipmentMaintenanceFormSet,
)
from .generic_forms import GenericDDLForm, EquipmentModelForm, SearchForm, MaintenanceForm

__all__ = [
    'Select2Widget',
    'CarForm',
    'CarMaintenanceFormSet',
    'CarLicenseRecordFormSet',
    'CarInspectionRecordFormSet',
    'EquipmentForm',
    'CalibrationCertificateImageForm',
    'EquipmentMaintenanceFormSet',
    'GenericDDLForm',
    'EquipmentModelForm',
    'SearchForm',
    'MaintenanceForm',
]