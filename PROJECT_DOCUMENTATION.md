# Fleet Management System - AI Agent Reference

## 🎯 Project Overview
**Domain**: Fleet & Equipment Management System  
**Tech Stack**: Django 5.2.7, PostgreSQL, Bootstrap 5  
**Language**: Python 3.11  
**UI Language**: 100% Arabic Interface  
**Architecture**: Service Layer + Modular Views + Generic Foreign Keys  

## 🏗️ Core Architecture Patterns

### 1. **Service Layer Pattern**
- **BaseService**: Common CRUD operations (`inventory/services/base.py`)
- **CarService**: Vehicle-specific business logic (`inventory/services/car_service.py`)
- **EquipmentService**: Equipment-specific business logic (`inventory/services/equipment_service.py`)
- **MaintenanceService**: Generic maintenance operations (`inventory/services/maintenance_service.py`)

### 2. **Modular View Structure**
- **auth_views.py**: Authentication & authorization
- **dashboard_views.py**: Dashboard with expiry alerts
- **car_views.py**: Vehicle CRUD operations
- **equipment_views.py**: Equipment CRUD operations
- **generic_table_views.py**: DDL table management
- **media_views.py**: Secure file serving

### 3. **Generic Foreign Key Pattern**
- **Maintenance Model**: Uses `GenericForeignKey` to link to both Cars and Equipment
- **ContentType**: Enables polymorphic relationships

## 📊 Data Model Architecture

### Core Models
```python
# Main Entities
Car                    # Fleet vehicles with Arabic/English plates
Equipment             # Equipment with calibration certificates
Maintenance           # Generic maintenance records (polymorphic)

# DDL Tables (BaseDDLModel inheritance)
AdministrativeUnit    # الإدارة
Department           # الأقسام
Driver               # السائقين
CarClass             # فئات السيارات
Manufacturer         # الشركات المصنعة
CarModel             # موديلات السيارات
EquipmentModel        # موديلات المعدات
FunctionalLocation    # المواقع الوظيفية
Room                 # الغرف
Location             # المواقع
Sector               # القطاعات
NotificationRecipient # مستلمي الإشعارات
ContractType         # أنواع العقود
Activity             # الأنشطة
Region               # المناطق
CalibrationCertificateImage # شهادات المعايرة
```

### Key Relationships
- **Car** → Many ForeignKeys to DDL tables + ManyToMany to Regions
- **Equipment** → ForeignKeys to Manufacturer, Model, Location, Sector
- **Maintenance** → GenericForeignKey to Car OR Equipment
- **CalibrationCertificateImage** → ForeignKey to Equipment

## 🔧 Business Logic Patterns

### Service Layer Methods
```python
# BaseService (Common Operations)
get_all(select_related, prefetch_related)
get_by_id(pk)
search(queryset, field, query)
sort(queryset, field, order)
paginate(queryset, page, per_page)

# CarService (Vehicle Operations)
get_cars_with_related()           # Prefetch all FKs
get_cars_with_maintenance()       # Annotate with latest maintenance
get_expiring_cars(status, days)   # Filter by inspection expiry

# EquipmentService (Equipment Operations)
get_equipment_with_related()      # Prefetch all FKs
get_equipment_with_maintenance() # Annotate with latest maintenance
get_expiring_equipment(status, days) # Filter by inspection expiry

# MaintenanceService (Maintenance Operations)
get_maintenance_for_object(obj)   # Get all maintenance for any object
create_maintenance(obj, **kwargs) # Create maintenance record
```

### Custom Model Managers
```python
# CarManager
with_related()           # Prefetch all related objects
by_status(status)       # Filter by status
expiring_inspections(days) # Get expiring inspections

# EquipmentManager
with_related()           # Prefetch all related objects
by_status(status)       # Filter by status
expiring_inspections(days) # Get expiring inspections
```

## 🎨 UI & Translation System

### Arabic Translation Architecture
- **Centralized**: `inventory/utils/translations.py`
- **Model Translations**: Arabic names for all models
- **Operation Translations**: Arabic labels for CRUD operations
- **Message Templates**: Success/error messages in Arabic

### Template Structure
```
templates/
├── base.html                    # Main layout with Arabic sidebar
├── base_login.html             # Login layout
└── inventory/
    ├── dashboard.html          # Dashboard with alerts
    ├── car_*.html             # Vehicle management
    ├── equipment_*.html       # Equipment management
    ├── generic_*.html          # DDL table management
    └── errors/                # Error pages
```

## 🔐 Security & Authentication

### Access Control
- **Admin Required**: All views require admin group membership
- **Secure Media**: Files served through authentication check
- **CSRF Protection**: Enabled on all forms
- **SQL Injection**: Protected by Django ORM

### Authentication Flow
1. **Login**: Arabic form with admin group check
2. **Session**: HTTP-only cookies
3. **Authorization**: `@user_passes_test(is_admin)` decorator
4. **Logout**: Redirect to login page

## 📁 File Organization Patterns

### Directory Structure
```
inventory/
├── models.py              # All data models
├── constants.py           # Application constants
├── managers.py            # Custom model managers
├── services/              # Business logic layer
│   ├── base.py           # Base service class
│   ├── car_service.py    # Vehicle operations
│   ├── equipment_service.py # Equipment operations
│   └── maintenance_service.py # Maintenance operations
├── views/                 # Modular view structure
│   ├── auth_views.py     # Authentication
│   ├── dashboard_views.py # Dashboard
│   ├── car_views.py      # Vehicle CRUD
│   ├── equipment_views.py # Equipment CRUD
│   ├── generic_table_views.py # DDL management
│   └── media_views.py    # File serving
├── forms/                 # Form organization
│   ├── base.py           # Base widgets
│   ├── car_forms.py      # Vehicle forms
│   ├── equipment_forms.py # Equipment forms
│   └── generic_forms.py  # DDL forms
├── utils/                 # Utility functions
│   ├── translations.py   # Arabic translations
│   ├── decorators.py     # Custom decorators
│   ├── mixins.py         # View mixins
│   └── helpers.py        # Helper functions
└── tests/                # Test coverage
    ├── test_models.py    # Model tests
    ├── test_services.py  # Service tests
    └── test_views.py     # View tests
```

## 🚀 Development Patterns

### Adding New Features
1. **Model**: Add to `models.py` with Arabic verbose names
2. **Service**: Create service class inheriting from `BaseService`
3. **Views**: Add views to appropriate module in `views/`
4. **Forms**: Create forms in appropriate module in `forms/`
5. **Templates**: Add Arabic templates following existing patterns
6. **Translations**: Update `utils/translations.py` with Arabic names

### Database Operations
- **Always use services** for business logic
- **Use select_related/prefetch_related** for performance
- **Follow Django ORM patterns** for queries
- **Use custom managers** for common queries

### UI Development
- **100% Arabic interface** required
- **Bootstrap 5** for responsive design
- **Consistent form patterns** across all modules
- **Error handling** with Arabic messages

## 🔍 Common Query Patterns

### Performance Optimizations
```python
# Good: Use service methods with prefetching
cars = car_service.get_cars_with_related()

# Good: Use custom managers
cars = Car.objects.with_related().by_status('operational')

# Good: Use select_related for single FK
cars = Car.objects.select_related('manufacturer', 'model')

# Good: Use prefetch_related for M2M
cars = Car.objects.prefetch_related('visited_regions')
```

### Search Patterns
```python
# Use service search methods
cars = car_service.search(cars, 'fleet_no', search_query)

# Use Django Q objects for complex queries
cars = Car.objects.filter(
    Q(fleet_no__icontains=query) | 
    Q(plate_no_en__icontains=query)
)
```

## 🎯 Key Business Rules

### Car Management
- **Fleet No**: Unique identifier
- **Plates**: Both English and Arabic required
- **Location**: Description required
- **Inspections**: Track start/end dates
- **Regions**: Many-to-many relationship

### Equipment Management
- **Door No**: Unique identifier
- **Plate No**: Required
- **Manufacturing Year**: 2000-2030 range
- **Status**: Operational/New/Defective
- **Certificates**: Multiple calibration certificates

### Maintenance Tracking
- **Generic**: Works with both Cars and Equipment
- **Dates**: Maintenance and recovery dates
- **Cost**: Optional maintenance cost
- **History**: Full maintenance history per object

## 🔧 Configuration & Settings

### Environment Variables
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*
DB_NAME=fleet_management_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
TIME_ZONE=Asia/Riyadh
```

### Django Settings
- **Language**: Arabic (`ar`)
- **Time Zone**: Asia/Riyadh
- **Media**: Local storage (not S3)
- **Static**: Bootstrap 5 + custom CSS
- **Database**: PostgreSQL with connection pooling

## 📋 Development Checklist

### Before Making Changes
- [ ] Understand the service layer pattern
- [ ] Check existing translations in `utils/translations.py`
- [ ] Review similar implementations in other modules
- [ ] Ensure Arabic interface compliance

### After Making Changes
- [ ] Test with `python manage.py check`
- [ ] Run existing tests: `python manage.py test`
- [ ] Verify Arabic translations work
- [ ] Check performance with Django Debug Toolbar
- [ ] Update this documentation if architecture changes

## 🚨 Critical Constraints

1. **100% Arabic UI**: All user-facing text must be in Arabic
2. **Backward Compatibility**: Never break existing functionality
3. **Service Layer**: Use services for all business logic
4. **Generic Foreign Keys**: Maintenance model uses polymorphic relationships
5. **Admin Only**: All operations require admin group membership
6. **Local Storage**: Media files stored locally (not cloud)

## 🔗 Quick Reference

### Common Imports
```python
from inventory.services import CarService, EquipmentService
from inventory.models import Car, Equipment, Maintenance
from inventory.utils.translations import get_model_arabic_name
from inventory.utils.decorators import admin_required
```

### Common Patterns
```python
# Service initialization
car_service = CarService()
equipment_service = EquipmentService()

# View decorators
@login_required
@user_passes_test(is_admin)
def my_view(request):
    pass

# Arabic translations
model_name = get_model_arabic_name('Car')
```

---

**Last Updated**: Current as of project analysis  
**Version**: 1.0.0  
**Maintainer**: AI Agent Reference Documentation