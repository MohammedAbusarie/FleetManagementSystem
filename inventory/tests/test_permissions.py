"""Permission system tests for inventory app"""
from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from inventory.models import UserProfile, ModulePermission, UserPermission
from inventory.utils.decorators import super_admin_required, permission_required
from inventory.utils.mixins import SuperAdminRequiredMixin, PermissionRequiredMixin
from inventory.utils.helpers import (
    is_super_admin, is_admin_user, has_permission, get_user_permissions,
    get_user_type, get_user_permissions_summary
)


class PermissionHelpersTest(TestCase):
    """Test cases for permission helper functions"""
    
    def setUp(self):
        """Set up test data"""
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
    
    def test_is_super_admin_with_profile(self):
        """Test is_super_admin with user profile"""
        self.assertTrue(is_super_admin(self.super_admin))
        self.assertFalse(is_super_admin(self.admin))
        self.assertFalse(is_super_admin(self.normal_user))
    
    def test_is_super_admin_without_profile(self):
        """Test is_super_admin without user profile (legacy)"""
        self.assertTrue(is_super_admin(self.legacy_admin))
    
    def test_is_admin_user_with_profile(self):
        """Test is_admin_user with user profile"""
        self.assertTrue(is_admin_user(self.super_admin))
        self.assertTrue(is_admin_user(self.admin))
        self.assertFalse(is_admin_user(self.normal_user))
    
    def test_is_admin_user_without_profile(self):
        """Test is_admin_user without user profile (legacy)"""
        self.assertTrue(is_admin_user(self.legacy_admin))
    
    def test_get_user_type_with_profile(self):
        """Test get_user_type with user profile"""
        self.assertEqual(get_user_type(self.super_admin), 'super_admin')
        self.assertEqual(get_user_type(self.admin), 'admin')
        self.assertEqual(get_user_type(self.normal_user), 'normal')
    
    def test_get_user_type_without_profile(self):
        """Test get_user_type without user profile (legacy)"""
        self.assertEqual(get_user_type(self.legacy_admin), 'admin')
    
    def test_has_permission_super_admin(self):
        """Test has_permission for super admin"""
        self.assertTrue(has_permission(self.super_admin, 'cars', 'create'))
        self.assertTrue(has_permission(self.super_admin, 'equipment', 'delete'))
        self.assertTrue(has_permission(self.super_admin, 'generic_tables', 'read'))
    
    def test_has_permission_admin(self):
        """Test has_permission for admin"""
        self.assertTrue(has_permission(self.admin, 'cars', 'create'))
        self.assertTrue(has_permission(self.admin, 'equipment', 'delete'))
        self.assertTrue(has_permission(self.admin, 'generic_tables', 'read'))
    
    def test_has_permission_normal_user_no_permissions(self):
        """Test has_permission for normal user with no permissions"""
        self.assertFalse(has_permission(self.normal_user, 'cars', 'create'))
        self.assertFalse(has_permission(self.normal_user, 'equipment', 'read'))
    
    def test_has_permission_normal_user_with_permissions(self):
        """Test has_permission for normal user with assigned permissions"""
        # Assign permissions
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
        
        self.assertTrue(has_permission(self.normal_user, 'cars', 'create'))
        self.assertTrue(has_permission(self.normal_user, 'cars', 'read'))
        self.assertFalse(has_permission(self.normal_user, 'cars', 'update'))
        self.assertFalse(has_permission(self.normal_user, 'equipment', 'create'))
    
    def test_has_permission_legacy_admin(self):
        """Test has_permission for legacy admin"""
        self.assertTrue(has_permission(self.legacy_admin, 'cars', 'create'))
        self.assertTrue(has_permission(self.legacy_admin, 'equipment', 'delete'))
    
    def test_get_user_permissions_normal_user(self):
        """Test get_user_permissions for normal user"""
        # Assign some permissions
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_read_permission,
            granted=False  # Revoked permission
        )
        
        permissions = get_user_permissions(self.normal_user)
        self.assertEqual(permissions.count(), 2)  # Both granted and revoked
        
        granted_permissions = permissions.filter(granted=True)
        self.assertEqual(granted_permissions.count(), 1)
        self.assertEqual(granted_permissions.first().module_permission.permission_type, 'create')
    
    def test_get_user_permissions_summary(self):
        """Test get_user_permissions_summary"""
        # Assign permissions
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
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.equipment_create_permission,
            granted=True
        )
        
        summary = get_user_permissions_summary(self.normal_user)
        
        self.assertIn('cars', summary)
        self.assertIn('equipment', summary)
        self.assertEqual(len(summary['cars']), 2)
        self.assertEqual(len(summary['equipment']), 1)
        self.assertIn('create', summary['cars'])
        self.assertIn('read', summary['cars'])
        self.assertIn('create', summary['equipment'])
    
    def test_get_user_permissions_summary_super_admin(self):
        """Test get_user_permissions_summary for super admin"""
        summary = get_user_permissions_summary(self.super_admin)
        
        # Super admin should have all permissions
        self.assertIn('cars', summary)
        self.assertIn('equipment', summary)
        self.assertIn('generic_tables', summary)
        self.assertEqual(len(summary['cars']), 4)  # create, read, update, delete
        self.assertEqual(len(summary['equipment']), 4)
        self.assertEqual(len(summary['generic_tables']), 4)


class PermissionDecoratorsTest(TestCase):
    """Test cases for permission decorators"""
    
    def setUp(self):
        """Set up test data"""
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
    
    def test_super_admin_required_decorator_super_admin(self):
        """Test @super_admin_required decorator with super admin"""
        @super_admin_required
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.super_admin)
        result = test_view(request)
        self.assertEqual(result, "Success")
    
    def test_super_admin_required_decorator_admin(self):
        """Test @super_admin_required decorator with admin"""
        @super_admin_required
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.admin)
        
        with self.assertRaises(PermissionDenied):
            test_view(request)
    
    def test_super_admin_required_decorator_normal_user(self):
        """Test @super_admin_required decorator with normal user"""
        @super_admin_required
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.normal_user)
        
        with self.assertRaises(PermissionDenied):
            test_view(request)
    
    def test_permission_required_decorator_super_admin(self):
        """Test @permission_required decorator with super admin"""
        @permission_required('cars', 'create')
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.super_admin)
        result = test_view(request)
        self.assertEqual(result, "Success")
    
    def test_permission_required_decorator_admin(self):
        """Test @permission_required decorator with admin"""
        @permission_required('cars', 'create')
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.admin)
        result = test_view(request)
        self.assertEqual(result, "Success")
    
    def test_permission_required_decorator_normal_user_with_permission(self):
        """Test @permission_required decorator with normal user having permission"""
        # Assign permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        @permission_required('cars', 'create')
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.normal_user)
        result = test_view(request)
        self.assertEqual(result, "Success")
    
    def test_permission_required_decorator_normal_user_without_permission(self):
        """Test @permission_required decorator with normal user without permission"""
        @permission_required('cars', 'create')
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.normal_user)
        
        with self.assertRaises(PermissionDenied):
            test_view(request)
    
    def test_permission_required_decorator_multiple_permissions(self):
        """Test @permission_required decorator with multiple permissions"""
        car_read_permission = ModulePermission.objects.create(
            module_name='cars',
            permission_type='read',
            description='Read cars'
        )
        
        # Assign only create permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        @permission_required('cars', ['create', 'read'])
        def test_view(request):
            return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        request = MockRequest(self.normal_user)
        
        with self.assertRaises(PermissionDenied):
            test_view(request)


class PermissionMixinsTest(TestCase):
    """Test cases for permission mixins"""
    
    def setUp(self):
        """Set up test data"""
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
    
    def test_super_admin_required_mixin_super_admin(self):
        """Test SuperAdminRequiredMixin with super admin"""
        class TestView(SuperAdminRequiredMixin):
            def dispatch(self, request, *args, **kwargs):
                return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        view = TestView()
        request = MockRequest(self.super_admin)
        result = view.dispatch(request)
        self.assertEqual(result, "Success")
    
    def test_super_admin_required_mixin_normal_user(self):
        """Test SuperAdminRequiredMixin with normal user"""
        class TestView(SuperAdminRequiredMixin):
            def dispatch(self, request, *args, **kwargs):
                return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        view = TestView()
        request = MockRequest(self.normal_user)
        
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)
    
    def test_permission_required_mixin_with_permission(self):
        """Test PermissionRequiredMixin with user having permission"""
        # Assign permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        class TestView(PermissionRequiredMixin):
            required_permissions = [('cars', 'create')]
            
            def dispatch(self, request, *args, **kwargs):
                return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        view = TestView()
        request = MockRequest(self.normal_user)
        result = view.dispatch(request)
        self.assertEqual(result, "Success")
    
    def test_permission_required_mixin_without_permission(self):
        """Test PermissionRequiredMixin with user without permission"""
        class TestView(PermissionRequiredMixin):
            required_permissions = [('cars', 'create')]
            
            def dispatch(self, request, *args, **kwargs):
                return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        view = TestView()
        request = MockRequest(self.normal_user)
        
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)
    
    def test_permission_required_mixin_multiple_permissions(self):
        """Test PermissionRequiredMixin with multiple permissions"""
        car_read_permission = ModulePermission.objects.create(
            module_name='cars',
            permission_type='read',
            description='Read cars'
        )
        
        # Assign only create permission
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_create_permission,
            granted=True
        )
        
        class TestView(PermissionRequiredMixin):
            required_permissions = [('cars', 'create'), ('cars', 'read')]
            
            def dispatch(self, request, *args, **kwargs):
                return "Success"
        
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        view = TestView()
        request = MockRequest(self.normal_user)
        
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)


class PermissionIntegrationTest(TestCase):
    """Integration tests for permission system"""
    
    def setUp(self):
        """Set up test data"""
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
        self.car_permissions = []
        for permission_type in ['create', 'read', 'update', 'delete']:
            permission = ModulePermission.objects.create(
                module_name='cars',
                permission_type=permission_type,
                description=f'{permission_type.title()} cars'
            )
            self.car_permissions.append(permission)
        
        self.equipment_permissions = []
        for permission_type in ['create', 'read', 'update', 'delete']:
            permission = ModulePermission.objects.create(
                module_name='equipment',
                permission_type=permission_type,
                description=f'{permission_type.title()} equipment'
            )
            self.equipment_permissions.append(permission)
    
    def test_permission_assignment_and_checking(self):
        """Test complete permission assignment and checking workflow"""
        # Assign permissions to normal user
        for permission in self.car_permissions[:2]:  # Only create and read
            UserPermission.objects.create(
                user=self.normal_user,
                module_permission=permission,
                granted=True
            )
        
        # Check permissions
        self.assertTrue(has_permission(self.normal_user, 'cars', 'create'))
        self.assertTrue(has_permission(self.normal_user, 'cars', 'read'))
        self.assertFalse(has_permission(self.normal_user, 'cars', 'update'))
        self.assertFalse(has_permission(self.normal_user, 'cars', 'delete'))
        self.assertFalse(has_permission(self.normal_user, 'equipment', 'create'))
    
    def test_permission_revocation(self):
        """Test permission revocation workflow"""
        # Assign all car permissions
        for permission in self.car_permissions:
            UserPermission.objects.create(
                user=self.normal_user,
                module_permission=permission,
                granted=True
            )
        
        # Verify all permissions are granted
        for permission_type in ['create', 'read', 'update', 'delete']:
            self.assertTrue(has_permission(self.normal_user, 'cars', permission_type))
        
        # Revoke update and delete permissions
        UserPermission.objects.filter(
            user=self.normal_user,
            module_permission__permission_type__in=['update', 'delete']
        ).update(granted=False)
        
        # Verify only create and read remain
        self.assertTrue(has_permission(self.normal_user, 'cars', 'create'))
        self.assertTrue(has_permission(self.normal_user, 'cars', 'read'))
        self.assertFalse(has_permission(self.normal_user, 'cars', 'update'))
        self.assertFalse(has_permission(self.normal_user, 'cars', 'delete'))
    
    def test_permission_inheritance_super_admin(self):
        """Test that super admin inherits all permissions"""
        # Super admin should have all permissions without explicit assignment
        for module in ['cars', 'equipment', 'generic_tables']:
            for permission_type in ['create', 'read', 'update', 'delete']:
                self.assertTrue(has_permission(self.super_admin, module, permission_type))
    
    def test_permission_inheritance_admin(self):
        """Test that admin inherits all permissions"""
        # Admin should have all permissions without explicit assignment
        for module in ['cars', 'equipment', 'generic_tables']:
            for permission_type in ['create', 'read', 'update', 'delete']:
                self.assertTrue(has_permission(self.admin, module, permission_type))
    
    def test_permission_summary_completeness(self):
        """Test that permission summary includes all modules and permissions"""
        # Assign some permissions
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.car_permissions[0],  # create
            granted=True
        )
        UserPermission.objects.create(
            user=self.normal_user,
            module_permission=self.equipment_permissions[1],  # read
            granted=True
        )
        
        summary = get_user_permissions_summary(self.normal_user)
        
        # Should include all modules
        self.assertIn('cars', summary)
        self.assertIn('equipment', summary)
        self.assertIn('generic_tables', summary)
        
        # Should have correct permissions
        self.assertEqual(len(summary['cars']), 1)
        self.assertEqual(len(summary['equipment']), 1)
        self.assertEqual(len(summary['generic_tables']), 0)
        
        self.assertIn('create', summary['cars'])
        self.assertIn('read', summary['equipment'])
