from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
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
    path("generic-tables/<str:model_name>/<int:pk>/update/", views.generic_table_update_view, name="generic_table_update"),
    path("generic-tables/<str:model_name>/<int:pk>/delete/", views.generic_table_delete_view, name="generic_table_delete"),
    
    # Secure Media Files
    path("secure-media/<path:path>", views.secure_media_view, name="secure_media"),
]