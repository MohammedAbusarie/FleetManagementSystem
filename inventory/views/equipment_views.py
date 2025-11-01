"""Equipment-related views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib import messages
from ..models import Equipment, Maintenance, CalibrationCertificateImage, Region, EquipmentImage, FireExtinguisherInspectionRecord, FireExtinguisherImage
from ..forms import EquipmentForm, EquipmentMaintenanceFormSet, EquipmentLicenseRecordFormSet, EquipmentInspectionRecordFormSet, FireExtinguisherInspectionRecordFormSet
from ..services import EquipmentService
from ..translation_utils import get_message_template
from .auth_views import is_admin
from ..utils.decorators import admin_or_permission_required, admin_or_permission_required_with_message
from ..utils.helpers import has_permission, log_user_action, get_client_ip
from ..services.rbac_service import LoggingService

equipment_service = EquipmentService()


@login_required
@admin_or_permission_required_with_message('equipment', 'read')
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
        'equipment_license_start_date': equipment.current_license_record.start_date.strftime('%Y-%m-%d') if equipment.current_license_record else None,
        'equipment_license_end_date': equipment.current_license_record.end_date.strftime('%Y-%m-%d') if equipment.current_license_record else None,
        'annual_inspection_start_date': equipment.current_inspection_record.start_date.strftime('%Y-%m-%d') if equipment.current_inspection_record else None,
        'annual_inspection_end_date': equipment.current_inspection_record.end_date.strftime('%Y-%m-%d') if equipment.current_inspection_record else None,
        'fire_extinguisher_inspection_date': equipment.current_fire_extinguisher_record.inspection_date.strftime('%Y-%m-%d') if equipment.current_fire_extinguisher_record else None,
        'fire_extinguisher_expiry_date': equipment.current_fire_extinguisher_record.expiry_date.strftime('%Y-%m-%d') if equipment.current_fire_extinguisher_record else None,
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
@admin_or_permission_required_with_message('equipment', 'create')
def equipment_create_view(request):
    """Equipment create view"""
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        maintenance_formset = EquipmentMaintenanceFormSet(request.POST, request.FILES)
        license_formset = EquipmentLicenseRecordFormSet(request.POST)
        inspection_formset = EquipmentInspectionRecordFormSet(request.POST)
        fire_extinguisher_formset = FireExtinguisherInspectionRecordFormSet(request.POST)
        
        if form.is_valid() and maintenance_formset.is_valid() and license_formset.is_valid() and inspection_formset.is_valid() and fire_extinguisher_formset.is_valid():
            equipment = form.save(commit=False)
            equipment.save()
            
            # Handle multiple equipment images
            files = request.FILES.getlist('equipment_images')
            for f in files:
                EquipmentImage.objects.create(equipment=equipment, image=f)
            
            # Handle multiple calibration certificate images
            files = request.FILES.getlist('calibration_certificates')
            for f in files:
                CalibrationCertificateImage.objects.create(equipment=equipment, image=f)
            
            # Handle multiple fire extinguisher images
            files = request.FILES.getlist('fire_extinguisher_images')
            for f in files:
                FireExtinguisherImage.objects.create(equipment=equipment, image=f)
            
            # Save license records
            license_instances = license_formset.save(commit=False)
            for obj in license_instances:
                obj.equipment = equipment
                obj.save()
            
            # Save inspection records
            inspection_instances = inspection_formset.save(commit=False)
            for obj in inspection_instances:
                obj.equipment = equipment
                obj.save()
            
            # Save fire extinguisher records
            fire_extinguisher_instances = fire_extinguisher_formset.save(commit=False)
            for obj in fire_extinguisher_instances:
                obj.equipment = equipment
                obj.save()
            
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
        license_formset = EquipmentLicenseRecordFormSet()
        inspection_formset = EquipmentInspectionRecordFormSet()
        fire_extinguisher_formset = FireExtinguisherInspectionRecordFormSet()
    
    context = {
        'form': form,
        'maintenance_formset': maintenance_formset,
        'license_formset': license_formset,
        'inspection_formset': inspection_formset,
        'fire_extinguisher_formset': fire_extinguisher_formset,
        'action': 'Create',
        'all_regions': Region.objects.all()
    }
    return render(request, 'inventory/equipment_form.html', context)


@login_required
@admin_or_permission_required_with_message('equipment', 'update')
def equipment_update_view(request, pk):
    """Equipment update view"""
    equipment = get_object_or_404(Equipment.objects.select_related('sector', 'department', 'division'), pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        maintenance_formset = EquipmentMaintenanceFormSet(
            request.POST,
            request.FILES,
            instance=equipment,
        )
        license_formset = EquipmentLicenseRecordFormSet(request.POST, instance=equipment)
        inspection_formset = EquipmentInspectionRecordFormSet(request.POST, instance=equipment)
        fire_extinguisher_formset = FireExtinguisherInspectionRecordFormSet(request.POST, instance=equipment)
        
        if form.is_valid() and maintenance_formset.is_valid() and license_formset.is_valid() and inspection_formset.is_valid() and fire_extinguisher_formset.is_valid():
            equipment = form.save(commit=False)
            # Handle image update: if a new image is uploaded, it overwrites the old one.
            # If no new image is uploaded, the old one is kept (default behavior of ModelForm).
            equipment.save()
            
            # Handle multiple equipment images
            files = request.FILES.getlist('equipment_images')
            for f in files:
                EquipmentImage.objects.create(equipment=equipment, image=f)
            
            # Handle equipment image deletion
            images_to_delete = request.POST.get('images_to_delete', '')
            if images_to_delete:
                image_ids = [int(id) for id in images_to_delete.split(',') if id.strip()]
                if image_ids:
                    EquipmentImage.objects.filter(id__in=image_ids).delete()
            
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
            
            # Handle multiple fire extinguisher images
            files = request.FILES.getlist('fire_extinguisher_images')
            for f in files:
                FireExtinguisherImage.objects.create(equipment=equipment, image=f)
            
            # Handle fire extinguisher image deletion
            fire_extinguisher_images_to_delete = request.POST.get('fire_extinguisher_images_to_delete', '')
            if fire_extinguisher_images_to_delete:
                image_ids = [int(id) for id in fire_extinguisher_images_to_delete.split(',') if id.strip()]
                if image_ids:
                    FireExtinguisherImage.objects.filter(id__in=image_ids).delete()
            
            # Save license records
            license_instances = license_formset.save(commit=False)
            for obj in license_instances:
                obj.equipment = equipment
                obj.save()
            
            # Handle deleted license instances
            for obj in license_formset.deleted_objects:
                obj.delete()
            
            # Save inspection records
            inspection_instances = inspection_formset.save(commit=False)
            for obj in inspection_instances:
                obj.equipment = equipment
                obj.save()
            
            # Handle deleted inspection instances
            for obj in inspection_formset.deleted_objects:
                obj.delete()
            
            # Save fire extinguisher records
            fire_extinguisher_instances = fire_extinguisher_formset.save(commit=False)
            for obj in fire_extinguisher_instances:
                obj.equipment = equipment
                obj.save()
            
            # Handle deleted fire extinguisher instances
            for obj in fire_extinguisher_formset.deleted_objects:
                obj.delete()
                
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
        # Ensure formsets load existing records
        license_formset = EquipmentLicenseRecordFormSet(instance=equipment, queryset=equipment.license_records.all())
        inspection_formset = EquipmentInspectionRecordFormSet(instance=equipment, queryset=equipment.inspection_records.all())
        fire_extinguisher_formset = FireExtinguisherInspectionRecordFormSet(instance=equipment, queryset=equipment.fire_extinguisher_records.all())
    
    context = {
        'form': form,
        'maintenance_formset': maintenance_formset,
        'license_formset': license_formset,
        'inspection_formset': inspection_formset,
        'fire_extinguisher_formset': fire_extinguisher_formset,
        'action': 'Update',
        'equipment': equipment,
        'all_regions': Region.objects.all()
    }
    return render(request, 'inventory/equipment_form.html', context)


@login_required
@admin_or_permission_required_with_message('equipment', 'read')
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
    
    # Get historical records
    license_records = equipment.license_records.all().order_by('-start_date')
    inspection_records = equipment.inspection_records.all().order_by('-start_date')
    fire_extinguisher_records = equipment.fire_extinguisher_records.all().order_by('-inspection_date')
    
    context = {
        'equipment': equipment,
        'maintenance_records': maintenance_records,
        'calibration_certificates': calibration_certificates,
        'license_records': license_records,
        'inspection_records': inspection_records,
        'fire_extinguisher_records': fire_extinguisher_records,
    }
    return render(request, 'inventory/equipment_detail.html', context)


@login_required
@admin_or_permission_required_with_message('equipment', 'delete')
def equipment_delete_view(request, pk):
    """Equipment delete view"""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, get_message_template('delete_success', 'Equipment', 'delete'))
        return redirect('equipment_list')
    
    context = {'equipment': equipment}
    return render(request, 'inventory/equipment_confirm_delete.html', context)
