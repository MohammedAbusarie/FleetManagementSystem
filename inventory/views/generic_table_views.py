"""Generic table views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.apps import apps
from ..translation_utils import get_verbose_model_translations, get_model_arabic_name, get_message_template
from ..forms import EquipmentModelForm
from .auth_views import is_admin


@login_required
@user_passes_test(is_admin)
def generic_tables_view(request):
    """Generic tables management view"""
    # Use the translation utilities for model translations
    model_translations = get_verbose_model_translations()
    
    # Exclude specific models that should not appear in generic tables
    excluded_models = ['Car', 'Equipment', 'Maintenance', 'CalibrationCertificateImage']
    
    # Filter out excluded models
    filtered_translations = {name: trans for name, trans in model_translations.items() 
                           if name not in excluded_models}
    
    # Convert the model names to a structure that includes both English and Arabic names
    ddl_models = [{'name': name, 'arabic': trans} for name, trans in filtered_translations.items()]
    
    context = {'ddl_models': ddl_models}
    return render(request, 'inventory/generic_tables.html', context)


@login_required
@user_passes_test(is_admin)
def generic_table_detail_view(request, model_name):
    """Generic table detail view for CRUD operations"""
    try:
        model = apps.get_model('inventory', model_name)
        # Use translation utilities for Arabic names
        model_translations = get_verbose_model_translations()
        arabic_name = model_translations.get(model_name, model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    objects = model.objects.all().order_by('name') # Default sort for generic tables
    
    context = {
        'model_name': model_name,
        'arabic_name': arabic_name,
        'objects': objects,
    }
    
    # Check if this is an AJAX request
    if request.GET.get('ajax') == '1':
        return render(request, 'inventory/generic_table_content.html', context)
    else:
        return render(request, 'inventory/generic_table_detail.html', context)


@login_required
@user_passes_test(is_admin)
def generic_table_create_view(request, model_name):
    """Generic table create view"""
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    # Use specific form for EquipmentModel
    if model_name == 'EquipmentModel':
        if request.method == 'POST':
            form = EquipmentModelForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, get_message_template('create_success', model_name, 'create'))
                return redirect('generic_table_detail', model_name=model_name)
            else:
                messages.error(request, get_message_template('validation_error'))
        else:
            form = EquipmentModelForm()
    else:
        # Handle other models with simple name field
        if request.method == 'POST':
            name = request.POST.get('name')
            try:
                model.objects.create(name=name)
                messages.success(request, get_message_template('create_success', model_name, 'create'))
                return redirect('generic_table_detail', model_name=model_name)
            except Exception as e:
                messages.error(request, get_message_template('create_error', model_name, 'create'))
        else:
            form = None
    
    context = {
        'model_name': model_name,
        'model_name_arabic': get_model_arabic_name(model_name),
        'form': form if model_name == 'EquipmentModel' else None
    }
    return render(request, 'inventory/generic_table_form.html', context)


@login_required
@user_passes_test(is_admin)
def generic_table_update_view(request, model_name, pk):
    """Generic table update view"""
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    obj = get_object_or_404(model, pk=pk)
    
    # Use specific form for EquipmentModel
    if model_name == 'EquipmentModel':
        if request.method == 'POST':
            form = EquipmentModelForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, get_message_template('update_success', model_name, 'update'))
                return redirect('generic_table_detail', model_name=model_name)
            else:
                messages.error(request, get_message_template('validation_error'))
        else:
            form = EquipmentModelForm(instance=obj)
    else:
        # Handle other models with simple name field
        if request.method == 'POST':
            name = request.POST.get('name')
            
            try:
                obj.name = name
                obj.save()
                messages.success(request, get_message_template('update_success', model_name, 'update'))
                return redirect('generic_table_detail', model_name=model_name)
            except Exception as e:
                messages.error(request, get_message_template('update_error', model_name, 'update'))
        else:
            form = None
    
    context = {
        'model_name': model_name, 
        'model_name_arabic': get_model_arabic_name(model_name),
        'object': obj,
        'form': form if model_name == 'EquipmentModel' else None
    }
    return render(request, 'inventory/generic_table_form.html', context)


@login_required
@user_passes_test(is_admin)
def generic_table_delete_view(request, model_name, pk):
    """Generic table delete view"""
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    obj = get_object_or_404(model, pk=pk)
    
    if request.method == 'POST':
        obj.delete()
        messages.success(request, get_message_template('delete_success', model_name, 'delete'))
        return redirect('generic_table_detail', model_name=model_name)
    
    context = {
        'model_name': model_name, 
        'model_name_arabic': get_model_arabic_name(model_name),
        'object': obj
    }
    return render(request, 'inventory/generic_table_confirm_delete.html', context)
