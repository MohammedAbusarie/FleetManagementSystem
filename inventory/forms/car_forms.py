"""Car-related forms"""
from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from ..models import (
    Car, Maintenance, CarImage, CarLicenseRecord, CarInspectionRecord,
    Sector, Department, AdministrativeUnit, Division
)
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
            'contract_type', 'activity', 'sector', 'department', 'division', 'status'
        ]
        widgets = {
            # English/LTR fields
            'fleet_no': forms.TextInput(attrs={
                'class': 'form-control english-field',
                'placeholder': 'Fleet Number',
                'style': 'text-transform: uppercase;',
                'lang': 'en',
                'inputmode': 'latin'
            }),
            'plate_no_en': forms.TextInput(attrs={
                'class': 'form-control english-field',
                'placeholder': 'License Plate (English)',
                'style': 'text-transform: uppercase;',
                'lang': 'en',
                'inputmode': 'latin'
            }),
            # Foreign key fields with search functionality
            'administrative_unit': Select2Widget(attrs={
                'data-placeholder': 'اختر الإدارة...', 'class': 'nested-selector-administrative-unit'
            }),
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
            # Organizational Hierarchy fields
            'sector': Select2Widget(attrs={'data-placeholder': 'اختر القطاع...', 'class': 'nested-selector-sector'}),
            'department': Select2Widget(attrs={'data-placeholder': 'اختر القسم...'}),
            'division': Select2Widget(attrs={'data-placeholder': 'اختر الدائرة...', 'class': 'nested-selector-division'}),
            # Other fields
            'location_description': forms.Textarea(attrs={'rows': 3}),
            'address_details_1': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        # Ensure sector field always has all sectors available
        self.fields['sector'].queryset = Sector.objects.all()
        
        # Make sure administrative_unit, department and division fields are not required initially (will be validated in clean)
        self.fields['administrative_unit'].required = False
        self.fields['department'].required = False
        self.fields['division'].required = False
        
        # Filter querysets based on instance values if updating
        if self.instance and self.instance.pk:
            # If updating, filter administrative units and divisions based on existing values
            if self.instance.sector:
                self.fields['administrative_unit'].queryset = AdministrativeUnit.objects.filter(
                    Q(sector=self.instance.sector) | Q(is_dummy=True)
                ).distinct()
            else:
                self.fields['administrative_unit'].queryset = AdministrativeUnit.objects.filter(is_dummy=True)

            if getattr(self.instance, 'administrative_unit', None):
                self.fields['division'].queryset = Division.objects.filter(
                    Q(administrative_unit=self.instance.administrative_unit) | Q(is_dummy=True)
                ).distinct()
            else:
                self.fields['division'].queryset = Division.objects.filter(is_dummy=True)

            if getattr(self.instance, 'division', None):
                self.fields['department'].queryset = Department.objects.filter(
                    Q(division=self.instance.division) | Q(is_dummy=True)
                ).distinct()
            else:
                self.fields['department'].queryset = Department.objects.filter(is_dummy=True)

            if getattr(self.instance, 'department', None):
                self.fields['department'].queryset = Department.objects.filter(
                    Q(pk=self.instance.department.pk) |
                    Q(division=self.instance.division) |
                    Q(is_dummy=True)
                ).distinct()
        else:
            # For new records, set defaults to "غير محدد" (dummy records)
            # Get dummy records
            dummy_sector = Sector.objects.filter(name='غير محدد', is_dummy=True).first()
            dummy_unit = AdministrativeUnit.objects.filter(name='غير محدد', is_dummy=True).first()
            dummy_division = Division.objects.filter(name='غير محدد', is_dummy=True).first()
            dummy_department = Department.objects.filter(name='غير محدد', is_dummy=True).first()
            
            # Set default values to dummy records
            if dummy_sector and not self.initial.get('sector'):
                self.initial['sector'] = dummy_sector.pk
            if dummy_unit and not self.initial.get('administrative_unit'):
                self.initial['administrative_unit'] = dummy_unit.pk
            if dummy_division and not self.initial.get('division'):
                self.initial['division'] = dummy_division.pk
            if dummy_department and not self.initial.get('department'):
                self.initial['department'] = dummy_department.pk
            
            # Start with querysets that include dummy records
            self.fields['administrative_unit'].queryset = AdministrativeUnit.objects.filter(is_dummy=True)
            self.fields['division'].queryset = Division.objects.filter(is_dummy=True)
            self.fields['department'].queryset = Department.objects.filter(is_dummy=True)
        
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
            admin_unit_id = self.data.get('administrative_unit')
            department_id = self.data.get('department')
            division_id = self.data.get('division')
            
            # Update querysets based on submitted values BEFORE validation
            if sector_id:
                try:
                    sector = Sector.objects.get(pk=sector_id)
                    # Update administrative unit queryset to include units for this sector
                    self.fields['administrative_unit'].queryset = AdministrativeUnit.objects.filter(
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
                                sector_units = AdministrativeUnit.objects.filter(
                                    Q(sector=sector) | Q(is_dummy=True)
                                ).distinct()
                                self.fields['division'].queryset = Division.objects.filter(
                                    Q(administrative_unit__in=sector_units) | Q(is_dummy=True) | Q(pk=division.pk)
                                ).distinct()
                        except Division.DoesNotExist:
                            pass
                except (Sector.DoesNotExist, ValueError):
                    pass
            
            if admin_unit_id:
                try:
                    administrative_unit = AdministrativeUnit.objects.get(pk=admin_unit_id)
                    # Update division queryset to include divisions for this administrative unit
                    self.fields['division'].queryset = Division.objects.filter(
                        Q(administrative_unit=administrative_unit) | Q(is_dummy=True)
                    ).distinct()
                except (AdministrativeUnit.DoesNotExist, ValueError):
                    pass

            if division_id:
                try:
                    division = Division.objects.get(pk=division_id)
                    if division not in self.fields['division'].queryset:
                        self.fields['division'].queryset = Division.objects.filter(
                            Q(pk=division.pk) | Q(is_dummy=True)
                        ).distinct()
                    self.fields['department'].queryset = Department.objects.filter(
                        Q(division=division) | Q(is_dummy=True)
                    ).distinct()
                except (Division.DoesNotExist, ValueError):
                    pass
            elif department_id:
                try:
                    department = Department.objects.get(pk=department_id)
                    if department not in self.fields['department'].queryset:
                        self.fields['department'].queryset = Department.objects.filter(
                            Q(pk=department.pk) | Q(is_dummy=True)
                        ).distinct()
                except (Department.DoesNotExist, ValueError):
                    pass
        
        # Call parent full_clean to proceed with normal validation
        super().full_clean()
    
    def clean(self):
        cleaned_data = super().clean()
        sector = cleaned_data.get('sector')
        administrative_unit = cleaned_data.get('administrative_unit')
        department = cleaned_data.get('department')
        division = cleaned_data.get('division')
        fleet_no = (cleaned_data.get('fleet_no') or '').strip()
        plate_no_en = (cleaned_data.get('plate_no_en') or '').strip()
        plate_no_ar = (cleaned_data.get('plate_no_ar') or '').strip()

        # Unique constraints validation with Arabic messages
        duplicate_errors = {}
        qs_base = Car.objects.all()
        if self.instance.pk:
            qs_base = qs_base.exclude(pk=self.instance.pk)

        if fleet_no:
            if qs_base.filter(fleet_no__iexact=fleet_no).exists():
                duplicate_errors['fleet_no'] = 'رقم الأسطول مستخدم بالفعل، يرجى إدخال رقم مختلف.'

        if plate_no_en:
            if qs_base.filter(plate_no_en__iexact=plate_no_en).exists():
                duplicate_errors['plate_no_en'] = 'رقم اللوحة (الإنجليزية) مستخدم بالفعل، يرجى إدخال رقم مختلف.'

        if plate_no_ar:
            if qs_base.filter(plate_no_ar=plate_no_ar).exists():
                duplicate_errors['plate_no_ar'] = 'رقم اللوحة (العربية) مستخدم بالفعل، يرجى إدخال رقم مختلف.'

        if duplicate_errors:
            raise forms.ValidationError(duplicate_errors)
        
        # Validation for new records - division is required
        # For existing records, allow NULL values (backward compatibility)
        if not self.instance.pk and not division:
            raise forms.ValidationError({
                'division': 'يجب اختيار دائرة (Division is required for new records).'
            })
        
        # If updating and all hierarchy fields are NULL, that's okay (backward compatibility)
        if self.instance.pk and not sector and not administrative_unit and not department and not division:
            return cleaned_data
        
        # Validate hierarchy consistency
        if division:
            if administrative_unit and division.administrative_unit != administrative_unit:
                # Special case: Allow main dummy division "غير محدد" to be selected
                # with any administrative unit (it's a fallback option that should always be available)
                if division.name == 'غير محدد' and division.is_dummy:
                    pass  # Allow combination with any administrative unit
                else:
                    raise forms.ValidationError({
                        'division': 'الدائرة المختارة لا تنتمي للإدارة المحددة.'
                    })
            elif not administrative_unit:
                # If division is selected without administrative unit, set it from division
                cleaned_data['administrative_unit'] = division.administrative_unit
        
        if administrative_unit:
            if sector and administrative_unit.sector != sector:
                # Special case: Allow main dummy administrative unit "غير محدد" to be selected
                if administrative_unit.name == 'غير محدد' and administrative_unit.is_dummy:
                    pass
                else:
                    raise forms.ValidationError({
                        'administrative_unit': 'الإدارة المختارة لا تنتمي للقطاع المحدد.'
                    })
            elif not sector and administrative_unit.sector:
                # If administrative unit is selected without sector, set sector from administrative unit
                cleaned_data['sector'] = administrative_unit.sector

        if department:
            department_division = department.division
            department_unit = department.administrative_unit
            department_sector = department.sector

            if division:
                if department_division and department_division != division:
                    if department.name == 'غير محدد' and department.is_dummy:
                        pass
                    else:
                        raise forms.ValidationError({
                            'department': 'القسم المختار لا ينتمي للدائرة المحددة.'
                        })
            elif department_division:
                cleaned_data['division'] = department_division

            if administrative_unit:
                if department_unit and department_unit != administrative_unit:
                    if department.name == 'غير محدد' and department.is_dummy:
                        pass
                    else:
                        raise forms.ValidationError({
                            'department': 'القسم المختار لا ينتمي للإدارة المحددة.'
                        })
            elif department_unit:
                cleaned_data['administrative_unit'] = department_unit

            if sector and department_sector and department_sector != sector:
                if department.name == 'غير محدد' and department.is_dummy:
                    pass
                else:
                    raise forms.ValidationError({
                        'department': 'القسم المختار لا يتوافق مع القطاع المحدد.'
                    })
            elif not sector and department_sector:
                cleaned_data['sector'] = department_sector
        
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