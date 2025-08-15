"""Base form components"""
from django import forms


class Select2Widget(forms.Select):
    """Custom Select2 widget for searchable dropdowns"""
    class Media:
        css = {
            'all': ('admin/css/vendor/select2/select2.min.css',)
        }
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/vendor/select2/select2.full.min.js',
            'admin/js/vendor/select2/i18n/ar.js',
        )
    
    def __init__(self, attrs=None, choices=(), **kwargs):
        super().__init__(attrs, choices, **kwargs)
        if attrs is None:
            attrs = {}
        attrs.update({
            'class': 'form-control select2-search',
            'data-language': 'ar',
            'data-placeholder': 'اختر...',
            'data-allow-clear': 'true',
            'data-width': '100%',
            'data-dir': 'rtl'
        })
        self.attrs = attrs
    
    def render(self, name, value, attrs=None, renderer=None):
        """Override render to ensure proper attributes"""
        if attrs is None:
            attrs = {}
        
        # Ensure the select2-search class is always present
        if 'class' in attrs:
            if 'select2-search' not in attrs['class']:
                attrs['class'] += ' select2-search'
        else:
            attrs['class'] = 'form-control select2-search'
        
        # Add data attributes for Select2
        attrs.update({
            'data-language': 'ar',
            'data-placeholder': 'اختر...',
            'data-allow-clear': 'true',
            'data-width': '100%',
            'data-dir': 'rtl'
        })
        
        return super().render(name, value, attrs, renderer)