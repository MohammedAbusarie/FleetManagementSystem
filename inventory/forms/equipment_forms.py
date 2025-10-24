"""Equipment-related forms"""
from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from ..models import Equipment, CalibrationCertificateImage, Maintenance, EquipmentImage, EquipmentLicenseRecord, EquipmentInspectionRecord, FireExtinguisherInspectionRecord, FireExtinguisherImage
from .base import Select2Widget
from .generic_forms import MaintenanceForm


class EquipmentForm(forms.ModelForm):
    """Form for Equipment model"""
    
    class Meta:
        model = Equipment
        fields = [
            'door_no', 'plate_no', 'manufacture_year', 'manufacturer', 'model',
            'location', 'sector', 'status'
        ]
        widgets = {
            # Foreign key fields with search functionality
            'manufacturer': Select2Widget(attrs={'data-placeholder': 'اختر الشركة المصنعة...'}),
            'model': Select2Widget(attrs={'data-placeholder': 'اختر الموديل...'}),
            'location': Select2Widget(attrs={'data-placeholder': 'اختر الموقع...'}),
            'sector': Select2Widget(attrs={'data-placeholder': 'اختر القطاع...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'


class CalibrationCertificateImageForm(forms.ModelForm):
    """Form for Calibration Certificate Images"""
    
    class Meta:
        model = CalibrationCertificateImage
        fields = ['image']


class EquipmentImageForm(forms.ModelForm):
    """Form for Equipment Images"""
    
    class Meta:
        model = EquipmentImage
        fields = ['image']


class EquipmentLicenseRecordForm(forms.ModelForm):
    """Form for Equipment License Records"""
    
    class Meta:
        model = EquipmentLicenseRecord
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class EquipmentInspectionRecordForm(forms.ModelForm):
    """Form for Equipment Inspection Records"""
    
    class Meta:
        model = EquipmentInspectionRecord
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class FireExtinguisherInspectionRecordForm(forms.ModelForm):
    """Form for Fire Extinguisher Inspection Records"""
    
    class Meta:
        model = FireExtinguisherInspectionRecord
        fields = ['inspection_date', 'expiry_date']
        widgets = {
            'inspection_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }


class FireExtinguisherImageForm(forms.ModelForm):
    """Form for Fire Extinguisher Images"""
    
    class Meta:
        model = FireExtinguisherImage
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

# Equipment License Records Formset
EquipmentLicenseRecordFormSet = forms.inlineformset_factory(
    Equipment,
    EquipmentLicenseRecord,
    form=EquipmentLicenseRecordForm,
    extra=1,
    can_delete=True,
    min_num=1,  # At least one license record is required
    validate_min=True
)

# Equipment Inspection Records Formset
EquipmentInspectionRecordFormSet = forms.inlineformset_factory(
    Equipment,
    EquipmentInspectionRecord,
    form=EquipmentInspectionRecordForm,
    extra=1,
    can_delete=True,
    min_num=1,  # At least one inspection record is required
    validate_min=True
)

# Fire Extinguisher Inspection Records Formset
FireExtinguisherInspectionRecordFormSet = forms.inlineformset_factory(
    Equipment,
    FireExtinguisherInspectionRecord,
    form=FireExtinguisherInspectionRecordForm,
    extra=1,
    can_delete=True,
    min_num=1,  # At least one fire extinguisher record is required
    validate_min=True
)