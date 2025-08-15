"""Generic forms"""
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from ..models import EquipmentModel, Maintenance


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