"""RBAC services tests for inventory app"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from inventory.services.rbac_service import (
    UserProfileService, PermissionService, LoggingService,
    AdminService, LoggingServiceNew, PermissionServiceNew
)
from inventory.models import (
    UserProfile, ModulePermission, UserPermission, LoginLog, ActionLog
)


class UserProfileServiceTest(TestCase):
    """Test cases for UserProfileService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = UserProfileService()
        
        # Create test users
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@test.com',
            password='testpass123'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@test.com',
            password='testpass123'
        )
    
    def test_get_user_profile_existing(self):
        """Test get_user_profile with existing profile"""
        # Create profile first
        profile = UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        result_profile = self.service.get_user_profile(self.normal_user)
        self.assertEqual(result_profile, profile)
        self.assertEqual(result_profile.user_type, 'normal')
    
    def test_get_user_profile_create_new(self):
        """Test get_user_profile creates new profile"""
        result_profile = self.service.get_user_profile(self.normal_user)
        
        self.assertIsNotNone(result_profile)
        self.assertEqual(result_profile.user, self.normal_user)
        self.assertEqual(result_profile.user_type, 'normal')
        self.assertTrue(result_profile.is_active)
    
    def test_get_user_type_with_profile(self):
        """Test get_user_type with user profile"""
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        UserProfile.objects.create(
            user=self.admin,
            user_type='admin',
            is_active=True
        )
        UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        self.assertEqual(self.service.get_user_type(self.super_admin), 'super_admin')
        self.assertEqual(self.service.get_user_type(self.admin), 'admin')
        self.assertEqual(self.service.get_user_type(self.normal_user), 'normal')
    
    def test_get_user_type_without_profile(self):
        """Test get_user_type without user profile (legacy fallback)"""
        # Test with superuser
        self.super_admin.is_superuser = True
        self.super_admin.save()
        
        self.assertEqual(self.service.get_user_type(self.super_admin), 'admin')
    
    def test_is_super_admin_with_profile(self):
        """Test is_super_admin with user profile"""
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        UserProfile.objects.create(
            user=self.admin,
            user_type='admin',
            is_active=True
        )
        
        self.assertTrue(self.service.is_super_admin(self.super_admin))
        self.assertFalse(self.service.is_super_admin(self.admin))
    
    def test_is_super_admin_without_profile(self):
        """Test is_super_admin without user profile (legacy fallback)"""
        self.super_admin.is_superuser = True
        self.super_admin.save()
        
        self.assertTrue(self.service.is_super_admin(self.super_admin))
    
    def test_is_admin_user_with_profile(self):
        """Test is_admin_user with user profile"""
        UserProfile.objects.create(
            user=self.super_admin,
            user_type='super_admin',
            is_active=True
        )
        UserProfile.objects.create(
            user=self.admin,
            user_type='admin',
            is_active=True
        )
        UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        self.assertTrue(self.service.is_admin_user(self.super_admin))
        self.assertTrue(self.service.is_admin_user(self.admin))
        self.assertFalse(self.service.is_admin_user(self.normal_user))
    
    def test_create_user_profile(self):
        """Test create_user_profile"""
        profile = self.service.create_user_profile(
            self.normal_user,
            user_type='admin',
            created_by=self.admin
        )
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, self.normal_user)
        self.assertEqual(profile.user_type, 'admin')
        self.assertEqual(profile.created_by, self.admin)
        self.assertTrue(profile.is_active)
    
    def test_update_user_profile(self):
        """Test update_user_profile"""
        # Create initial profile
        profile = UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        updated_profile = self.service.update_user_profile(
            self.normal_user,
            user_type='admin',
            is_active=False
        )
        
        self.assertEqual(updated_profile.user_type, 'admin')
        self.assertFalse(updated_profile.is_active)
    
    def test_deactivate_user_profile(self):
        """Test deactivate_user_profile"""
        # Create active profile
        profile = UserProfile.objects.create(
            user=self.normal_user,
            user_type='normal',
            is_active=True
        )
        
        result = self.service.deactivate_user_profile(self.normal_user)
        
        self.assertTrue(result)
        profile.refresh_from_db()
        self.assertFalse(profile.is_active)
        self.assertFalse(self.normal_user.is_active)


class PermissionServiceTest(TestCase):
    """Test cases for PermissionService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = PermissionService()
        
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
    
    def test_get_module_permissions(self):
        """Test get_module_permissions"""
        permissions = self.service.get_module_permissions('cars')
        
        self.assertEqual(permissions.count(), 2)
        self.assertIn(self.car_create_permission, permissions)
        self.assertIn(self.car_read_permission, permissions)
    
    def test_get_user_permissions(self):
        """Test get_user_permissions"""
        # Create user permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        permissions = self.service.get_user_permissions(self.normal_user)
        
        self.assertEqual(permissions.count(), 1)
        self.assertEqual(permissions.first().module_permission, self.car_create_permission)
        self.assertTrue(permissions.first().granted)
    
    def test_has_permission_super_admin(self):
        """Test has_permission for super admin"""
        self.assertTrue(self.service.has_permission(self.super_admin, 'cars', 'create'))
        self.assertTrue(self.service.has_permission(self.super_admin, 'equipment', 'delete'))
    
    def test_has_permission_admin(self):
        """Test has_permission for admin"""
        self.assertTrue(self.service.has_permission(self.admin, 'cars', 'create'))
        self.assertTrue(self.service.has_permission(self.admin, 'equipment', 'delete'))
    
    def test_has_permission_normal_user_with_permission(self):
        """Test has_permission for normal user with permission"""
        # Assign permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        self.assertTrue(self.service.has_permission(self.normal_user, 'cars', 'create'))
        self.assertFalse(self.service.has_permission(self.normal_user, 'cars', 'read'))
    
    def test_has_permission_normal_user_without_permission(self):
        """Test has_permission for normal user without permission"""
        self.assertFalse(self.service.has_permission(self.normal_user, 'cars', 'create'))
        self.assertFalse(self.service.has_permission(self.normal_user, 'equipment', 'read'))
    
    def test_grant_permission(self):
        """Test grant_permission"""
        permission = self.service.grant_permission(
            self.normal_user,
            'cars',
            'create',
            granted_by=self.admin
        )
        
        self.assertIsNotNone(permission)
        self.assertEqual(permission.user, self.normal_user)
        self.assertEqual(permission.module_permission, self.car_create_permission)
        self.assertTrue(permission.granted)
    
    def test_revoke_permission(self):
        """Test revoke_permission"""
        # First grant permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        permission = self.service.revoke_permission(
            self.normal_user,
            'cars',
            'create',
            revoked_by=self.admin
        )
        
        self.assertIsNotNone(permission)
        self.assertFalse(permission.granted)
    
    def test_get_user_module_permissions(self):
        """Test get_user_module_permissions"""
        # Create permissions for cars module
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
        
        permissions = self.service.get_user_module_permissions(self.normal_user, 'cars')
        
        self.assertEqual(permissions.count(), 2)
    
    def test_assign_module_permissions(self):
        """Test assign_module_permissions"""
        permissions = self.service.assign_module_permissions(
            self.normal_user,
            'cars',
            ['create', 'read'],
            assigned_by=self.admin
        )
        
        self.assertEqual(len(permissions), 2)
        
        # Check that permissions were created
        user_permissions = UserPermission.objects.filter(
            user=self.normal_user,
            granted=True
        )
        self.assertEqual(user_permissions.count(), 2)
    
    def test_revoke_module_permissions(self):
        """Test revoke_module_permissions"""
        # First assign permissions
        self.service.assign_module_permissions(
            self.normal_user,
            'cars',
            ['create', 'read', 'update'],
            assigned_by=self.admin
        )
        
        # Then revoke some
        permissions = self.service.revoke_module_permissions(
            self.normal_user,
            'cars',
            ['create', 'update'],
            revoked_by=self.admin
        )
        
        self.assertEqual(len(permissions), 2)
        
        # Check that only 'read' permission remains
        user_permissions = UserPermission.objects.filter(
            user=self.normal_user,
            granted=True
        )
        self.assertEqual(user_permissions.count(), 1)
        self.assertEqual(user_permissions.first().module_permission.permission_type, 'read')
    
    def test_get_user_permissions_summary(self):
        """Test get_user_permissions_summary"""
        # Assign some permissions
        self.service.assign_module_permissions(
            self.normal_user,
            'cars',
            ['create', 'read'],
            assigned_by=self.admin
        )
        
        summary = self.service.get_user_permissions_summary(self.normal_user)
        
        self.assertIn('cars', summary)
        self.assertEqual(len(summary['cars']), 2)
        self.assertIn('create', summary['cars'])
        self.assertIn('read', summary['cars'])
    
    def test_validate_permission_assignment_valid(self):
        """Test validate_permission_assignment with valid data"""
        is_valid, error = self.service.validate_permission_assignment(
            self.normal_user,
            'cars',
            ['create', 'read'],
            self.admin
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_validate_permission_assignment_invalid_user(self):
        """Test validate_permission_assignment with invalid user"""
        is_valid, error = self.service.validate_permission_assignment(
            self.normal_user,
            'cars',
            ['create', 'read'],
            self.normal_user  # Normal user cannot assign permissions
        )
        
        self.assertFalse(is_valid)
        self.assertIn("ليس لديك صلاحية", error)
    
    def test_validate_permission_assignment_invalid_permission(self):
        """Test validate_permission_assignment with invalid permission"""
        is_valid, error = self.service.validate_permission_assignment(
            self.normal_user,
            'cars',
            ['invalid_permission'],
            self.admin
        )
        
        self.assertFalse(is_valid)
        self.assertIn("نوع صلاحية غير صحيح", error)
    
    def test_get_permission_statistics(self):
        """Test get_permission_statistics"""
        # Create some permissions
        self.service.assign_module_permissions(
            self.normal_user,
            'cars',
            ['create', 'read'],
            assigned_by=self.admin
        )
        
        stats = self.service.get_permission_statistics()
        
        self.assertEqual(stats['total_permissions'], 2)
        self.assertEqual(stats['granted_permissions'], 2)
        self.assertEqual(stats['revoked_permissions'], 0)
        self.assertEqual(stats['users_with_permissions'], 1)
    
    def test_search_user_permissions(self):
        """Test search_user_permissions"""
        # Create permissions
        self.service.assign_module_permissions(
            self.normal_user,
            'cars',
            ['create', 'read'],
            assigned_by=self.admin
        )
        
        # Search by username
        permissions = self.service.search_user_permissions(
            UserPermission.objects.all(), 'username', 'normal'
        )
        self.assertEqual(permissions.count(), 2)
        
        # Search by module
        permissions = self.service.search_user_permissions(
            UserPermission.objects.all(), 'module_name', 'cars'
        )
        self.assertEqual(permissions.count(), 2)
    
    def test_get_all_module_permissions(self):
        """Test get_all_module_permissions"""
        all_permissions = self.service.get_all_module_permissions()
        
        self.assertIn('cars', all_permissions)
        self.assertIn('equipment', all_permissions)
        self.assertIn('create', all_permissions['cars'])
        self.assertIn('create', all_permissions['equipment'])
    
    def test_create_default_permissions(self):
        """Test create_default_permissions"""
        created_permissions = self.service.create_default_permissions()
        
        # Should create permissions for all modules and permission types
        self.assertEqual(len(created_permissions), 12)  # 3 modules * 4 permission types
        
        # Check that permissions were created
        total_permissions = ModulePermission.objects.count()
        self.assertEqual(total_permissions, 12)


class LoggingServiceTest(TestCase):
    """Test cases for LoggingService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = LoggingService()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user,
            user_type='normal',
            is_active=True
        )
    
    def test_log_login_success(self):
        """Test log_login with successful login"""
        # Mock request object
        class MockRequest:
            META = {
                'REMOTE_ADDR': '192.168.1.1',
                'HTTP_USER_AGENT': 'Mozilla/5.0'
            }
        
        request = MockRequest()
        
        login_log = self.service.log_login(self.user, request, success=True)
        
        self.assertIsNotNone(login_log)
        self.assertEqual(login_log.user, self.user)
        self.assertEqual(login_log.ip_address, '192.168.1.1')
        self.assertEqual(login_log.user_agent, 'Mozilla/5.0')
        self.assertTrue(login_log.success)
    
    def test_log_login_failure(self):
        """Test log_login with failed login"""
        # Mock request object
        class MockRequest:
            META = {
                'REMOTE_ADDR': '192.168.1.1',
                'HTTP_USER_AGENT': 'Mozilla/5.0'
            }
        
        request = MockRequest()
        
        login_log = self.service.log_login(self.user, request, success=False)
        
        self.assertIsNotNone(login_log)
        self.assertEqual(login_log.user, self.user)
        self.assertFalse(login_log.success)
    
    def test_log_logout(self):
        """Test log_logout"""
        # Create a login log first
        login_log = LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        
        # Mock request object
        class MockRequest:
            META = {'REMOTE_ADDR': '192.168.1.1'}
        
        request = MockRequest()
        
        updated_log = self.service.log_logout(self.user, request)
        
        self.assertIsNotNone(updated_log)
        self.assertIsNotNone(updated_log.logout_time)
    
    def test_log_action(self):
        """Test log_action"""
        # Mock request object
        class MockRequest:
            META = {'REMOTE_ADDR': '192.168.1.1'}
        
        request = MockRequest()
        
        action_log = self.service.log_action(
            self.user,
            'create',
            'cars',
            '123',
            'تم إنشاء سيارة جديدة',
            request
        )
        
        self.assertIsNotNone(action_log)
        self.assertEqual(action_log.user, self.user)
        self.assertEqual(action_log.action_type, 'create')
        self.assertEqual(action_log.module_name, 'cars')
        self.assertEqual(action_log.object_id, '123')
        self.assertEqual(action_log.description, 'تم إنشاء سيارة جديدة')
        self.assertEqual(action_log.ip_address, '192.168.1.1')
    
    def test_get_user_login_history(self):
        """Test get_user_login_history"""
        # Create some login logs
        LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.2',
            user_agent='Chrome/5.0',
            success=False
        )
        
        history = self.service.get_user_login_history(self.user, limit=10)
        self.assertEqual(history.count(), 2)
    
    def test_get_user_action_history(self):
        """Test get_user_action_history"""
        # Create some action logs
        ActionLog.objects.create(
            user=self.user,
            action_type='create',
            module_name='cars',
            description='تم إنشاء سيارة'
        )
        ActionLog.objects.create(
            user=self.user,
            action_type='update',
            module_name='cars',
            description='تم تحديث سيارة'
        )
        
        history = self.service.get_user_action_history(self.user, limit=10)
        self.assertEqual(history.count(), 2)
    
    def test_get_login_statistics(self):
        """Test get_login_statistics"""
        # Create some login logs
        LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.2',
            user_agent='Chrome/5.0',
            success=False
        )
        
        stats = self.service.get_login_statistics(days=30)
        
        self.assertEqual(stats['total_logins'], 2)
        self.assertEqual(stats['successful_logins'], 1)
        self.assertEqual(stats['failed_logins'], 1)
        self.assertEqual(stats['unique_users'], 1)
        self.assertEqual(stats['success_rate'], 50.0)
    
    def test_get_action_statistics(self):
        """Test get_action_statistics"""
        # Create some action logs
        ActionLog.objects.create(
            user=self.user,
            action_type='create',
            module_name='cars',
            description='تم إنشاء سيارة'
        )
        ActionLog.objects.create(
            user=self.user,
            action_type='create',
            module_name='equipment',
            description='تم إنشاء معدة'
        )
        
        stats = self.service.get_action_statistics(days=30)
        
        self.assertEqual(stats['total_actions'], 2)
        self.assertEqual(len(stats['actions_by_type']), 1)  # Only 'create' type
        self.assertEqual(len(stats['actions_by_module']), 2)  # cars and equipment
        self.assertEqual(len(stats['active_users']), 1)  # One user
    
    def test_search_login_logs(self):
        """Test search_login_logs"""
        # Create login logs
        LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        
        # Search by username
        logs = self.service.search_login_logs(
            LoginLog.objects.all(), 'username', 'testuser'
        )
        self.assertEqual(logs.count(), 1)
        
        # Search by IP
        logs = self.service.search_login_logs(
            LoginLog.objects.all(), 'ip_address', '192.168.1.1'
        )
        self.assertEqual(logs.count(), 1)
    
    def test_search_action_logs(self):
        """Test search_action_logs"""
        # Create action logs
        ActionLog.objects.create(
            user=self.user,
            action_type='create',
            module_name='cars',
            description='تم إنشاء سيارة'
        )
        
        # Search by action type
        logs = self.service.search_action_logs(
            ActionLog.objects.all(), 'action_type', 'create'
        )
        self.assertEqual(logs.count(), 1)
        
        # Search by module
        logs = self.service.search_action_logs(
            ActionLog.objects.all(), 'module_name', 'cars'
        )
        self.assertEqual(logs.count(), 1)
    
    def test_cleanup_old_logs(self):
        """Test cleanup_old_logs"""
        # Create old logs
        old_login_log = LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        old_login_log.login_time = timezone.now() - timedelta(days=100)
        old_login_log.save()
        
        old_action_log = ActionLog.objects.create(
            user=self.user,
            action_type='create',
            module_name='cars',
            description='تم إنشاء سيارة'
        )
        old_action_log.timestamp = timezone.now() - timedelta(days=100)
        old_action_log.save()
        
        # Create recent logs
        LoginLog.objects.create(
            user=self.user,
            ip_address='192.168.1.2',
            user_agent='Mozilla/5.0',
            success=True
        )
        ActionLog.objects.create(
            user=self.user,
            action_type='update',
            module_name='cars',
            description='تم تحديث سيارة'
        )
        
        # Cleanup logs older than 30 days
        deleted_count = self.service.cleanup_old_logs(days=30)
        
        # Should delete 2 old logs
        self.assertEqual(deleted_count, 2)
        
        # Verify old logs are deleted
        self.assertFalse(LoginLog.objects.filter(pk=old_login_log.pk).exists())
        self.assertFalse(ActionLog.objects.filter(pk=old_action_log.pk).exists())
        
        # Verify recent logs still exist
        self.assertEqual(LoginLog.objects.count(), 1)
        self.assertEqual(ActionLog.objects.count(), 1)
