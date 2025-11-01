"""Equipment-related forms"""
from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from ..models import Equipment, CalibrationCertificateImage, Maintenance, EquipmentImage, EquipmentLicenseRecord, EquipmentInspectionRecord, FireExtinguisherInspectionRecord, FireExtinguisherImage, Sector, Department, Division
from .base import Select2Widget
from .generic_forms import MaintenanceForm


class EquipmentForm(forms.ModelForm):
    """Form for Equipment model"""
    
    class Meta:
        model = Equipment
        fields = [
            'door_no', 'plate_no', 'manufacture_year', 'manufacturer', 'model',
            'location', 'sector', 'department', 'division', 'status'
        ]
        widgets = {
            # Foreign key fields with search functionality
            'manufacturer': Select2Widget(attrs={'data-placeholder': 'اختر الشركة المصنعة...'}),
            'model': Select2Widget(attrs={'data-placeholder': 'اختر الموديل...'}),
            'location': Select2Widget(attrs={'data-placeholder': 'اختر الموقع...'}),
            'sector': Select2Widget(attrs={'data-placeholder': 'اختر القطاع...', 'class': 'nested-selector-sector'}),
            'department': Select2Widget(attrs={'data-placeholder': 'اختر الإدارة...', 'class': 'nested-selector-department'}),
            'division': Select2Widget(attrs={'data-placeholder': 'اختر الدائرة...', 'class': 'nested-selector-division'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        # Ensure sector field always has all sectors available
        self.fields['sector'].queryset = Sector.objects.all()
        
        # Make sure department and division fields are not required initially (will be validated in clean)
        self.fields['department'].required = False
        self.fields['division'].required = False
        
        # Filter querysets based on instance values if updating
        if self.instance and self.instance.pk:
            # If updating, filter departments and divisions based on existing values
            if self.instance.sector:
                self.fields['department'].queryset = Department.objects.filter(
                    Q(sector=self.instance.sector) | Q(is_dummy=True)
                ).distinct()
            else:
                self.fields['department'].queryset = Department.objects.filter(is_dummy=True)
            
            if self.instance.department:
                self.fields['division'].queryset = Division.objects.filter(
                    Q(department=self.instance.department) | Q(is_dummy=True)
                ).distinct()
            else:
                self.fields['division'].queryset = Division.objects.filter(is_dummy=True)
        else:
            # For new records, set defaults to "غير محدد" (dummy records)
            # Get dummy records
            dummy_sector = Sector.objects.filter(name='غير محدد', is_dummy=True).first()
            dummy_department = Department.objects.filter(name='غير محدد', is_dummy=True).first()
            dummy_division = Division.objects.filter(name='غير محدد', is_dummy=True).first()
            
            # Set default values to dummy records
            if dummy_sector and not self.initial.get('sector'):
                self.initial['sector'] = dummy_sector.pk
            if dummy_department and not self.initial.get('department'):
                self.initial['department'] = dummy_department.pk
            if dummy_division and not self.initial.get('division'):
                self.initial['division'] = dummy_division.pk
            
            # Start with querysets that include dummy records
            self.fields['department'].queryset = Department.objects.filter(is_dummy=True)
            self.fields['division'].queryset = Division.objects.filter(is_dummy=True)
        
        # Ensure fields render even with empty querysets by explicitly including them
        # The fields will be populated dynamically via JavaScript when sector/department is selected
    
    def full_clean(self):
        """
        Override full_clean to update querysets before field validation.
        This ensures that selected values pass Django's queryset validation.
        """
        # Get raw data from form before validation
        if self.data:
            sector_id = self.data.get('sector')
            department_id = self.data.get('department')
            division_id = self.data.get('division')
            
            # Update querysets based on submitted values BEFORE validation
            if sector_id:
                try:
                    sector = Sector.objects.get(pk=sector_id)
                    # Update department queryset to include departments for this sector
                    self.fields['department'].queryset = Department.objects.filter(
                        Q(sector=sector) | Q(is_dummy=True)
                    ).distinct()
                    
                    # If division is also selected, update division queryset
                    if division_id:
                        try:
                            division = Division.objects.get(pk=division_id)
                            # Allow the selected division
                            current_division_qs = self.fields['division'].queryset
                            if division not in current_division_qs:
                                # Add the selected division to queryset
                                sector_departments = Department.objects.filter(
                                    Q(sector=sector) | Q(is_dummy=True)
                                ).distinct()
                                self.fields['division'].queryset = Division.objects.filter(
                                    Q(department__in=sector_departments) | Q(is_dummy=True) | Q(pk=division.pk)
                                ).distinct()
                        except Division.DoesNotExist:
                            pass
                except (Sector.DoesNotExist, ValueError):
                    pass
            
            if department_id:
                try:
                    department = Department.objects.get(pk=department_id)
                    # Update division queryset to include divisions for this department
                    self.fields['division'].queryset = Division.objects.filter(
                        Q(department=department) | Q(is_dummy=True)
                    ).distinct()
                except (Department.DoesNotExist, ValueError):
                    pass
            
            # If division is selected without department, ensure it's in queryset
            if division_id and not department_id:
                try:
                    division = Division.objects.get(pk=division_id)
                    if division not in self.fields['division'].queryset:
                        self.fields['division'].queryset = Division.objects.filter(
                            Q(pk=division.pk) | Q(is_dummy=True)
                        ).distinct()
                except (Division.DoesNotExist, ValueError):
                    pass
        
        # Call parent full_clean to proceed with normal validation
        super().full_clean()
    
    def clean(self):
        cleaned_data = super().clean()
        sector = cleaned_data.get('sector')
        department = cleaned_data.get('department')
        division = cleaned_data.get('division')
        
        # Validation for new records - division is required
        # For existing records, allow NULL values (backward compatibility)
        if not self.instance.pk and not division:
            raise forms.ValidationError({
                'division': 'يجب اختيار دائرة (Division is required for new records).'
            })
        
        # If updating and all hierarchy fields are NULL, that's okay (backward compatibility)
        if self.instance.pk and not sector and not department and not division:
            return cleaned_data
        
        # Validate hierarchy consistency
        if division:
            if department and division.department != department:
                # Special case: Allow main dummy division "غير محدد" to be selected
                # with any department (it's a fallback option that should always be available)
                if division.name == 'غير محدد' and division.is_dummy:
                    # Allow this combination - keep the selected department
                    pass  # Don't change department, allow the combination
                else:
                    raise forms.ValidationError({
                        'division': 'الدائرة المختارة لا تنتمي للإدارة المحددة.'
                    })
            elif not department:
                # If division is selected without department, set department from division
                cleaned_data['department'] = division.department
        
        if department:
            if sector and department.sector != sector:
                # Special case: Allow main dummy department "غير محدد" to be selected
                # with any sector (it's a fallback option that should always be available)
                if department.name == 'غير محدد' and department.is_dummy:
                    # Allow this combination - keep the selected sector
                    pass  # Don't change sector, allow the combination
                else:
                    raise forms.ValidationError({
                        'department': 'الإدارة المختارة لا تنتمي للقطاع المحدد.'
                    })
            elif not sector:
                # If department is selected without sector, set sector from department
                cleaned_data['sector'] = department.sector
        
        # Allow all combinations (per system requirements):
        # - Valid Sector → Dummy Department → Dummy Division (allowed)
        # - Valid Sector → Dummy Department → Valid Division (allowed)
        # - Dummy Sector → Dummy Department → Dummy Division (allowed)
        # - Dummy Sector → Dummy Department → Valid Division (allowed)
        # - Valid Sector → Valid Department → Valid Division (allowed)
        # - Valid Sector → Valid Department → Dummy Division (allowed) - NEW: Allowed per requirements
        # No restrictions on dummy department with valid sector
        # No restrictions on dummy division with valid department
        
        return cleaned_data


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