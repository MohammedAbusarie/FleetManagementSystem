"""API views for dynamic filtering"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ..models import Sector, Department, Division


@require_http_methods(["GET"])
def sectors_list(request):
    """List all sectors"""
    sectors = Sector.objects.all().order_by('name')
    data = [{
        'id': sector.id,
        'name': sector.name,
        'is_dummy': sector.is_dummy
    } for sector in sectors]
    return JsonResponse({'sectors': data})


@require_http_methods(["GET"])
def departments_by_sector(request):
    """Get departments filtered by sector"""
    sector_id = request.GET.get('sector_id')
    
    # ALWAYS get the main dummy department "غير محدد" - it should always be available
    main_dummy_dept = Department.objects.filter(
        name='غير محدد',
        is_dummy=True
    ).first()
    
    if sector_id:
        try:
            sector = Sector.objects.get(id=sector_id)
            # Get all departments for this sector (including dummy departments)
            departments = Department.objects.filter(sector=sector)
            
            # ALWAYS include the main dummy department "غير محدد" regardless of selected sector
            # This ensures users can always select "غير محدد" as a fallback option
            departments_list = list(departments)
            if main_dummy_dept:
                # Check if it's already in the list (by ID)
                if not any(d.id == main_dummy_dept.id for d in departments_list):
                    departments_list.append(main_dummy_dept)
        except Sector.DoesNotExist:
            departments_list = []
            # Even if sector doesn't exist, include dummy department
            if main_dummy_dept:
                departments_list = [main_dummy_dept]
    else:
        # If no sector_id provided, return all departments
        departments_list = list(Department.objects.all())
    # Separate dummy "غير محدد" from others
    # Only include ONE dummy department "غير محدد" (the main one)
    dummy_depts = [d for d in departments_list if d.is_dummy and d.name == 'غير محدد']
    # If multiple dummy depts exist, only keep the first one (main dummy)
    if len(dummy_depts) > 1:
        dummy_depts = [dummy_depts[0]]
    
    other_depts = [d for d in departments_list if d not in dummy_depts]
    # Sort other departments by name
    other_depts = sorted(other_depts, key=lambda x: x.name)
    # Combine: dummy first, then others
    departments_list = dummy_depts + other_depts
    
    data = [{
        'id': dept.id,
        'name': dept.name,
        'is_dummy': dept.is_dummy,
        'sector_id': dept.sector.id if dept.sector else None
    } for dept in departments_list]
    
    return JsonResponse({'departments': data})


@require_http_methods(["GET"])
def divisions_by_department(request):
    """Get divisions filtered by department"""
    department_id = request.GET.get('department_id')
    
    # ALWAYS get the main dummy division "غير محدد" - it should always be available
    main_dummy_div = Division.objects.filter(
        name='غير محدد',
        is_dummy=True
    ).first()
    
    if department_id:
        try:
            department = Department.objects.get(id=department_id)
            # Get all divisions for this department
            divisions = Division.objects.filter(department=department)
            
            # ALWAYS include the main dummy division "غير محدد" regardless of selected department
            # This ensures users can always select "غير محدد" as a fallback option
            divisions_list = list(divisions)
            if main_dummy_div:
                # Check if it's already in the list (by ID)
                if not any(d.id == main_dummy_div.id for d in divisions_list):
                    divisions_list.append(main_dummy_div)
        except Department.DoesNotExist:
            divisions_list = []
            # Even if department doesn't exist, include dummy division
            if main_dummy_div:
                divisions_list = [main_dummy_div]
    else:
        # If no department_id provided, return all divisions
        divisions_list = list(Division.objects.all())
    # Separate dummy "غير محدد" from others
    # Only include ONE dummy division "غير محدد" (the main one)
    dummy_divs = [d for d in divisions_list if d.is_dummy and d.name == 'غير محدد']
    # If multiple dummy divs exist, only keep the first one (main dummy)
    if len(dummy_divs) > 1:
        dummy_divs = [dummy_divs[0]]
    
    other_divs = [d for d in divisions_list if d not in dummy_divs]
    # Sort other divisions by name
    other_divs = sorted(other_divs, key=lambda x: x.name)
    # Combine: dummy first, then others
    divisions_list = dummy_divs + other_divs
    
    data = [{
        'id': div.id,
        'name': div.name,
        'is_dummy': div.is_dummy,
        'department_id': div.department.id if div.department else None
    } for div in divisions_list]
    
    return JsonResponse({'divisions': data})

