"""Car-related forms"""
from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from ..models import Car, Maintenance, CarImage, CarLicenseRecord, CarInspectionRecord
from .base import Select2Widget
from .generic_forms import MaintenanceForm


class CarForm(forms.ModelForm):
    """Form for Car model"""
    
    class Meta:
        model = Car
        fields = [
            'fleet_no', 'plate_no_en', 'plate_no_ar', 'administrative_unit', 'department_code', 'driver_name',
            'car_class', 'manufacturer', 'model', 'functional_location', 'ownership_type',
            'room', 'location_description', 'address_details_1', 'notification_recipient',
            'contract_type', 'activity', 'status'
        ]
        widgets = {
            # Foreign key fields with search functionality
            'administrative_unit': Select2Widget(attrs={'data-placeholder': 'اختر الإدارة...'}),
            'department_code': Select2Widget(attrs={'data-placeholder': 'اختر رمز القسم...'}),
            'driver_name': Select2Widget(attrs={'data-placeholder': 'اختر اسم السائق...'}),
            'car_class': Select2Widget(attrs={'data-placeholder': 'اختر فئة السيارة...'}),
            'manufacturer': Select2Widget(attrs={'data-placeholder': 'اختر الشركة المصنعة...'}),
            'model': Select2Widget(attrs={'data-placeholder': 'اختر الموديل...'}),
            'functional_location': Select2Widget(attrs={'data-placeholder': 'اختر الموقع الوظيفي...'}),
            'room': Select2Widget(attrs={'data-placeholder': 'اختر الغرفة...'}),
            'notification_recipient': Select2Widget(attrs={'data-placeholder': 'اختر مستلم الإشعار...'}),
            'contract_type': Select2Widget(attrs={'data-placeholder': 'اختر نوع العقد...'}),
            'activity': Select2Widget(attrs={'data-placeholder': 'اختر النشاط...'}),
            # Other fields
            'location_description': forms.Textarea(attrs={'rows': 3}),
            'address_details_1': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'


class CarLicenseRecordForm(forms.ModelForm):
    """Form for Car License Records"""
    
    class Meta:
        model = CarLicenseRecord
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class CarInspectionRecordForm(forms.ModelForm):
    """Form for Car Inspection Records"""
    
    class Meta:
        model = CarInspectionRecord
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class CarImageForm(forms.ModelForm):
    """Form for Car Images"""
    
    class Meta:
        model = CarImage
        fields = ['image']


# Car Maintenance Formset
CarMaintenanceFormSet = generic_inlineformset_factory(
    Maintenance,
    form=MaintenanceForm,
    extra=1,
    can_delete=True,
    ct_field="content_type",
    fk_field="object_id"
)

# Car License Records Formset
CarLicenseRecordFormSet = forms.inlineformset_factory(
    Car,
    CarLicenseRecord,
    form=CarLicenseRecordForm,
    extra=1,
    can_delete=True,
    min_num=1,  # At least one license record is required
    validate_min=True
)

# Car Inspection Records Formset
CarInspectionRecordFormSet = forms.inlineformset_factory(
    Car,
    CarInspectionRecord,
    form=CarInspectionRecordForm,
    extra=1,
    can_delete=True,
    min_num=1,  # At least one inspection record is required
    validate_min=True
)