"""Equipment-related views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib import messages
from ..models import Equipment, Maintenance, CalibrationCertificateImage, Region
from ..forms import EquipmentForm, EquipmentMaintenanceFormSet
from ..services import EquipmentService
from ..translation_utils import get_message_template
from .auth_views import is_admin

equipment_service = EquipmentService()


@login_required
@user_passes_test(is_admin)
def equipment_list_view(request):
    """Equipment list view with search, pagination, and sorting"""
    search_query = request.GET.get('search_query', '')
    search_field = request.GET.get('search_field', 'door_no')
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    
    # Get equipment with maintenance info
    equipment = equipment_service.get_equipment_with_maintenance()

    # Apply search
    if search_query and search_field:
        equipment = equipment_service.search_equipment(equipment, search_field, search_query)

    # Apply sorting
    equipment = equipment_service.sort(equipment, sort_by, sort_order)

    # Pagination
    paginator = Paginator(equipment, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    search_fields = [
        ('door_no', 'رقم الباب'),
        ('plate_no', 'رقم اللوحة'),
        ('manufacturer', 'الشركة المصنعة'),
    ]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'search_field': search_field,
        'search_fields': search_fields,
        'sort_by': sort_by.replace('-' , ''),
        'sort_order': sort_order,
    }
    return render(request, 'inventory/equipment_list.html', context)


@login_required
@user_passes_test(is_admin)
def equipment_detail_json(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    data = {
        'door_no': equipment.door_no,
        'plate_no': equipment.plate_no,
        'manufacture_year': equipment.manufacture_year,
        'manufacturer': equipment.manufacturer.name,
        'model': equipment.model.name,
        'location': equipment.location.name,
        'sector': equipment.sector.name,
        'status': equipment.status,
        'status_display': equipment.get_status_display(),
        'equipment_license_start_date': equipment.equipment_license_start_date.strftime('%Y-%m-%d') if equipment.equipment_license_start_date else None,
        'equipment_license_end_date': equipment.equipment_license_end_date.strftime('%Y-%m-%d') if equipment.equipment_license_end_date else None,
        'annual_inspection_start_date': equipment.annual_inspection_start_date.strftime('%Y-%m-%d') if equipment.annual_inspection_start_date else None,
        'annual_inspection_end_date': equipment.annual_inspection_end_date.strftime('%Y-%m-%d') if equipment.annual_inspection_end_date else None,
        'equipment_image_url': reverse('secure_media', kwargs={'path': str(equipment.equipment_image)}) if equipment.equipment_image else None,
        'calibration_certificates': [{'image_url': reverse('secure_media', kwargs={'path': str(cert.image)})} for cert in equipment.calibration_certificates.all()],
        'maintenance_records': [{
            'maintenance_date': maint.maintenance_date.strftime('%Y-%m-%d') if maint.maintenance_date else None,
            'restoration_date': maint.restoration_date.strftime('%Y-%m-%d') if maint.restoration_date else None,
            'cost': str(maint.cost) if maint.cost else None,
            'description': maint.description,
        } for maint in equipment.maintenance_set.all()],
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
def equipment_create_view(request):
    """Equipment create view"""
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        maintenance_formset = EquipmentMaintenanceFormSet(request.POST, request.FILES)
        
        if form.is_valid() and maintenance_formset.is_valid():
            equipment = form.save()
            
            # Handle multiple calibration certificate images
            files = request.FILES.getlist('calibration_certificates')
            for f in files:
                CalibrationCertificateImage.objects.create(equipment=equipment, image=f)
            
            # Save maintenance records if status is under_maintenance
            if equipment.status == 'under_maintenance':
                instances = maintenance_formset.save(commit=False)
                for obj in instances:
                    obj.content_object = equipment
                    obj.save()
            
            messages.success(request, get_message_template('create_success', 'Equipment', 'create'))
            return redirect('equipment_list')
        else:
            messages.error(request, get_message_template('validation_error'))
    else:
        form = EquipmentForm()
        maintenance_formset = EquipmentMaintenanceFormSet()
    
    context = {
        'form': form,
        'maintenance_formset': maintenance_formset,
        'action': 'Create',
        'all_regions': Region.objects.all()
    }
    return render(request, 'inventory/equipment_form.html', context)


@login_required
@user_passes_test(is_admin)
def equipment_update_view(request, pk):
    """Equipment update view"""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        maintenance_formset = EquipmentMaintenanceFormSet(
            request.POST,
            request.FILES,
            instance=equipment,
        )
        if form.is_valid() and maintenance_formset.is_valid():
            equipment = form.save(commit=False)
            # Handle image update: if a new image is uploaded, it overwrites the old one.
            # If no new image is uploaded, the old one is kept (default behavior of ModelForm).
            equipment.save()
            
            # Handle multiple calibration certificate images
            files = request.FILES.getlist('calibration_certificates')
            for f in files:
                CalibrationCertificateImage.objects.create(equipment=equipment, image=f)
            
            # Handle certificate deletion
            certificates_to_delete = request.POST.get('certificates_to_delete', '')
            if certificates_to_delete:
                cert_ids = [int(id) for id in certificates_to_delete.split(',') if id.strip()]
                if cert_ids:
                    CalibrationCertificateImage.objects.filter(id__in=cert_ids).delete()
                
            # Save maintenance records
            instances = maintenance_formset.save(commit=False)
            for obj in instances:
                obj.content_object = equipment
                obj.save()
            
            # Handle deleted instances
            for obj in maintenance_formset.deleted_objects:
                obj.delete()
            
            messages.success(request, get_message_template('update_success', 'Equipment', 'update'))
            return redirect('equipment_list')
        else:
            messages.error(request, get_message_template('validation_error'))
    else:
        form = EquipmentForm(instance=equipment)
        maintenance_formset = EquipmentMaintenanceFormSet(
            instance=equipment,
        )
    
    context = {
        'form': form,
        'maintenance_formset': maintenance_formset,
        'action': 'Update',
        'equipment': equipment,
        'all_regions': Region.objects.all()
    }
    return render(request, 'inventory/equipment_form.html', context)


@login_required
@user_passes_test(is_admin)
def equipment_detail_view(request, pk):
    """Equipment detail view - comprehensive page showing all equipment information"""
    equipment = get_object_or_404(Equipment, pk=pk)
    
    # Get maintenance records for this equipment
    from django.contrib.contenttypes.models import ContentType
    equipment_content_type = ContentType.objects.get_for_model(Equipment)
    maintenance_records = Maintenance.objects.filter(
        content_type=equipment_content_type,
        object_id=equipment.pk
    ).order_by('-maintenance_date')
    
    # Get calibration certificates
    calibration_certificates = equipment.calibration_certificates.all()
    
    context = {
        'equipment': equipment,
        'maintenance_records': maintenance_records,
        'calibration_certificates': calibration_certificates,
    }
    return render(request, 'inventory/equipment_detail.html', context)


@login_required
@user_passes_test(is_admin)
def equipment_delete_view(request, pk):
    """Equipment delete view"""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, get_message_template('delete_success', 'Equipment', 'delete'))
        return redirect('equipment_list')
    
    context = {'equipment': equipment}
    return render(request, 'inventory/equipment_confirm_delete.html', context)
