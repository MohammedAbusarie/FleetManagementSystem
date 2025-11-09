"""API views for dynamic filtering"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from ..models import Sector, AdministrativeUnit, Division


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
def administrative_units_by_sector(request):
    """Get administrative units filtered by sector"""
    sector_id = request.GET.get('sector_id')
    
    main_dummy_unit = AdministrativeUnit.objects.filter(
        name='غير محدد',
        is_dummy=True
    ).first()
    
    if sector_id:
        try:
            sector = Sector.objects.get(id=sector_id)
            units = AdministrativeUnit.objects.filter(sector=sector)
            
            units_list = list(units)
            if main_dummy_unit and not any(u.id == main_dummy_unit.id for u in units_list):
                units_list.append(main_dummy_unit)
        except Sector.DoesNotExist:
            units_list = []
            if main_dummy_unit:
                units_list = [main_dummy_unit]
    else:
        units_list = list(AdministrativeUnit.objects.all())
    
    dummy_units = [u for u in units_list if u.is_dummy and u.name == 'غير محدد']
    if len(dummy_units) > 1:
        dummy_units = [dummy_units[0]]
    
    other_units = [u for u in units_list if u not in dummy_units]
    other_units = sorted(other_units, key=lambda x: x.name)
    units_list = dummy_units + other_units
    
    data = [{
        'id': unit.id,
        'name': unit.name,
        'is_dummy': unit.is_dummy,
        'sector_id': unit.sector.id if unit.sector else None
    } for unit in units_list]
    
    return JsonResponse({'administrative_units': data})


@require_http_methods(["GET"])
def divisions_by_administrative_unit(request):
    """Get divisions filtered by administrative unit"""
    administrative_unit_id = request.GET.get('administrative_unit_id')
    
    main_dummy_div = Division.objects.filter(
        name='غير محدد',
        is_dummy=True
    ).first()
    
    if administrative_unit_id:
        try:
            administrative_unit = AdministrativeUnit.objects.get(id=administrative_unit_id)
            divisions = Division.objects.filter(administrative_unit=administrative_unit)
            
            divisions_list = list(divisions)
            if main_dummy_div and not any(d.id == main_dummy_div.id for d in divisions_list):
                divisions_list.append(main_dummy_div)
        except AdministrativeUnit.DoesNotExist:
            divisions_list = []
            if main_dummy_div:
                divisions_list = [main_dummy_div]
    else:
        divisions_list = list(Division.objects.all())
    
    dummy_divs = [d for d in divisions_list if d.is_dummy and d.name == 'غير محدد']
    if len(dummy_divs) > 1:
        dummy_divs = [dummy_divs[0]]
    
    other_divs = [d for d in divisions_list if d not in dummy_divs]
    other_divs = sorted(other_divs, key=lambda x: x.name)
    divisions_list = dummy_divs + other_divs
    
    data = [{
        'id': div.id,
        'name': div.name,
        'is_dummy': div.is_dummy,
        'administrative_unit_id': div.administrative_unit.id if div.administrative_unit else None
    } for div in divisions_list]
    
    return JsonResponse({'divisions': data})

