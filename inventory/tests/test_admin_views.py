"""Admin panel view tests for inventory app"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from inventory.models import (
    UserProfile, ModulePermission, UserPermission, LoginLog, ActionLog,
    Car, Equipment, AdministrativeUnit, Manufacturer, CarModel, EquipmentModel, 
    Location, Sector
)


class AdminPanelAccessTest(TestCase):
    """Test cases for admin panel access control"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.admin,
            user_type='admin',
            is_active=True
        )
        
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        # Create legacy admin user (Admin group)
        self.legacy_admin = User.objects.create_user(
            username='legacyadmin',
            email='legacyadmin@test.com',
            password='testpass123'
        )
        self.admin_group = Group.objects.create(name='Admin')
        self.legacy_admin.groups.add(self.admin_group)
    
    def test_admin_panel_requires_login(self):
        """Test admin panel requires authentication"""
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/?next=/admin/')
    
    def test_admin_panel_super_admin_access(self):
        """Test super admin can access admin panel"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة الإدارة')
    
    def test_admin_panel_admin_access(self):
        """Test admin can access admin panel"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة الإدارة')
    
    def test_admin_panel_legacy_admin_access(self):
        """Test legacy admin can access admin panel"""
        self.client.login(username='legacyadmin', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة الإدارة')
    
    def test_admin_panel_normal_user_denied(self):
        """Test normal user cannot access admin panel"""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 403)
    
    def test_user_management_super_admin_access(self):
        """Test super admin can access user management"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/users/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إدارة المستخدمين')
    
    def test_user_management_admin_access(self):
        """Test admin can access user management"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/users/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إدارة المستخدمين')
    
    def test_user_management_normal_user_denied(self):
        """Test normal user cannot access user management"""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get('/admin/users/')
        self.assertEqual(response.status_code, 403)
    
    def test_system_logs_super_admin_access(self):
        """Test super admin can access system logs"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'سجلات النظام')
    
    def test_system_logs_admin_access(self):
        """Test admin can access system logs"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/admin/logs/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'سجلات النظام')
    
    def test_system_logs_normal_user_denied(self):
        """Test normal user cannot access system logs"""
        self.client.login(username='normal', password='testpass123')
        response = self.client.get('/admin/logs/')
        self.assertEqual(response.status_code, 403)


class UserManagementTest(TestCase):
    """Test cases for user management functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create super admin
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        
        # Create admin
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.admin,
            user_type='admin',
            is_active=True
        )
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
    
    def test_user_list_view(self):
        """Test user list view displays all users"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/users/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'superadmin')
        self.assertContains(response, 'admin')
        self.assertContains(response, 'normal')
    
    def test_user_create_view_get(self):
        """Test user create view GET request"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/users/create/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إضافة مستخدم جديد')
    
    def test_user_create_view_post_valid(self):
        """Test user create view POST with valid data"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/admin/users/create/', {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'normal',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        # Should redirect to user list on success
        self.assertRedirects(response, '/admin/users/')
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.user_type, 'normal')
    
    def test_user_create_view_post_invalid(self):
        """Test user create view POST with invalid data"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post('/admin/users/create/', {
            'username': 'normal',  # Already exists
            'email': 'newuser@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'normal'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_user_update_view_get(self):
        """Test user update view GET request"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(f'/admin/users/{self.normal_user.pk}/update/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تحديث المستخدم')
        self.assertContains(response, 'normal')
    
    def test_user_update_view_post_valid(self):
        """Test user update view POST with valid data"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post(f'/admin/users/{self.normal_user.pk}/update/', {
            'username': 'updateduser',
            'email': 'updated@test.com',
            'user_type': 'admin',
            'first_name': 'Updated',
            'last_name': 'User'
        })
        
        # Should redirect to user detail
        self.assertRedirects(response, f'/admin/users/{self.normal_user.pk}/')
        
        # Verify user was updated
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.username, 'updateduser')
        self.assertEqual(self.normal_user.email, 'updated@test.com')
        self.assertEqual(self.normal_user.profile.user_type, 'admin')
    
    def test_user_delete_view_get(self):
        """Test user delete view GET request"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(f'/admin/users/{self.normal_user.pk}/delete/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تأكيد الحذف')
        self.assertContains(response, 'normal')
    
    def test_user_delete_view_post(self):
        """Test user delete view POST request"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post(f'/admin/users/{self.normal_user.pk}/delete/')
        
        # Should redirect to user list
        self.assertRedirects(response, '/admin/users/')
        
        # Verify user was soft deleted
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)
        self.assertFalse(self.normal_user.profile.is_active)
    
    def test_admin_cannot_create_super_admin(self):
        """Test admin cannot create super admin users"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/admin/users/create/', {
            'username': 'newsuperadmin',
            'email': 'newsuperadmin@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'super_admin',  # Admin cannot create super admin
            'first_name': 'New',
            'last_name': 'SuperAdmin'
        })
        
        # Should show error or redirect with error
        self.assertNotEqual(response.status_code, 302)  # Not a successful redirect
    
    def test_admin_cannot_delete_super_admin(self):
        """Test admin cannot delete super admin users"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(f'/admin/users/{self.super_admin.pk}/delete/')
        
        # Should be denied access
        self.assertEqual(response.status_code, 403)
    
    def test_user_search(self):
        """Test user search functionality"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/users/', {
            'search_query': 'admin',
            'search_field': 'username'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'superadmin')
        self.assertContains(response, 'admin')
        self.assertNotContains(response, 'normal')
    
    def test_user_sort(self):
        """Test user sorting functionality"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/users/', {
            'sort_by': 'username',
            'sort_order': 'asc'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should contain all users in sorted order


class PermissionManagementTest(TestCase):
    """Test cases for permission management functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create super admin
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        # Create module permissions
        self.car_create_permission = ModulePermission.objects.create(
            module_name='cars',
            permission_type='create',
            description='Create cars'
        )
        self.car_read_permission = ModulePermission.objects.create(
            module_name='cars',
            permission_type='read',
            description='Read cars'
        )
        self.equipment_create_permission = ModulePermission.objects.create(
            module_name='equipment',
            permission_type='create',
            description='Create equipment'
        )
    
    def test_permission_assignment_view_get(self):
        """Test permission assignment view GET request"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(f'/admin/users/{self.normal_user.pk}/permissions/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إدارة الصلاحيات')
        self.assertContains(response, 'normal')
    
    def test_permission_assignment_view_post(self):
        """Test permission assignment view POST request"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post(f'/admin/users/{self.normal_user.pk}/permissions/', {
            'cars': ['create', 'read'],
            'equipment': ['create']
        })
        
        # Should redirect to user detail
        self.assertRedirects(response, f'/admin/users/{self.normal_user.pk}/')
        
        # Verify permissions were assigned
        user_permissions = UserPermission.objects.filter(
            user=self.normal_user,
            granted=True
        )
        self.assertEqual(user_permissions.count(), 3)  # 2 for cars + 1 for equipment
    
    def test_permission_revocation(self):
        """Test permission revocation"""
        # First assign permissions
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_read_permission,
            granted=True
        )
        
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.post(f'/admin/users/{self.normal_user.pk}/permissions/', {
            'cars': ['read'],  # Only read permission
            'equipment': []
        })
        
        # Should redirect to user detail
        self.assertRedirects(response, f'/admin/users/{self.normal_user.pk}/')
        
        # Verify only read permission remains
        user_permissions = UserPermission.objects.filter(
            user=self.normal_user,
            granted=True
        )
        self.assertEqual(user_permissions.count(), 1)
        self.assertEqual(user_permissions.first().module_permission.permission_type, 'read')
    
    def test_permission_view_user_permissions(self):
        """Test viewing user permissions"""
        # Assign some permissions
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get(f'/admin/users/{self.normal_user.pk}/permissions/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cars')
        self.assertContains(response, 'create')


class SystemLogsTest(TestCase):
    """Test cases for system logs functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create super admin
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        # Create test logs
        self.login_log = LoginLog.objects.create(
            user=self.normal_user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        
        self.action_log = ActionLog.objects.create(
            user=self.normal_user,
            action_type='create',
            module_name='cars',
            object_id='123',
            description='تم إنشاء سيارة جديدة',
            ip_address='192.168.1.1'
        )
    
    def test_login_logs_view(self):
        """Test login logs view"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/login/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'سجل تسجيل الدخول')
        self.assertContains(response, 'normal')
        self.assertContains(response, '192.168.1.1')
    
    def test_action_logs_view(self):
        """Test action logs view"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/actions/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'سجل العمليات')
        self.assertContains(response, 'normal')
        self.assertContains(response, 'تم إنشاء سيارة جديدة')
    
    def test_login_logs_search(self):
        """Test login logs search functionality"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/login/', {
            'search_query': 'normal',
            'search_field': 'username'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'normal')
    
    def test_action_logs_search(self):
        """Test action logs search functionality"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/actions/', {
            'search_query': 'create',
            'search_field': 'action_type'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'create')
    
    def test_login_logs_filter_by_success(self):
        """Test login logs filtering by success status"""
        # Create failed login log
        LoginLog.objects.create(
            user=self.normal_user,
            ip_address='192.168.1.2',
            user_agent='Chrome/5.0',
            success=False
        )
        
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/login/', {
            'success_filter': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should only show successful logins
        self.assertContains(response, '192.168.1.1')
        self.assertNotContains(response, '192.168.1.2')
    
    def test_action_logs_filter_by_module(self):
        """Test action logs filtering by module"""
        # Create action log for equipment
        ActionLog.objects.create(
            user=self.normal_user,
            action_type='update',
            module_name='equipment',
            object_id='456',
            description='تم تحديث معدة',
            ip_address='192.168.1.1'
        )
        
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/logs/actions/', {
            'module_filter': 'cars'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should only show car-related actions
        self.assertContains(response, 'cars')
        self.assertNotContains(response, 'equipment')


class DatabaseStorageTest(TestCase):
    """Test cases for database storage monitoring"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create super admin
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        
        # Create some test data to have database content
        self.manufacturer = Manufacturer.objects.create(name="Test Manufacturer")
        self.car_model = CarModel.objects.create(
            manufacturer=self.manufacturer,
            name="Test Model"
        )
        self.administrative_unit = AdministrativeUnit.objects.create(name="Test Unit")
        
        self.car = Car.objects.create(
            fleet_no="STORAGE001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.car_model,
            administrative_unit=self.administrative_unit
        )
    
    def test_database_storage_view(self):
        """Test database storage view"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/storage/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'مراقب قاعدة البيانات')
        self.assertContains(response, 'استخدام التخزين')
    
    def test_database_storage_api(self):
        """Test database storage API endpoint"""
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/admin/storage/api/')
        
        self.assertEqual(response.status_code, 200)
        # Should return JSON with storage information
        self.assertIn('total_size', response.json())
        self.assertIn('used_size', response.json())
        self.assertIn('free_size', response.json())
        self.assertIn('usage_percentage', response.json())
    
    def test_database_storage_normal_user_denied(self):
        """Test normal user cannot access database storage"""
        normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=normal_user,
            user_type='normal',
            is_active=True
        )
        
        self.client.login(username='normal', password='testpass123')
        response = self.client.get('/admin/storage/')
        
        self.assertEqual(response.status_code, 403)
