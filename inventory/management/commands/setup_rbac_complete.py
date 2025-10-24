"""
Management command to setup complete RBAC system
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Setup complete RBAC system with all components'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migration',
            action='store_true',
            help='Skip database migration (assumes already run)'
        )
        parser.add_argument(
            '--skip-permissions',
            action='store_true',
            help='Skip permission setup (assumes already done)'
        )
        parser.add_argument(
            '--skip-user-migration',
            action='store_true',
            help='Skip user migration (assumes already done)'
        )
        parser.add_argument(
            '--create-super-admin',
            action='store_true',
            help='Create initial super admin user'
        )
        parser.add_argument(
            '--super-admin-username',
            type=str,
            default='admin',
            help='Username for super admin (default: admin)'
        )
        parser.add_argument(
            '--super-admin-email',
            type=str,
            default='admin@example.com',
            help='Email for super admin (default: admin@example.com)'
        )
        parser.add_argument(
            '--super-admin-password',
            type=str,
            default='admin123',
            help='Password for super admin (default: admin123)'
        )

    def handle(self, *args, **options):
        skip_migration = options['skip_migration']
        skip_permissions = options['skip_permissions']
        skip_user_migration = options['skip_user_migration']
        create_super_admin = options['create_super_admin']
        super_admin_username = options['super_admin_username']
        super_admin_email = options['super_admin_email']
        super_admin_password = options['super_admin_password']

        self.stdout.write('Setting up complete RBAC system...')
        self.stdout.write('=' * 50)

        try:
            # Step 1: Run database migration
            if not skip_migration:
                self.stdout.write('Step 1: Running database migration...')
                call_command('migrate', 'inventory', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✓ Database migration completed')
                )
            else:
                self.stdout.write('Step 1: Skipping database migration')

            # Step 2: Setup default permissions
            if not skip_permissions:
                self.stdout.write('Step 2: Setting up default permissions...')
                call_command('setup_rbac_permissions', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✓ Default permissions setup completed')
                )
            else:
                self.stdout.write('Step 2: Skipping permission setup')

            # Step 3: Migrate existing users
            if not skip_user_migration:
                self.stdout.write('Step 3: Migrating existing users...')
                call_command('migrate_users_to_rbac', verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✓ User migration completed')
                )
            else:
                self.stdout.write('Step 3: Skipping user migration')

            # Step 4: Create super admin user
            if create_super_admin:
                self.stdout.write('Step 4: Creating super admin user...')
                call_command(
                    'setup_super_admin',
                    username=super_admin_username,
                    email=super_admin_email,
                    password=super_admin_password,
                    verbosity=1
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ Super admin user created')
                )
            else:
                self.stdout.write('Step 4: Skipping super admin creation')

            # Final summary
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(
                self.style.SUCCESS('RBAC system setup completed successfully!')
            )
            
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Access the admin panel at /admin/')
            self.stdout.write('2. Create additional users as needed')
            self.stdout.write('3. Assign permissions to users')
            self.stdout.write('4. Review system logs and monitoring')
            
            if create_super_admin:
                self.stdout.write(f'\nSuper admin credentials:')
                self.stdout.write(f'Username: {super_admin_username}')
                self.stdout.write(f'Email: {super_admin_email}')
                self.stdout.write(f'Password: {super_admin_password}')
                self.stdout.write(
                    self.style.WARNING('Please change the password after first login!')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during RBAC setup: {str(e)}')
            )
            raise
