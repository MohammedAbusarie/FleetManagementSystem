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

# RBAC Models
UserProfile           # Extended user information with user types
ModulePermission      # Available permissions for each module
UserPermission        # User-specific permission assignments
LoginLog             # User login/logout tracking
ActionLog            # System action logging

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
- **UserProfile** → OneToOne to User (optional, with fallback)
- **UserPermission** → ForeignKey to User + ModulePermission
- **LoginLog** → ForeignKey to User
- **ActionLog** → ForeignKey to User

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

# RBAC Services
UserProfileService:
get_user_profile(user)            # Get or create user profile
get_user_type(user)              # Get user type with fallback
is_super_admin(user)             # Check super admin status
is_admin_user(user)              # Check admin status

PermissionService:
get_module_permissions(module)    # Get permissions for module
get_user_permissions(user)       # Get user's permissions
has_permission(user, module, action) # Check specific permission
grant_permission(user, module, action) # Grant permission
revoke_permission(user, module, action) # Revoke permission

LoggingService:
log_login(user, request, success) # Log login attempt
log_logout(user, request)         # Log logout
log_action(user, action, module, obj_id, desc) # Log system action
get_user_login_history(user)     # Get login history
get_user_action_history(user)    # Get action history

AdminService:
create_user(username, email, user_type) # Create new user
update_user(user, **kwargs)      # Update user and profile
soft_delete_user(user)          # Soft delete user
assign_permissions(user, permissions) # Assign permissions
get_user_statistics()           # Get user statistics
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

# RBAC Managers
UserProfileManager:
active_users()          # Get active users only
by_user_type(type)     # Filter by user type
with_permissions()     # Prefetch user permissions

ModulePermissionManager:
by_module(module)       # Get permissions for specific module
by_permission_type(type) # Get permissions by type

UserPermissionManager:
granted_permissions()   # Get only granted permissions
revoked_permissions()   # Get only revoked permissions
by_user(user)          # Get permissions for specific user

LoginLogManager:
successful_logins()     # Get successful login attempts
failed_logins()        # Get failed login attempts
by_user(user)          # Get login history for user
recent_logins(days)    # Get recent login attempts

ActionLogManager:
by_user(user)          # Get action history for user
by_module(module)      # Get actions for specific module
by_action_type(type)   # Get actions by type
recent_actions(days)   # Get recent actions
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
    ├── admin/                 # Admin panel templates
    │   ├── admin_panel.html   # Main admin dashboard
    │   ├── user_management.html # User management interface
    │   ├── system_logs.html   # System logs display
    │   ├── permission_management.html # Permission assignment
    │   └── database_storage.html # Database storage monitor
    └── errors/                # Error pages
```

## 🔐 Security & Authentication

### Role-Based Access Control (RBAC)
- **Super Admin**: Full system access, can manage all users and permissions
- **Admin**: Can access admin panel, manage normal users, view system logs
- **Normal User**: Limited access based on assigned permissions
- **Legacy Support**: Existing Admin group users continue to work unchanged

### User Types & Permissions
```python
# User Types Hierarchy
Super Admin (is_superuser=True)
├── Can create, disable, and delete both Admins and Normal Users
├── Can assign or edit CRUD permissions for each user
├── Fully controls which user can Create/Read/Update/Delete any module
└── Access to all admin panel features

Admin User (user_type='admin')
├── Can access the admin panel
├── Can view system logs and database gauge
├── Can create and manage only Normal Users
├── Cannot create or manage Admins
└── Operates only within permissions granted by Super Admin

Normal User (user_type='normal')
├── Cannot access admin panel
└── Operates only within assigned permissions
```

### Permission System
```python
# Module Permissions Structure
MODULE_PERMISSIONS = {
    'cars': ['create', 'read', 'update', 'delete'],
    'equipment': ['create', 'read', 'update', 'delete'],
    'generic_tables': ['create', 'read', 'update', 'delete']
}
```

### Access Control
- **Admin Panel**: Only Super Admin and Admin users can access
- **User Management**: Super Admin can manage all users, Admin can manage Normal Users only
- **Permission Assignment**: Super Admin and Admin can assign permissions
- **System Logs**: Super Admin and Admin can view system activity
- **Secure Media**: Files served through authentication check
- **CSRF Protection**: Enabled on all forms
- **SQL Injection**: Protected by Django ORM

### Authentication Flow
1. **Login**: Arabic form with user type and permission check
2. **Session**: HTTP-only cookies with user profile
3. **Authorization**: `@super_admin_required` or `@permission_required` decorators
4. **Logout**: Redirect to login page with activity logging

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
│   ├── maintenance_service.py # Maintenance operations
│   ├── rbac_service.py   # RBAC operations
│   ├── admin_service.py  # Admin panel operations
│   ├── logging_service.py # System logging operations
│   └── permission_service.py # Permission management operations
├── views/                 # Modular view structure
│   ├── auth_views.py     # Authentication
│   ├── dashboard_views.py # Dashboard
│   ├── car_views.py      # Vehicle CRUD
│   ├── equipment_views.py # Equipment CRUD
│   ├── generic_table_views.py # DDL management
│   ├── admin_views.py    # Admin panel views
│   └── media_views.py    # File serving
├── forms/                 # Form organization
│   ├── base.py           # Base widgets
│   ├── car_forms.py      # Vehicle forms
│   ├── equipment_forms.py # Equipment forms
│   ├── generic_forms.py  # DDL forms
│   └── rbac_forms.py     # RBAC forms
├── utils/                 # Utility functions
│   ├── translations.py   # Arabic translations
│   ├── decorators.py     # Custom decorators
│   ├── mixins.py         # View mixins
│   └── helpers.py        # Helper functions
└── tests/                # Test coverage
    ├── test_models.py    # Model tests
    ├── test_services.py  # Service tests
    ├── test_views.py     # View tests
    ├── test_admin_views.py # Admin panel tests
    ├── test_permissions.py # Permission system tests
    └── test_rbac_services.py # RBAC service tests
```

## 🎛️ Admin Panel Features

### User Management
- **User Creation**: Create new users with specific user types
- **User Updates**: Modify user information and permissions
- **User Deactivation**: Soft delete users while preserving audit trail
- **Permission Assignment**: Grant/revoke module-specific permissions
- **User Search**: Search users by username, email, or user type
- **User Statistics**: View user counts by type and activity

### System Monitoring
- **Login Logs**: Track user login/logout activities
- **Action Logs**: Monitor system operations and changes
- **Database Storage**: Monitor database size and usage
- **Performance Metrics**: Track system performance indicators
- **Audit Trail**: Complete history of system changes

### Permission Management
- **Module Permissions**: Define available permissions for each module
- **User Permissions**: Assign specific permissions to users
- **Permission Inheritance**: Super Admin and Admin inherit all permissions
- **Permission Validation**: Ensure proper permission assignment
- **Permission Statistics**: View permission distribution and usage

### Admin Panel Access Control
- **Super Admin**: Full access to all admin panel features
- **Admin**: Limited access to user management and system logs
- **Normal User**: No access to admin panel
- **Legacy Support**: Existing Admin group users maintain access

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
from inventory.services import CarService, EquipmentService, AdminService, PermissionService, LoggingService
from inventory.models import Car, Equipment, Maintenance, UserProfile, ModulePermission, UserPermission
from inventory.utils.translations import get_model_arabic_name
from inventory.utils.decorators import admin_required, super_admin_required, permission_required
from inventory.utils.helpers import is_super_admin, is_admin_user, has_permission
```

### Common Patterns
```python
# Service initialization
car_service = CarService()
equipment_service = EquipmentService()
admin_service = AdminService()
permission_service = PermissionService()
logging_service = LoggingService()

# View decorators
@login_required
@user_passes_test(is_admin)
def my_view(request):
    pass

@super_admin_required
def admin_only_view(request):
    pass

@permission_required('cars', 'create')
def create_car_view(request):
    pass

# Permission checking
if has_permission(request.user, 'cars', 'create'):
    # User can create cars
    pass

# Arabic translations
model_name = get_model_arabic_name('Car')
```

---

**Last Updated**: Current as of project analysis  
**Version**: 1.0.0  
**Maintainer**: AI Agent Reference Documentation