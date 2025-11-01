"""Generic table views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.apps import apps
from ..translation_utils import get_verbose_model_translations, get_model_arabic_name, get_message_template
from ..forms import EquipmentModelForm, SectorForm, DepartmentForm, DivisionForm
from .auth_views import is_admin
from ..utils.decorators import admin_or_permission_required, admin_or_permission_required_with_message
from ..utils.helpers import has_permission, log_user_action, get_client_ip
from ..services.rbac_service import LoggingService


@login_required
@admin_or_permission_required_with_message('generic_tables', 'read')
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
@admin_or_permission_required_with_message('generic_tables', 'read')
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
    
    # Custom ordering for hierarchy models
    if model_name == 'Sector':
        objects = model.objects.all().order_by('-is_dummy', 'name')
    elif model_name == 'Department':
        objects = model.objects.all().order_by('-is_dummy', 'sector__name', 'name')
    elif model_name == 'Division':
        objects = model.objects.all().order_by('-is_dummy', 'department__name', 'name')
    else:
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
@admin_or_permission_required_with_message('generic_tables', 'create')
def generic_table_create_view(request, model_name):
    """Generic table create view"""
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    # Use specific forms for models with special fields
    form_class = None
    if model_name == 'EquipmentModel':
        form_class = EquipmentModelForm
    elif model_name == 'Sector':
        form_class = SectorForm
    elif model_name == 'Department':
        form_class = DepartmentForm
    elif model_name == 'Division':
        form_class = DivisionForm
    
    if form_class:
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                obj = form.save()
                # Log the action
                log_user_action(
                    request.user,
                    'create',
                    module_name='generic_tables',
                    object_id=str(obj.pk),
                    description=f"تم إنشاء {get_model_arabic_name(model_name)}: {obj.name if hasattr(obj, 'name') else str(obj)}",
                    ip_address=get_client_ip(request)
                )
                messages.success(request, get_message_template('create_success', model_name, 'create'))
                return redirect('generic_table_detail', model_name=model_name)
            else:
                messages.error(request, get_message_template('validation_error'))
        else:
            form = form_class()
    else:
        # Handle other models with simple name field
        if request.method == 'POST':
            name = request.POST.get('name')
            try:
                obj = model.objects.create(name=name)
                # Log the action
                log_user_action(
                    request.user,
                    'create',
                    module_name='generic_tables',
                    object_id=str(obj.pk),
                    description=f"تم إنشاء {get_model_arabic_name(model_name)}: {name}",
                    ip_address=get_client_ip(request)
                )
                messages.success(request, get_message_template('create_success', model_name, 'create'))
                return redirect('generic_table_detail', model_name=model_name)
            except Exception as e:
                messages.error(request, get_message_template('create_error', model_name, 'create'))
        else:
            form = None
    
    context = {
        'model_name': model_name,
        'model_name_arabic': get_model_arabic_name(model_name),
        'form': form
    }
    return render(request, 'inventory/generic_table_form.html', context)


@login_required
@admin_or_permission_required_with_message('generic_tables', 'update')
def generic_table_update_view(request, model_name, pk):
    """Generic table update view"""
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    obj = get_object_or_404(model, pk=pk)
    
    # Prevent editing protected default records
    if model_name in ['Sector', 'Department', 'Division']:
        if hasattr(obj, 'is_protected_default') and obj.is_protected_default:
            messages.error(
                request,
                'لا يمكن تعديل السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.'
            )
            return redirect('generic_table_detail', model_name=model_name)
    
    # Use specific forms for models with special fields
    form_class = None
    if model_name == 'EquipmentModel':
        form_class = EquipmentModelForm
    elif model_name == 'Sector':
        form_class = SectorForm
    elif model_name == 'Department':
        form_class = DepartmentForm
    elif model_name == 'Division':
        form_class = DivisionForm
    
    if form_class:
        if request.method == 'POST':
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                obj = form.save()
                # Log the action
                log_user_action(
                    request.user,
                    'update',
                    module_name='generic_tables',
                    object_id=str(obj.pk),
                    description=f"تم تحديث {get_model_arabic_name(model_name)}: {obj.name if hasattr(obj, 'name') else str(obj)}",
                    ip_address=get_client_ip(request)
                )
                messages.success(request, get_message_template('update_success', model_name, 'update'))
                return redirect('generic_table_detail', model_name=model_name)
            else:
                messages.error(request, get_message_template('validation_error'))
        else:
            form = form_class(instance=obj)
    else:
        # Handle other models with simple name field
        if request.method == 'POST':
            name = request.POST.get('name')
            
            try:
                obj.name = name
                obj.save()
                # Log the action
                log_user_action(
                    request.user,
                    'update',
                    module_name='generic_tables',
                    object_id=str(obj.pk),
                    description=f"تم تحديث {get_model_arabic_name(model_name)}: {name}",
                    ip_address=get_client_ip(request)
                )
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
        'form': form
    }
    return render(request, 'inventory/generic_table_form.html', context)


@login_required
@admin_or_permission_required_with_message('generic_tables', 'delete')
def generic_table_delete_view(request, model_name, pk):
    """Generic table delete view"""
    try:
        model = apps.get_model('inventory', model_name)
    except LookupError:
        messages.error(request, get_message_template('not_found', model_name))
        return redirect('generic_tables')
    
    obj = get_object_or_404(model, pk=pk)
    
    # Prevent deletion of "غير محدد" (dummy) records for hierarchy models
    if model_name in ['Sector', 'Department', 'Division']:
        if hasattr(obj, 'is_protected_default') and obj.is_protected_default:
            messages.error(
                request,
                'لا يمكن حذف السجل "غير محدد" لأنه قيمة افتراضية أساسية في النظام.'
            )
            return redirect('generic_table_detail', model_name=model_name)
    
    if request.method == 'POST':
        obj_name = obj.name if hasattr(obj, 'name') else str(obj)  # Store before deletion
        obj_pk = str(obj.pk)
        obj.delete()
        
        # Log the action
        log_user_action(
            request.user,
            'delete',
            module_name='generic_tables',
            object_id=obj_pk,
            description=f"تم حذف {get_model_arabic_name(model_name)}: {obj_name}",
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, get_message_template('delete_success', model_name, 'delete'))
        return redirect('generic_table_detail', model_name=model_name)
    
    context = {
        'model_name': model_name, 
        'model_name_arabic': get_model_arabic_name(model_name),
        'object': obj
    }
    return render(request, 'inventory/generic_table_confirm_delete.html', context)
