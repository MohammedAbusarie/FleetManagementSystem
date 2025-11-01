"""Car-related views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib import messages
from ..models import Car, Maintenance, Region, CarImage
from ..forms import CarForm, CarMaintenanceFormSet, CarLicenseRecordFormSet, CarInspectionRecordFormSet
from ..services import CarService
from ..translation_utils import get_message_template
from .auth_views import is_admin
from ..utils.decorators import admin_or_permission_required, admin_or_permission_required_with_message
from ..utils.helpers import has_permission, log_user_action, get_client_ip
from ..services.rbac_service import LoggingService

car_service = CarService()


@login_required
@admin_or_permission_required_with_message('cars', 'read')
def car_list_view(request):
    """Car list view with search, pagination, and sorting"""
    search_query = request.GET.get('search_query', '')
    search_field = request.GET.get('search_field', 'fleet_no')
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'desc')
    
    # Get cars with maintenance info
    cars = car_service.get_cars_with_maintenance()

    # Apply search
    if search_query and search_field:
        cars = car_service.search_cars(cars, search_field, search_query)

    # Apply sorting
    cars = car_service.sort(cars, sort_by, sort_order)

    # Pagination
    paginator = Paginator(cars, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    search_fields = [
        ('fleet_no', 'رقم الأسطول'),
        ('plate_no_en', 'رقم اللوحة (إنجليزي)'),
        ('plate_no_ar', 'رقم اللوحة (عربي)'),
        ('manufacturer', 'الشركة المصنعة'),
    ]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'search_field': search_field,
        'search_fields': search_fields,
        'sort_by': sort_by.replace('-' , ''), # Pass original sort_by without '-' for template logic
        'sort_order': sort_order,
    }
    return render(request, 'inventory/car_list.html', context)






@login_required
@admin_or_permission_required_with_message('cars', 'create')
def car_create_view(request):
    """Car create view"""
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        maintenance_formset = CarMaintenanceFormSet(request.POST, request.FILES)
        license_formset = CarLicenseRecordFormSet(request.POST)
        inspection_formset = CarInspectionRecordFormSet(request.POST)
        
        if form.is_valid() and maintenance_formset.is_valid() and license_formset.is_valid() and inspection_formset.is_valid():
            car = form.save(commit=False)
            car.save()

            # Handle multiple car images
            files = request.FILES.getlist('car_images')
            for f in files:
                CarImage.objects.create(car=car, image=f)

            # Handle visited regions dynamically
            region_names = request.POST.getlist('visited_regions_dynamic')
            region_objs = []
            for name in region_names:
                name = name.strip()
                if name:
                    region_obj, _ = Region.objects.get_or_create(name=name)
                    region_objs.append(region_obj)
            car.visited_regions.set(region_objs)

            # Save license records
            license_instances = license_formset.save(commit=False)
            for obj in license_instances:
                obj.car = car
                obj.save()

            # Save inspection records
            inspection_instances = inspection_formset.save(commit=False)
            for obj in inspection_instances:
                obj.car = car
                obj.save()

            # Save maintenance records if status is under_maintenance
            if car.status == 'under_maintenance':
                instances = maintenance_formset.save(commit=False)
                for obj in instances:
                    obj.content_object = car
                    obj.save()

            # Log the action
            log_user_action(
                request.user,
                'create',
                module_name='cars',
                object_id=str(car.pk),
                description=f"تم إنشاء سيارة جديدة - رقم الأسطول: {car.fleet_no}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, get_message_template('create_success', 'Car', 'create'))
            return redirect('car_list')
        else:
            messages.error(request, get_message_template('validation_error'))
    else:
        form = CarForm()
        maintenance_formset = CarMaintenanceFormSet()
        license_formset = CarLicenseRecordFormSet()
        inspection_formset = CarInspectionRecordFormSet()

    context = {
        'form': form,
        'maintenance_formset': maintenance_formset,
        'license_formset': license_formset,
        'inspection_formset': inspection_formset,
        'action': 'Create',
        'all_regions': Region.objects.all()
    }
    return render(request, 'inventory/car_form.html', context)


@login_required
@admin_or_permission_required_with_message('cars', 'update')
def car_update_view(request, pk):
    """Car update view"""
    car = get_object_or_404(Car.objects.select_related('sector', 'department', 'division'), pk=pk)
    from django.contrib.contenttypes.models import ContentType
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        maintenance_formset = CarMaintenanceFormSet(request.POST, request.FILES, instance=car)
        license_formset = CarLicenseRecordFormSet(request.POST, instance=car)
        inspection_formset = CarInspectionRecordFormSet(request.POST, instance=car)
        
        if form.is_valid() and maintenance_formset.is_valid() and license_formset.is_valid() and inspection_formset.is_valid():
            car = form.save(commit=False)
            car.save()

            # Handle multiple car images
            files = request.FILES.getlist('car_images')
            for f in files:
                CarImage.objects.create(car=car, image=f)
            
            # Handle image deletion
            images_to_delete = request.POST.get('images_to_delete', '')
            if images_to_delete:
                image_ids = [int(id) for id in images_to_delete.split(',') if id.strip()]
                if image_ids:
                    CarImage.objects.filter(id__in=image_ids).delete()

            # Handle visited regions dynamically
            region_names = request.POST.getlist('visited_regions_dynamic')
            region_objs = []
            for name in region_names:
                name = name.strip()
                if name:
                    region_obj, _ = Region.objects.get_or_create(name=name)
                    region_objs.append(region_obj)
            car.visited_regions.set(region_objs)
            
            # Save license records
            license_instances = license_formset.save(commit=False)
            for obj in license_instances:
                obj.car = car
                obj.save()
            
            # Handle deleted license instances
            for obj in license_formset.deleted_objects:
                obj.delete()
            
            # Save inspection records
            inspection_instances = inspection_formset.save(commit=False)
            for obj in inspection_instances:
                obj.car = car
                obj.save()
            
            # Handle deleted inspection instances
            for obj in inspection_formset.deleted_objects:
                obj.delete()
            
            # Save maintenance records
            instances = maintenance_formset.save(commit=False)
            for obj in instances:
                obj.content_object = car
                obj.save()
            
            # Handle deleted instances
            for obj in maintenance_formset.deleted_objects:
                obj.delete()

            # Log the action
            log_user_action(
                request.user,
                'update',
                module_name='cars',
                object_id=str(car.pk),
                description=f"تم تحديث سيارة - رقم الأسطول: {car.fleet_no}",
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, get_message_template('update_success', 'Car', 'update'))
            return redirect('car_list')
        else:
            messages.error(request, get_message_template('validation_error'))
    else:
        form = CarForm(instance=car)
        maintenance_formset = CarMaintenanceFormSet(instance=car)
        # Ensure formsets load existing records
        license_formset = CarLicenseRecordFormSet(instance=car, queryset=car.license_records.all())
        inspection_formset = CarInspectionRecordFormSet(instance=car, queryset=car.inspection_records.all())
    
    context = {
        'form': form,
        'maintenance_formset': maintenance_formset,
        'license_formset': license_formset,
        'inspection_formset': inspection_formset,
        'action': 'Update',
        'car': car,
        'all_regions': Region.objects.all()
    }
    return render(request, 'inventory/car_form.html', context)


@login_required
@admin_or_permission_required_with_message('cars', 'read')
def car_detail_view(request, pk):
    """Car detail view - comprehensive page showing all car information"""
    car = get_object_or_404(Car, pk=pk)
    
    # Get maintenance records for this car
    from django.contrib.contenttypes.models import ContentType
    car_content_type = ContentType.objects.get_for_model(Car)
    maintenance_records = Maintenance.objects.filter(
        content_type=car_content_type,
        object_id=car.pk
    ).order_by('-maintenance_date')
    
    # Get license and inspection records
    license_records = car.license_records.all().order_by('-start_date')
    inspection_records = car.inspection_records.all().order_by('-start_date')
    
    context = {
        'car': car,
        'maintenance_records': maintenance_records,
        'license_records': license_records,
        'inspection_records': inspection_records,
    }
    return render(request, 'inventory/car_detail.html', context)


@login_required
@admin_or_permission_required_with_message('cars', 'delete')
def car_delete_view(request, pk):
    """Car delete view"""
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        fleet_no = car.fleet_no  # Store before deletion
        car_pk = str(car.pk)
        car.delete()
        
        # Log the action
        log_user_action(
            request.user,
            'delete',
            module_name='cars',
            object_id=car_pk,
            description=f"تم حذف سيارة - رقم الأسطول: {fleet_no}",
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, get_message_template('delete_success', 'Car', 'delete'))
        return redirect('car_list')
    
    context = {'car': car}
    return render(request, 'inventory/car_confirm_delete.html', context)
