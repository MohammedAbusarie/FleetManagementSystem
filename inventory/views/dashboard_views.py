"""Dashboard views"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date
from ..services import CarService, EquipmentService
from .auth_views import is_admin

car_service = CarService()
equipment_service = EquipmentService()


@login_required
@user_passes_test(is_admin)
def dashboard_view(request):
    """Dashboard view with expiry filtering"""
    expiry_status = request.GET.get('expiry_status', 'about_to_expire')
    expiry_days = request.GET.get('expiry_days', 30)
    
    try:
        expiry_days = int(expiry_days)
    except ValueError:
        expiry_days = 30
    
    today = date.today()
    
    # Use services for data retrieval
    cars_expiring = car_service.get_expiring_cars(expiry_status, expiry_days)
    equipment_expiring = equipment_service.get_expiring_equipment(expiry_status, expiry_days)
    
    context = {
        'cars_expiring': cars_expiring[:20],
        'equipment_expiring': equipment_expiring[:20],
        'expiry_days': expiry_days,
        'expiry_status': expiry_status,
        'today': today,
    }
    return render(request, 'inventory/dashboard.html', context)
