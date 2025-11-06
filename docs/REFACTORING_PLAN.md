# Fleet Management System - Detailed Refactoring Plan

## Current State Analysis

**Working System**: Django 5.2.7 fleet management with Cars, Equipment, Maintenance tracking, Arabic UI  
**Main Issues**: 
- Monolithic `views.py` (825 lines)
- Business logic mixed with presentation
- Code duplication (Arabic translations in 3 places)
- No service layer
- No test coverage

**Critical Constraint**: Must maintain 100% backward compatibility - no breaking changes

---

## PHASE 1: Service Layer (Additive Only - Zero Risk)

**Goal**: Create service layer WITHOUT modifying existing code

### Step 1.1: Create Directory Structure
```bash
mkdir inventory/services
touch inventory/services/__init__.py
touch inventory/services/base.py
touch inventory/services/car_service.py
touch inventory/services/equipment_service.py
touch inventory/services/maintenance_service.py
```

### Step 1.2: Create `inventory/services/base.py`
**Complete file content:**
```python
"""Base service class with common CRUD operations"""
from django.core.paginator import Paginator
from django.db.models import Q


class BaseService:
    """Base service with common database operations"""
    model = None
    
    def get_all(self, select_related=None, prefetch_related=None):
        """Get all objects with optional related prefetching"""
        queryset = self.model.objects.all()
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return queryset
    
    def get_by_id(self, pk):
        """Get single object by primary key"""
        return self.model.objects.get(pk=pk)
    
    def search(self, queryset, search_field, search_query):
        """Apply search filter to queryset"""
        if not search_query:
            return queryset
        filter_kwargs = {f"{search_field}__icontains": search_query}
        return queryset.filter(**filter_kwargs)
    
    def sort(self, queryset, sort_by, sort_order='asc'):
        """Apply sorting to queryset"""
        if sort_by:
            prefix = '-' if sort_order == 'desc' else ''
            return queryset.order_by(f"{prefix}{sort_by}")
        return queryset
    
    def paginate(self, queryset, page_number, per_page=20):
        """Paginate queryset"""
        paginator = Paginator(queryset, per_page)
        return paginator.get_page(page_number)
```

### Step 1.3: Create `inventory/services/car_service.py`
**Complete file content:**
```python
"""Car-related business logic"""
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery, Q
from datetime import date, timedelta
from .base import BaseService
from ..models import Car, Maintenance


class CarService(BaseService):
    """Service for Car operations"""
    model = Car
    
    def get_cars_with_related(self):
        """Get cars with all related objects prefetched"""
        return self.model.objects.select_related(
            'manufacturer', 'model', 'administrative_unit', 
            'department_code', 'car_class', 'driver_name',
            'functional_location', 'room', 'notification_recipient',
            'contract_type', 'activity'
        ).prefetch_related('visited_regions')
    
    def get_cars_with_maintenance(self):
        """Get cars annotated with latest maintenance info"""
        car_ct = ContentType.objects.get_for_model(Car)
        latest_maintenance = Maintenance.objects.filter(
            content_type=car_ct,
            object_id=OuterRef('pk')
        ).order_by('-maintenance_date')
        
        return self.get_cars_with_related().annotate(
            last_maintenance_date=Subquery(
                latest_maintenance.values('maintenance_date')[:1]
            ),
            last_maintenance_cost=Subquery(
                latest_maintenance.values('cost')[:1]
            )
        )
    
    def get_expiring_cars(self, expiry_status='about_to_expire', days=30):
        """Get cars with expiring inspections/licenses"""
        today = date.today()
        
        if expiry_status == 'expired':
            return self.get_cars_with_related().filter(
                Q(annual_inspection_end_date__lt=today) |
                Q(car_license_end_date__lt=today) |
                Q(annual_inspection_end_date__isnull=True) |
                Q(car_license_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
        else:
            expiry_date = today + timedelta(days=days)
            return self.get_cars_with_related().filter(
                Q(annual_inspection_end_date__gte=today) | Q(annual_inspection_end_date__isnull=True),
                Q(car_license_end_date__gte=today) | Q(car_license_end_date__isnull=True),
                Q(annual_inspection_end_date__lte=expiry_date) | Q(annual_inspection_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
```

### Step 1.4: Create `inventory/services/equipment_service.py`
**Complete file content:**
```python
"""Equipment-related business logic"""
from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery, Q
from datetime import date, timedelta
from .base import BaseService
from ..models import Equipment, Maintenance


class EquipmentService(BaseService):
    """Service for Equipment operations"""
    model = Equipment
    
    def get_equipment_with_related(self):
        """Get equipment with all related objects prefetched"""
        return self.model.objects.select_related(
            'manufacturer', 'model', 'location', 'sector'
        ).prefetch_related('calibration_certificates')
    
    def get_equipment_with_maintenance(self):
        """Get equipment annotated with latest maintenance info"""
        equipment_ct = ContentType.objects.get_for_model(Equipment)
        latest_maintenance = Maintenance.objects.filter(
            content_type=equipment_ct,
            object_id=OuterRef('pk')
        ).order_by('-maintenance_date')
        
        return self.get_equipment_with_related().annotate(
            last_maintenance_date=Subquery(
                latest_maintenance.values('maintenance_date')[:1]
            ),
            last_maintenance_cost=Subquery(
                latest_maintenance.values('cost')[:1]
            )
        )
    
    def get_expiring_equipment(self, expiry_status='about_to_expire', days=30):
        """Get equipment with expiring inspections/licenses"""
        today = date.today()
        
        if expiry_status == 'expired':
            return self.get_equipment_with_related().filter(
                Q(annual_inspection_end_date__lt=today) |
                Q(equipment_license_end_date__lt=today) |
                Q(annual_inspection_end_date__isnull=True) |
                Q(equipment_license_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
        else:
            expiry_date = today + timedelta(days=days)
            return self.get_equipment_with_related().filter(
                Q(annual_inspection_end_date__gte=today) | Q(annual_inspection_end_date__isnull=True),
                Q(equipment_license_end_date__gte=today) | Q(equipment_license_end_date__isnull=True),
                Q(annual_inspection_end_date__lte=expiry_date) | Q(annual_inspection_end_date__isnull=True)
            ).order_by('annual_inspection_end_date')
```

### Step 1.5: Create `inventory/services/maintenance_service.py`
**Complete file content:**
```python
"""Maintenance-related business logic"""
from django.contrib.contenttypes.models import ContentType
from .base import BaseService
from ..models import Maintenance


class MaintenanceService(BaseService):
    """Service for Maintenance operations"""
    model = Maintenance
    
    def get_maintenance_for_object(self, obj):
        """Get all maintenance records for a specific object"""
        content_type = ContentType.objects.get_for_model(obj)
        return self.model.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).order_by('-maintenance_date')
    
    def create_maintenance(self, content_object, **kwargs):
        """Create maintenance record for an object"""
        maintenance = self.model(content_object=content_object, **kwargs)
        maintenance.save()
        return maintenance
```

### Step 1.6: Create `inventory/services/__init__.py`
**Complete file content:**
```python
"""Service layer exports"""
from .base import BaseService
from .car_service import CarService
from .equipment_service import EquipmentService
from .maintenance_service import MaintenanceService

__all__ = [
    'BaseService',
    'CarService',
    'EquipmentService',
    'MaintenanceService',
]
```

### Step 1.7: Test Phase 1
```bash
python manage.py shell
```
```python
from inventory.services import CarService, EquipmentService
car_service = CarService()
print(car_service.get_all().count())
equipment_service = EquipmentService()
print(equipment_service.get_all().count())
```

**Expected Result**: No errors, counts should match existing data

**Files Created**: 5 new files  
**Files Modified**: NONE  
**Risk Level**: ZERO (purely additive)

---

## PHASE 2: Integrate Services into Views

**Goal**: Replace direct model queries in views.py with service calls

### Step 2.1: Add Service Imports to `inventory/views.py`
**Add at top of file (line 32, after existing imports):**
```python
from .services import CarService, EquipmentService, MaintenanceService
```

### Step 2.2: Initialize Services in Views
**Add after imports:**
```python
# Initialize services
car_service = CarService()
equipment_service = EquipmentService()
maintenance_service = MaintenanceService()
```

### Step 2.3: Refactor `dashboard_view` (lines 68-128)
**Replace lines 80-119 with:**
```python
# Filter cars based on expiry status
cars_expiring = car_service.get_expiring_cars(expiry_status, expiry_days)
equipment_expiring = equipment_service.get_expiring_equipment(expiry_status, expiry_days)
```

### Step 2.4: Refactor `car_list_view` (lines 133-205)
**Replace lines 146-166 with:**
```python
# Get cars with maintenance info
cars = car_service.get_cars_with_maintenance()

# Apply search
if search_query and search_field:
    cars = car_service.search(cars, search_field, search_query)

# Apply sorting
cars = car_service.sort(cars, sort_by, sort_order)
```

### Step 2.5: Refactor `equipment_list_view` (lines 383-445)
**Replace lines 400-424 with:**
```python
# Get equipment with maintenance info
equipment = equipment_service.get_equipment_with_maintenance()

# Apply search
if search_query and search_field:
    equipment = equipment_service.search(equipment, search_field, search_query)

# Apply sorting
equipment = equipment_service.sort(equipment, sort_by, sort_order)
```

### Step 2.6: Test After Each Change
```bash
python manage.py runserver
```
- Test dashboard loads
- Test car list loads and search works
- Test equipment list loads and search works
- Test pagination works

**Files Modified**: `inventory/views.py` (gradual changes)  
**Risk Level**: LOW (each function tested individually)

---

## PHASE 3: Split Views into Modules

**Goal**: Break views.py into logical modules while maintaining compatibility

### Step 3.1: Create Views Directory
```bash
mkdir inventory/views
touch inventory/views/__init__.py
touch inventory/views/auth_views.py
touch inventory/views/dashboard_views.py
touch inventory/views/car_views.py
touch inventory/views/equipment_views.py
touch inventory/views/generic_table_views.py
touch inventory/views/media_views.py
```

### Step 3.2: Extract Auth Views to `inventory/views/auth_views.py`
**Copy lines 34-63 from views.py:**
```python
"""Authentication views"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages


def is_admin(user):
    """Check if user is in Admin group or is superuser"""
    return user.groups.filter(name='Admin').exists() or user.is_superuser


def login_view(request):
    """Login view"""
    class ArabicAuthenticationForm(AuthenticationForm):
        username = forms.CharField(label='اسم المستخدم')
        password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput)
        
    if request.method == 'POST':
        form = ArabicAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if is_admin(user):
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'ليس لديك صلاحية للدخول إلى هذا النظام.')
    else:
        form = ArabicAuthenticationForm()
    return render(request, 'inventory/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')
```

### Step 3.3: Extract Dashboard Views to `inventory/views/dashboard_views.py`
**Copy lines 66-128 from views.py, add service imports:**
```python
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
```

### Step 3.4: Extract Car Views to `inventory/views/car_views.py`
**Copy all car-related views (lines 133-378), add imports and services**

### Step 3.5: Extract Equipment Views to `inventory/views/equipment_views.py`
**Copy all equipment-related views (lines 383-614), add imports and services**

### Step 3.6: Extract Generic Table Views to `inventory/views/generic_table_views.py`
**Copy generic table views (lines 619-779), add imports**

### Step 3.7: Extract Media Views to `inventory/views/media_views.py`
**Copy secure_media_view (lines 782-823), add imports**

### Step 3.8: Create Backward Compatible `inventory/views/__init__.py`
**Complete file content:**
```python
"""Views package - maintains backward compatibility with views.py"""
# Import all views from submodules
from .auth_views import is_admin, login_view, logout_view
from .dashboard_views import dashboard_view
from .car_views import (
    car_list_view,
    car_detail_json,
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
    'car_detail_json',
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
```

### Step 3.9: Backup and Replace Old Views
```bash
# Backup original
mv inventory/views.py inventory/views.py.backup

# Test imports still work
python manage.py check
python manage.py runserver
```

### Step 3.10: Test All Functionality
- Login/logout
- Dashboard
- Car CRUD operations
- Equipment CRUD operations
- Generic tables
- Media file access

### Step 3.11: If All Tests Pass, Remove Backup
```bash
rm inventory/views.py.backup
```

**Files Created**: 7 new view modules  
**Files Modified**: `inventory/views.py` → converted to package  
**Risk Level**: MEDIUM (test thoroughly before removing backup)

---

## PHASE 4: Model Managers & Constants

**Goal**: Add model managers for query optimization

### Step 4.1: Create `inventory/constants.py`
```python
"""Application-level constants"""

# Car choices
CAR_STATUS_CHOICES = [
    ('operational', 'عاملة'),
    ('new', 'جديدة'),
    ('defective', 'معطلة'),
    ('under_maintenance', 'تحت الصيانة'),
]

CAR_OWNERSHIP_CHOICES = [
    ('owned', 'Owned'),
    ('leased_regular', 'Leased - Regular'),
    ('leased_non_regular', 'Leased - Non Regular'),
    ('leased_emp_24hrs', 'Leased - Emp 24hrs'),
]

# Equipment choices
EQUIPMENT_STATUS_CHOICES = [
    ('operational', 'عاملة'),
    ('new', 'جديدة'),
    ('defective', 'معطلة'),
    ('under_maintenance', 'تحت الصيانة'),
]

# Pagination
DEFAULT_PAGE_SIZE = 20

# Date formats
ARABIC_DATE_FORMAT = '%Y-%m-%d'
```

### Step 4.2: Create `inventory/managers.py`
```python
"""Custom model managers"""
from django.db import models
from django.db.models import Q, OuterRef, Subquery
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta


class CarManager(models.Manager):
    """Custom manager for Car model"""
    
    def with_related(self):
        """Prefetch all related objects"""
        return self.select_related(
            'manufacturer', 'model', 'administrative_unit',
            'department_code', 'car_class', 'driver_name',
            'functional_location', 'room', 'notification_recipient',
            'contract_type', 'activity'
        ).prefetch_related('visited_regions')
    
    def by_status(self, status):
        """Filter by status with optimizations"""
        return self.with_related().filter(status=status)
    
    def expiring_inspections(self, days=30):
        """Get cars with inspections expiring in X days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)
        return self.with_related().filter(
            Q(annual_inspection_end_date__gte=today),
            Q(annual_inspection_end_date__lte=expiry_date)
        )


class EquipmentManager(models.Manager):
    """Custom manager for Equipment model"""
    
    def with_related(self):
        """Prefetch all related objects"""
        return self.select_related(
            'manufacturer', 'model', 'location', 'sector'
        ).prefetch_related('calibration_certificates')
    
    def by_status(self, status):
        """Filter by status with optimizations"""
        return self.with_related().filter(status=status)
    
    def expiring_inspections(self, days=30):
        """Get equipment with inspections expiring in X days"""
        today = date.today()
        expiry_date = today + timedelta(days=days)
        return self.with_related().filter(
            Q(annual_inspection_end_date__gte=today),
            Q(annual_inspection_end_date__lte=expiry_date)
        )
```

### Step 4.3: Update `inventory/models.py`
**Add imports at top:**
```python
from .constants import CAR_STATUS_CHOICES, CAR_OWNERSHIP_CHOICES, EQUIPMENT_STATUS_CHOICES
from .managers import CarManager, EquipmentManager
```

**Update Car model (line 144):**
```python
class Car(models.Model):
    """Car/Fleet model - جدول سيارات المدينة"""
    
    STATUS_CHOICES = CAR_STATUS_CHOICES
    OWNERSHIP_CHOICES = CAR_OWNERSHIP_CHOICES
    
    # ... existing fields ...
    
    # Add custom manager
    objects = CarManager()
    
    # ... rest of model ...
    
    @property
    def is_inspection_expired(self):
        """Check if inspection is expired"""
        if not self.annual_inspection_end_date:
            return True
        return self.annual_inspection_end_date < date.today()
    
    @property
    def days_until_inspection_expiry(self):
        """Days until inspection expires"""
        if not self.annual_inspection_end_date:
            return None
        delta = self.annual_inspection_end_date - date.today()
        return delta.days
```

**Update Equipment model (line 214):**
```python
class Equipment(models.Model):
    """Equipment model - جدول المعدات"""
    
    STATUS_CHOICES = EQUIPMENT_STATUS_CHOICES
    
    # ... existing fields ...
    
    # Add custom manager
    objects = EquipmentManager()
    
    # ... rest of model ...
    
    @property
    def is_inspection_expired(self):
        """Check if inspection is expired"""
        if not self.annual_inspection_end_date:
            return True
        return self.annual_inspection_end_date < date.today()
    
    @property
    def days_until_inspection_expiry(self):
        """Days until inspection expires"""
        if not self.annual_inspection_end_date:
            return None
        delta = self.annual_inspection_end_date - date.today()
        return delta.days
```

### Step 4.4: Test Changes
```bash
python manage.py check
python manage.py shell
```
```python
from inventory.models import Car, Equipment
# Test custom manager
print(Car.objects.with_related().count())
print(Equipment.objects.by_status('operational').count())
# Test properties
car = Car.objects.first()
print(car.is_inspection_expired)
print(car.days_until_inspection_expiry)
```

**Files Created**: `inventory/constants.py`, `inventory/managers.py`  
**Files Modified**: `inventory/models.py`  
**Risk Level**: LOW (additive properties, backward compatible)

---

## PHASE 5: Utilities Consolidation

**Goal**: Eliminate duplicate code, organize utilities

### Step 5.1: Create Utils Directory
```bash
mkdir inventory/utils
touch inventory/utils/__init__.py
touch inventory/utils/translations.py
touch inventory/utils/decorators.py
touch inventory/utils/mixins.py
touch inventory/utils/helpers.py
```

### Step 5.2: Create `inventory/utils/translations.py`
**Move content from translation_utils.py + consolidate duplicates:**
```python
"""Centralized translation utilities - consolidates all Arabic translations"""

# Model translations (consolidates from translation_utils, error_handlers, templatetags)
MODEL_TRANSLATIONS = {
    'Car': 'سيارة',
    'Equipment': 'معدة',
    'Maintenance': 'صيانة',
    'CalibrationCertificateImage': 'شهادة معايرة',
    'AdministrativeUnit': 'إدارة',
    'Department': 'قسم',
    'Driver': 'سائق',
    'CarClass': 'فئة السيارة',
    'Manufacturer': 'شركة مصنعة',
    'CarModel': 'موديل سيارة',
    'EquipmentModel': 'موديل معدة',
    'FunctionalLocation': 'موقع وظيفي',
    'Room': 'غرفة',
    'Location': 'موقع',
    'Sector': 'قطاع',
    'NotificationRecipient': 'مستلم إشعار',
    'ContractType': 'نوع عقد',
    'Activity': 'نشاط',
    'Region': 'منطقة',
}

# Verbose (plural) translations
MODEL_TRANSLATIONS_PLURAL = {
    'AdministrativeUnit': 'الإدارات',
    'Department': 'الأقسام',
    'Driver': 'السائقين',
    'CarClass': 'فئات السيارات',
    'Manufacturer': 'الشركات المصنعة',
    'CarModel': 'موديلات السيارات',
    'EquipmentModel': 'موديلات المعدات',
    'FunctionalLocation': 'المواقع الوظيفية',
    'Room': 'الغرف',
    'Location': 'المواقع',
    'Sector': 'القطاعات',
    'NotificationRecipient': 'مستلمي الإشعارات',
    'ContractType': 'أنواع العقود',
    'Activity': 'الأنشطة',
    'Region': 'المناطق',
    'Car': 'السيارات',
    'Equipment': 'المعدات',
    'Maintenance': 'سجلات الصيانة',
    'CalibrationCertificateImage': 'شهادات المعايرة',
}

# Operation translations
OPERATION_TRANSLATIONS = {
    'create': 'إنشاء',
    'update': 'تحديث',
    'delete': 'حذف',
    'add': 'إضافة',
    'edit': 'تعديل',
    'view': 'عرض',
    'list': 'قائمة',
    'detail': 'تفاصيل',
    'search': 'بحث',
    'save': 'حفظ',
    'cancel': 'إلغاء',
}

# Message templates
MESSAGE_TEMPLATES = {
    'create_success': 'تم {operation} {model} بنجاح!',
    'update_success': 'تم {operation} {model} بنجاح!',
    'delete_success': 'تم {operation} {model} بنجاح!',
    'create_error': 'حدث خطأ أثناء {operation} {model}',
    'update_error': 'حدث خطأ أثناء {operation} {model}',
    'delete_error': 'حدث خطأ أثناء {operation} {model}',
    'not_found': 'لم يتم العثور على {model}',
    'validation_error': 'يرجى تصحيح الأخطاء أدناه',
}


def get_model_arabic_name(model_name, plural=False):
    """Get Arabic name for a model (singular or plural)"""
    if plural:
        return MODEL_TRANSLATIONS_PLURAL.get(model_name, model_name)
    return MODEL_TRANSLATIONS.get(model_name, model_name)


def get_operation_arabic_name(operation):
    """Get Arabic name for an operation"""
    return OPERATION_TRANSLATIONS.get(operation, operation)


def get_message_template(template_key, model_name=None, operation=None):
    """Get a message template with Arabic translations"""
    template = MESSAGE_TEMPLATES.get(template_key, '')
    if model_name:
        model_arabic = get_model_arabic_name(model_name)
        template = template.replace('{model}', model_arabic)
    if operation:
        operation_arabic = get_operation_arabic_name(operation)
        template = template.replace('{operation}', operation_arabic)
    return template


# Maintain backward compatibility
get_verbose_model_translations = lambda: MODEL_TRANSLATIONS_PLURAL
get_contextual_action_label = lambda action, model_name: f"{get_operation_arabic_name(action)} {get_model_arabic_name(model_name)}"
```

### Step 5.3: Create `inventory/utils/decorators.py`
```python
"""Custom decorators"""
from functools import wraps
from django.contrib.auth.decorators import user_passes_test


def admin_required(function):
    """Decorator to require admin privileges"""
    def check_admin(user):
        return user.groups.filter(name='Admin').exists() or user.is_superuser
    
    return user_passes_test(check_admin)(function)
```

### Step 5.4: Update Imports Across Codebase
**Update `inventory/views/auth_views.py`:**
```python
from ..utils.decorators import admin_required

# Change is_admin function to use decorator
```

**Update `inventory/views/*_views.py`:**
```python
from ..utils.translations import get_message_template, get_model_arabic_name
```

**Update `inventory/error_handlers.py`:**
```python
from .utils.translations import get_model_arabic_name
# Remove duplicate get_arabic_model_name function
```

**Update `inventory/templatetags/inventory_extras.py`:**
```python
from ..utils.translations import get_model_arabic_name as arabic_model_name
```

### Step 5.5: Keep Old Files for Backward Compatibility
**Update `inventory/translation_utils.py` to import from new location:**
```python
"""Backward compatibility - imports from utils.translations"""
from .utils.translations import *
```

### Step 5.6: Test All Imports
```bash
python manage.py check
python manage.py runserver
# Test all pages load correctly
```

**Files Created**: 4 new utility modules  
**Files Modified**: Multiple view files, error_handlers, templatetags  
**Risk Level**: MEDIUM (many import changes - test thoroughly)

---

## PHASE 6: Forms Organization

**Goal**: Split forms.py into organized modules

### Step 6.1: Create Forms Directory
```bash
mkdir inventory/forms
touch inventory/forms/__init__.py
touch inventory/forms/base.py
touch inventory/forms/car_forms.py
touch inventory/forms/equipment_forms.py
touch inventory/forms/generic_forms.py
```

### Step 6.2: Extract Widget to `inventory/forms/base.py`
**Move Select2Widget class from forms.py**

### Step 6.3: Extract Car Forms to `inventory/forms/car_forms.py`
**Move CarForm and CarMaintenanceFormSet**

### Step 6.4: Extract Equipment Forms to `inventory/forms/equipment_forms.py`
**Move EquipmentForm, CalibrationCertificateImageForm, EquipmentMaintenanceFormSet**

### Step 6.5: Extract Generic Forms to `inventory/forms/generic_forms.py`
**Move GenericDDLForm, EquipmentModelForm, SearchForm**

### Step 6.6: Create Backward Compatible `inventory/forms/__init__.py`
```python
"""Forms package - maintains backward compatibility"""
from .base import Select2Widget
from .car_forms import CarForm, CarMaintenanceFormSet
from .equipment_forms import (
    EquipmentForm,
    CalibrationCertificateImageForm,
    EquipmentMaintenanceFormSet,
)
from .generic_forms import GenericDDLForm, EquipmentModelForm, SearchForm
from .generic_forms import MaintenanceForm  # If not already moved

__all__ = [
    'Select2Widget',
    'CarForm',
    'CarMaintenanceFormSet',
    'EquipmentForm',
    'CalibrationCertificateImageForm',
    'EquipmentMaintenanceFormSet',
    'GenericDDLForm',
    'EquipmentModelForm',
    'SearchForm',
    'MaintenanceForm',
]
```

### Step 6.7: Backup and Replace
```bash
mv inventory/forms.py inventory/forms.py.backup
python manage.py check
# Test form imports work
```

**Files Created**: 5 form modules  
**Files Modified**: `inventory/forms.py` → converted to package  
**Risk Level**: LOW (well-defined imports)

---

## PHASE 7: Testing Infrastructure

**Goal**: Add basic test coverage

### Step 7.1: Create Tests Directory
```bash
mkdir inventory/tests
touch inventory/tests/__init__.py
touch inventory/tests/test_models.py
touch inventory/tests/test_services.py
touch inventory/tests/test_views.py
```

### Step 7.2: Create `inventory/tests/test_models.py`
```python
"""Model tests"""
from django.test import TestCase
from inventory.models import Car, Equipment
from inventory.constants import CAR_STATUS_CHOICES


class CarModelTest(TestCase):
    def test_car_creation(self):
        """Test car can be created"""
        car = Car.objects.create(
            fleet_no="TEST001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
        self.assertEqual(car.fleet_no, "TEST001")
        self.assertTrue(car.pk is not None)
```

### Step 7.3: Create `inventory/tests/test_services.py`
```python
"""Service tests"""
from django.test import TestCase
from inventory.services import CarService, EquipmentService
from inventory.models import Car


class CarServiceTest(TestCase):
    def setUp(self):
        self.service = CarService()
        Car.objects.create(
            fleet_no="TEST001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
    
    def test_get_all_cars(self):
        """Test service can retrieve all cars"""
        cars = self.service.get_all()
        self.assertEqual(cars.count(), 1)
```

### Step 7.4: Run Tests
```bash
python manage.py test inventory.tests
```

**Files Created**: 3 test files  
**Files Modified**: None  
**Risk Level**: ZERO (tests don't affect production)

---

## Final Verification Checklist

After completing all phases:

### Functional Testing
- [ ] Login/logout works
- [ ] Dashboard displays correctly
- [ ] Can create new car
- [ ] Can edit existing car
- [ ] Can delete car
- [ ] Can create new equipment
- [ ] Can edit existing equipment
- [ ] Can delete equipment
- [ ] Generic tables CRUD works
- [ ] Search functionality works
- [ ] Pagination works
- [ ] Images display correctly
- [ ] Media files are secure

### Code Quality
- [ ] No import errors
- [ ] `python manage.py check` passes
- [ ] All tests pass
- [ ] No duplicate code remaining
- [ ] Consistent import style

### Performance
- [ ] Dashboard loads in < 2 seconds
- [ ] List views load in < 2 seconds
- [ ] No N+1 queries (check with Django Debug Toolbar)

---

## Rollback Plan

If anything breaks during any phase:

1. **Phase 1**: Simply delete `inventory/services/` directory
2. **Phase 2**: Restore `inventory/views.py.backup`
3. **Phase 3**: Restore `inventory/views.py.backup`, delete `inventory/views/`
4. **Phase 4**: Revert `inventory/models.py` from git
5. **Phase 5**: Revert all import changes from git
6. **Phase 6**: Restore `inventory/forms.py.backup`
7. **Phase 7**: Delete `inventory/tests/` (doesn't affect production)

**Git Strategy**: Create a branch for each phase:
```bash
git checkout -b phase1-services
# Complete phase 1
git commit -am "Phase 1: Service layer"
git checkout -b phase2-integrate-services
# Continue...
```

---

## Expected Timeline

- **Phase 1**: 2 hours (purely additive)
- **Phase 2**: 3 hours (careful integration)
- **Phase 3**: 4 hours (view splitting + thorough testing)
- **Phase 4**: 2 hours (managers + properties)
- **Phase 5**: 3 hours (utilities consolidation)
- **Phase 6**: 2 hours (forms splitting)
- **Phase 7**: 2 hours (basic tests)

**Total**: ~18 hours of focused work

---

## Success Metrics

1. ✅ All 825 lines from views.py distributed across 7 focused modules
2. ✅ Business logic separated into service layer
3. ✅ No duplicate translation mappings
4. ✅ 100% backward compatibility maintained
5. ✅ Test coverage > 30%
6. ✅ Code is more navigable and maintainable

