"""Views package - maintains backward compatibility with views.py"""
# Import all views from submodules
from .auth_views import is_admin, login_view, logout_view
from .dashboard_views import dashboard_view
from .car_views import (
    car_list_view,
    car_create_view,
    car_update_view,
    car_detail_view,
    car_delete_view,
)
from .equipment_views import (
    equipment_list_view,
    equipment_detail_json,
    equipment_create_view,
    equipment_update_view,
    equipment_detail_view,
    equipment_delete_view,
)
from .generic_table_views import (
    generic_tables_view,
    generic_table_detail_view,
    generic_table_create_view,
    generic_table_update_view,
    generic_table_delete_view,
)
from .media_views import secure_media_view

# Export all views (maintains backward compatibility)
__all__ = [
    'is_admin',
    'login_view',
    'logout_view',
    'dashboard_view',
    'car_list_view',
    'car_create_view',
    'car_update_view',
    'car_detail_view',
    'car_delete_view',
    'equipment_list_view',
    'equipment_detail_json',
    'equipment_create_view',
    'equipment_update_view',
    'equipment_detail_view',
    'equipment_delete_view',
    'generic_tables_view',
    'generic_table_detail_view',
    'generic_table_create_view',
    'generic_table_update_view',
    'generic_table_delete_view',
    'secure_media_view',
]
