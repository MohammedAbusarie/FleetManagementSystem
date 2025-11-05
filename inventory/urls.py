from django.urls import path
from . import views
from .views import admin_views, api_views

urlpatterns = [
    # Authentication
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_profile_view, name="account_profile"),

    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Cars
    path("cars/", views.car_list_view, name="car_list"),
    path("cars/create/", views.car_create_view, name="car_create"),
    path("cars/<int:pk>/", views.car_detail_view, name="car_detail"),
    path("cars/<int:pk>/update/", views.car_update_view, name="car_update"),
    path("cars/<int:pk>/delete/", views.car_delete_view, name="car_delete"),

    # Equipment
    path("equipment/", views.equipment_list_view, name="equipment_list"),
    path("equipment/create/", views.equipment_create_view, name="equipment_create"),
    path("equipment/<int:pk>/", views.equipment_detail_view, name="equipment_detail"),
    path("equipment/<int:pk>/update/", views.equipment_update_view, name="equipment_update"),
    path("equipment/<int:pk>/delete/", views.equipment_delete_view, name="equipment_delete"),
    path("equipment/<int:pk>/detail_json/", views.equipment_detail_json, name="equipment_detail_json"),

    # Generic Tables
    path("generic-tables/", views.generic_tables_view, name="generic_tables"),
    path("generic-tables/<str:model_name>/", views.generic_table_detail_view, name="generic_table_detail"),
    path("generic-tables/<str:model_name>/create/", views.generic_table_create_view, name="generic_table_create"),
    path("generic-tables/<str:model_name>/<int:pk>/update/", 
         views.generic_table_update_view, name="generic_table_update"),
    path("generic-tables/<str:model_name>/<int:pk>/delete/", 
         views.generic_table_delete_view, name="generic_table_delete"),

    # Secure Media Files
    path("secure-media/<path:path>", views.secure_media_view, name="secure_media"),

    # API Endpoints for Dynamic Filtering
    path("api/sectors/", api_views.sectors_list, name="api_sectors"),
    path("api/departments/", api_views.departments_by_sector, name="api_departments"),
    path("api/divisions/", api_views.divisions_by_department, name="api_divisions"),

    # Admin Panel
    path("admin/", admin_views.admin_panel_view, name="admin_panel"),
    path("admin/users/", admin_views.user_management_view, name="user_management"),
    path("admin/users/create/", admin_views.user_create_view, name="user_create"),
    path("admin/users/<int:user_id>/update/", admin_views.user_update_view, name="user_update"),
    path("admin/users/<int:user_id>/delete/", admin_views.user_delete_view, name="user_delete"),
    path("admin/permissions/", admin_views.permission_management_view, name="permission_management"),
    path("admin/permissions/<int:user_id>/", admin_views.user_permissions_view, name="user_permissions"),
    path("admin/logs/login/", admin_views.login_logs_view, name="login_logs"),
    path("admin/logs/actions/", admin_views.action_logs_view, name="action_logs"),
    path("admin/logs/login/export/", admin_views.login_logs_export, name="login_logs_export"),
    path("admin/logs/actions/export/", admin_views.action_logs_export, name="action_logs_export"),
    path("admin/storage/", admin_views.database_storage_view, name="database_storage"),
    path("admin/api/storage/", admin_views.storage_data_api, name="storage_data_api"),
]