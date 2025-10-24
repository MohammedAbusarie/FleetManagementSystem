"""
Management command to migrate existing users to RBAC system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from inventory.models import UserProfile


class Command(BaseCommand):
    help = 'Migrate existing users to RBAC system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if profiles already exist'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        self.stdout.write('Migrating existing users to RBAC system...')

        # Get all existing users
        all_users = User.objects.all()
        admin_group = Group.objects.filter(name='Admin').first()

        migrated_count = 0
        skipped_count = 0
        error_count = 0

        for user in all_users:
            try:
                # Check if user already has a profile
                if UserProfile.objects.filter(user=user).exists():
                    if not force:
                        self.stdout.write(
                            f'Skipping user "{user.username}" - profile already exists'
                        )
                        skipped_count += 1
                        continue
                    else:
                        # Delete existing profile
                        UserProfile.objects.filter(user=user).delete()
                        self.stdout.write(f'Deleted existing profile for "{user.username}"')

                # Determine user type based on existing system
                if user.is_superuser:
                    user_type = 'super_admin'
                    self.stdout.write(f'Migrating superuser: {user.username} -> super_admin')
                elif admin_group and user.groups.filter(name='Admin').exists():
                    user_type = 'admin'
                    self.stdout.write(f'Migrating admin user: {user.username} -> admin')
                else:
                    user_type = 'normal'
                    self.stdout.write(f'Migrating normal user: {user.username} -> normal')

                if not dry_run:
                    # Create user profile
                    UserProfile.objects.create(
                        user=user,
                        user_type=user_type,
                        is_active=user.is_active,
                        created_at=user.date_joined
                    )

                migrated_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error migrating user "{user.username}": {str(e)}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\nMigration Summary:')
        self.stdout.write(f'Users migrated: {migrated_count}')
        self.stdout.write(f'Users skipped: {skipped_count}')
        self.stdout.write(f'Errors: {error_count}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run. No changes were made.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('User migration completed successfully!')
            )
