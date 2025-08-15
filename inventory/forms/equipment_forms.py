"""Equipment-related forms"""
from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from ..models import Equipment, CalibrationCertificateImage, Maintenance
from .base import Select2Widget
from .generic_forms import MaintenanceForm


class EquipmentForm(forms.ModelForm):
    """Form for Equipment model"""
    
    class Meta:
        model = Equipment
        fields = [
            'door_no', 'plate_no', 'manufacture_year', 'manufacturer', 'model',
            'location', 'sector', 'status', 'equipment_license_start_date',
            'equipment_license_end_date', 'annual_inspection_start_date',
            'annual_inspection_end_date', 'equipment_image'
        ]
        widgets = {
            # Foreign key fields with search functionality
            'manufacturer': Select2Widget(attrs={'data-placeholder': 'اختر الشركة المصنعة...'}),
            'model': Select2Widget(attrs={'data-placeholder': 'اختر الموديل...'}),
            'location': Select2Widget(attrs={'data-placeholder': 'اختر الموقع...'}),
            'sector': Select2Widget(attrs={'data-placeholder': 'اختر القطاع...'}),
            # Other fields
            'equipment_license_start_date': forms.DateInput(attrs={'type': 'date'}),
            'equipment_license_end_date': forms.DateInput(attrs={'type': 'date'}),
            'annual_inspection_start_date': forms.DateInput(attrs={'type': 'date'}),
            'annual_inspection_end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'

        # Handle image update logic
        if self.instance and self.instance.equipment_image:
            self.fields['equipment_image'].required = False


class CalibrationCertificateImageForm(forms.ModelForm):
    """Form for Calibration Certificate Images"""
    
    class Meta:
        model = CalibrationCertificateImage
        fields = ['image']


# Equipment Maintenance Formset
EquipmentMaintenanceFormSet = generic_inlineformset_factory(
    Maintenance,
    form=MaintenanceForm,
    extra=1,
    can_delete=True,
    ct_field="content_type",
    fk_field="object_id"
)