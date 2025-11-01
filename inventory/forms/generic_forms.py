"""Generic forms"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, HTML
from ..models import EquipmentModel, Maintenance, Sector, Department, Division


class MaintenanceForm(forms.ModelForm):
    """Form for Maintenance model"""
    
    class Meta:
        model = Maintenance
        fields = ['maintenance_date', 'restoration_date', 'cost', 'description']
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'restoration_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'


# Generic DDL Form
class GenericDDLForm(forms.ModelForm):
    """Generic form for DDL tables"""
    
    class Meta:
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'


class EquipmentModelForm(forms.ModelForm):
    """Form for EquipmentModel"""
    
    class Meta:
        model = EquipmentModel
        fields = ['name', 'manufacturer']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.Select(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'


class SectorForm(forms.ModelForm):
    """Form for Sector model"""
    
    class Meta:
        model = Sector
        fields = ['name', 'is_dummy']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_dummy': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'name': 'الاسم',
            'is_dummy': 'قيمة افتراضية'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        # Make fields readonly if this is a protected default record
        if self.instance and self.instance.pk and self.instance.is_protected_default:
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['name'].widget.attrs['disabled'] = True
            self.fields['is_dummy'].widget.attrs['disabled'] = True
            self.fields['is_dummy'].widget.attrs['readonly'] = True
        
        self.helper.layout = Layout(
            Field('name'),
            Field('is_dummy'),
            HTML('<div class="mt-4">'),
            Submit('submit', 'حفظ', css_class='btn btn-primary'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">إلغاء</a>'),
            HTML('</div>')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        # Prevent saving changes to protected default record
        if self.instance and self.instance.pk and self.instance.is_protected_default:
            raise forms.ValidationError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        return cleaned_data


class DepartmentForm(forms.ModelForm):
    """Form for Department model"""
    
    class Meta:
        model = Department
        fields = ['name', 'sector', 'is_dummy']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sector': forms.Select(attrs={'class': 'form-control'}),
            'is_dummy': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'name': 'الاسم',
            'sector': 'القطاع',
            'is_dummy': 'قيمة افتراضية'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sector'].queryset = Sector.objects.all().order_by('name')
        self.fields['sector'].required = False
        
        # Make fields readonly if this is a protected default record
        if self.instance and self.instance.pk and self.instance.is_protected_default:
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['name'].widget.attrs['disabled'] = True
            self.fields['sector'].widget.attrs['disabled'] = True
            self.fields['is_dummy'].widget.attrs['disabled'] = True
            self.fields['is_dummy'].widget.attrs['readonly'] = True
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name'),
            Field('sector'),
            Field('is_dummy'),
            HTML('<div class="mt-4">'),
            Submit('submit', 'حفظ', css_class='btn btn-primary'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">إلغاء</a>'),
            HTML('</div>')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        # Prevent saving changes to protected default record
        if self.instance and self.instance.pk and self.instance.is_protected_default:
            raise forms.ValidationError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        return cleaned_data


class DivisionForm(forms.ModelForm):
    """Form for Division model"""
    
    class Meta:
        model = Division
        fields = ['name', 'department', 'is_dummy']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'is_dummy': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'name': 'الاسم',
            'department': 'الإدارة',
            'is_dummy': 'قيمة افتراضية'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.all().order_by('name')
        self.fields['department'].required = False
        
        # Make fields readonly if this is a protected default record
        if self.instance and self.instance.pk and self.instance.is_protected_default:
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['name'].widget.attrs['disabled'] = True
            self.fields['department'].widget.attrs['disabled'] = True
            self.fields['is_dummy'].widget.attrs['disabled'] = True
            self.fields['is_dummy'].widget.attrs['readonly'] = True
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name'),
            Field('department'),
            Field('is_dummy'),
            HTML('<div class="mt-4">'),
            Submit('submit', 'حفظ', css_class='btn btn-primary'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">إلغاء</a>'),
            HTML('</div>')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        # Prevent saving changes to protected default record
        if self.instance and self.instance.pk and self.instance.is_protected_default:
            raise forms.ValidationError('لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.')
        return cleaned_data


# Search Form
class SearchForm(forms.Form):
    """Generic search form"""
    search_query = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Search...')})
    )
    search_field = forms.ChoiceField(
        required=False,
        widget=forms.RadioSelect()
    )
    
    def __init__(self, *args, **kwargs):
        search_fields = kwargs.pop('search_fields', [])
        super().__init__(*args, **kwargs)
        self.fields['search_field'].choices = search_fields