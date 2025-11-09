"""Forms package - maintains backward compatibility"""
from .base import Select2Widget
from .car_forms import CarForm, CarMaintenanceFormSet, CarLicenseRecordFormSet, CarInspectionRecordFormSet
from .equipment_forms import (
    EquipmentForm,
    CalibrationCertificateImageForm,
    EquipmentMaintenanceFormSet,
    EquipmentLicenseRecordFormSet,
    EquipmentInspectionRecordFormSet,
    FireExtinguisherInspectionRecordFormSet,
)
from .generic_forms import (
    GenericDDLForm,
    EquipmentModelForm,
    CarModelForm,
    SearchForm,
    MaintenanceForm,
    SectorForm,
    AdministrativeUnitForm,
    DepartmentForm,
    DivisionForm,
)

__all__ = [
    'Select2Widget',
    'CarForm',
    'CarMaintenanceFormSet',
    'CarLicenseRecordFormSet',
    'CarInspectionRecordFormSet',
    'EquipmentForm',
    'CalibrationCertificateImageForm',
    'EquipmentMaintenanceFormSet',
    'EquipmentLicenseRecordFormSet',
    'EquipmentInspectionRecordFormSet',
    'FireExtinguisherInspectionRecordFormSet',
    'GenericDDLForm',
    'EquipmentModelForm',
    'CarModelForm',
    'SearchForm',
    'MaintenanceForm',
    'SectorForm',
    'AdministrativeUnitForm',
    'DepartmentForm',
    'DivisionForm',
]