"""
Management command to rollback RBAC system
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User, Group
from inventory.models import UserProfile, ModulePermission, UserPermission, LoginLog, ActionLog


class Command(BaseCommand):
    help = 'Rollback RBAC system to legacy admin group system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--keep-logs',
            action='store_true',
            help='Keep system logs (do not delete them)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm rollback operation (required for actual rollback)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        keep_logs = options['keep_logs']
        confirm = options['confirm']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        elif not confirm:
            self.stdout.write(
                self.style.ERROR(
                    'Rollback operation requires --confirm flag for safety'
                )
            )
            return

        self.stdout.write('Rolling back RBAC system to legacy admin group system...')

        try:
            with transaction.atomic():
                # Get or create Admin group
                admin_group, created = Group.objects.get_or_create(name='Admin')
                if created:
                    self.stdout.write('Created Admin group')

                # Migrate users back to Admin group
                migrated_users = 0
                
                # Get all users with profiles
                users_with_profiles = User.objects.filter(profile__isnull=False)
                
                for user in users_with_profiles:
                    try:
                        profile = user.profile
                        
                        # Add to Admin group if user is admin or super_admin
                        if profile.user_type in ['admin', 'super_admin']:
                            if not user.groups.filter(name='Admin').exists():
                                user.groups.add(admin_group)
                                self.stdout.write(f'Added {user.username} to Admin group')
                                migrated_users += 1
                        
                        # Set is_superuser if user is super_admin
                        if profile.user_type == 'super_admin' and not user.is_superuser:
                            user.is_superuser = True
                            user.is_staff = True
                            user.save()
                            self.stdout.write(f'Set {user.username} as superuser')

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error migrating user {user.username}: {str(e)}')
                        )

                # Delete RBAC data
                if not dry_run:
                    # Delete user permissions
                    user_permissions_count = UserPermission.objects.count()
                    UserPermission.objects.all().delete()
                    self.stdout.write(f'Deleted {user_permissions_count} user permissions')

                    # Delete module permissions
                    module_permissions_count = ModulePermission.objects.count()
                    ModulePermission.objects.all().delete()
                    self.stdout.write(f'Deleted {module_permissions_count} module permissions')

                    # Delete user profiles
                    user_profiles_count = UserProfile.objects.count()
                    UserProfile.objects.all().delete()
                    self.stdout.write(f'Deleted {user_profiles_count} user profiles')

                    # Delete system logs if requested
                    if not keep_logs:
                        login_logs_count = LoginLog.objects.count()
                        action_logs_count = ActionLog.objects.count()
                        
                        LoginLog.objects.all().delete()
                        ActionLog.objects.all().delete()
                        
                        self.stdout.write(f'Deleted {login_logs_count} login logs')
                        self.stdout.write(f'Deleted {action_logs_count} action logs')
                    else:
                        self.stdout.write('Kept system logs as requested')

                # Summary
                self.stdout.write('\nRollback Summary:')
                self.stdout.write(f'Users migrated to Admin group: {migrated_users}')
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING('This was a dry run. No changes were made.')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('RBAC system rollback completed successfully!')
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            'The system is now using the legacy Admin group system.'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during rollback: {str(e)}')
            )
            raise
