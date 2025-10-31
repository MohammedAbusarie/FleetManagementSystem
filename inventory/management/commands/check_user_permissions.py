"""Management command to check user permissions"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile, UserPermission, ModulePermission


class Command(BaseCommand):
    help = 'Check permissions for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the user to check'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email "{email}" not found.'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n=== User Information ==='))
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Full Name: {user.get_full_name() or "N/A"}')
        self.stdout.write(f'Is Superuser: {user.is_superuser}')
        self.stdout.write(f'Is Staff: {user.is_staff}')
        self.stdout.write(f'Is Active: {user.is_active}')
        
        # Check user profile
        try:
            profile = user.profile
            self.stdout.write(self.style.SUCCESS(f'\n=== User Profile ==='))
            self.stdout.write(f'User Type: {profile.user_type}')
            self.stdout.write(f'Profile Active: {profile.is_active}')
            self.stdout.write(f'Created By: {profile.created_by.username if profile.created_by else "N/A"}')
            
            user_type = profile.user_type
            
            if user_type == 'super_admin':
                self.stdout.write(self.style.WARNING('\n=== PERMISSIONS: SUPER ADMIN ==='))
                self.stdout.write('This user has ALL permissions automatically:')
                self.stdout.write('  - All modules: create, read, update, delete')
                self.stdout.write('  - Can manage all users')
                self.stdout.write('  - Full admin panel access')
                return
            
            if user_type == 'admin':
                self.stdout.write(self.style.WARNING('\n=== PERMISSIONS: ADMIN ==='))
                self.stdout.write('This user has ALL permissions automatically:')
                self.stdout.write('  - All modules: create, read, update, delete')
                self.stdout.write('  - Can manage normal users')
                self.stdout.write('  - Admin panel access')
                return
            
        except UserProfile.DoesNotExist:
            self.stdout.write(self.style.WARNING('\n=== User Profile ==='))
            self.stdout.write('No user profile found. Using fallback permissions.')
            if user.is_superuser:
                self.stdout.write('User is Django superuser - has all permissions')
                return
            user_type = 'normal'
        
        # For normal users, check specific permissions
        self.stdout.write(self.style.SUCCESS(f'\n=== User Permissions (Normal User) ==='))
        
        # Get all module permissions
        modules = ['cars', 'equipment', 'generic_tables']
        permissions = ['create', 'read', 'update', 'delete']
        
        # Get user's granted permissions
        user_permissions = UserPermission.objects.filter(
            user=user,
            granted=True
        ).select_related('module_permission')
        
        # Create a map of granted permissions
        granted_map = {}
        for up in user_permissions:
            module = up.module_permission.module_name
            perm_type = up.module_permission.permission_type
            if module not in granted_map:
                granted_map[module] = []
            granted_map[module].append(perm_type)
        
        # Display permissions by module
        has_any_permissions = False
        for module in modules:
            module_display = {
                'cars': 'السيارات (Cars)',
                'equipment': 'المعدات (Equipment)',
                'generic_tables': 'الجداول العامة (Generic Tables)'
            }.get(module, module)
            
            module_perms = granted_map.get(module, [])
            if module_perms:
                has_any_permissions = True
                self.stdout.write(f'\n{module_display}:')
                for perm in permissions:
                    if perm in module_perms:
                        perm_display = {
                            'create': 'إنشاء (Create)',
                            'read': 'قراءة (Read)',
                            'update': 'تحديث (Update)',
                            'delete': 'حذف (Delete)'
                        }.get(perm, perm)
                        self.stdout.write(self.style.SUCCESS(f'  ✓ {perm_display}'))
                    else:
                        perm_display = {
                            'create': 'إنشاء (Create)',
                            'read': 'قراءة (Read)',
                            'update': 'تحديث (Update)',
                            'delete': 'حذف (Delete)'
                        }.get(perm, perm)
                        self.stdout.write(self.style.ERROR(f'  ✗ {perm_display}'))
            else:
                self.stdout.write(f'\n{module_display}:')
                self.stdout.write(self.style.ERROR('  No permissions granted'))
        
        if not has_any_permissions:
            self.stdout.write(self.style.WARNING('\n⚠️  This user has NO permissions granted.'))
            self.stdout.write('They will not be able to access any modules.')
        
        # Show all permission records (including denied ones)
        all_user_permissions = UserPermission.objects.filter(
            user=user
        ).select_related('module_permission')
        
        if all_user_permissions.exists():
            self.stdout.write(self.style.SUCCESS(f'\n=== All Permission Records ==='))
            for up in all_user_permissions:
                status = '✓ Granted' if up.granted else '✗ Denied'
                self.stdout.write(
                    f'{up.module_permission.module_name} - '
                    f'{up.module_permission.permission_type}: {status}'
                )
        
        self.stdout.write('\n')

