"""
Management command to reset all users and create new ones
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from inventory.models import UserProfile


class Command(BaseCommand):
    help = 'Delete all users and create 2 superadmins, 2 admins, and 3 normal users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        # Users to create
        users_to_create = [
            # 2 Superadmins
            {
                'username': 'superadmin1',
                'email': 'superadmin1@fleet.com',
                'password': 'SuperAdmin123!',
                'first_name': 'مدير',
                'last_name': 'عام أول',
                'user_type': 'super_admin'
            },
            {
                'username': 'superadmin2',
                'email': 'superadmin2@fleet.com',
                'password': 'SuperAdmin456!',
                'first_name': 'مدير',
                'last_name': 'عام ثاني',
                'user_type': 'super_admin'
            },
            # 2 Admins
            {
                'username': 'admin1',
                'email': 'admin1@fleet.com',
                'password': 'Admin123!',
                'first_name': 'مدير',
                'last_name': 'أول',
                'user_type': 'admin'
            },
            {
                'username': 'admin2',
                'email': 'admin2@fleet.com',
                'password': 'Admin456!',
                'first_name': 'مدير',
                'last_name': 'ثاني',
                'user_type': 'admin'
            },
            # 3 Normal Users
            {
                'username': 'user1',
                'email': 'user1@fleet.com',
                'password': 'User123!',
                'first_name': 'مستخدم',
                'last_name': 'أول',
                'user_type': 'normal'
            },
            {
                'username': 'user2',
                'email': 'user2@fleet.com',
                'password': 'User456!',
                'first_name': 'مستخدم',
                'last_name': 'ثاني',
                'user_type': 'normal'
            },
            {
                'username': 'user3',
                'email': 'user3@fleet.com',
                'password': 'User789!',
                'first_name': 'مستخدم',
                'last_name': 'ثالث',
                'user_type': 'normal'
            },
        ]

        # Confirm deletion unless --force flag
        if not options['force']:
            user_count = User.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f'This will delete ALL {user_count} existing users and create 7 new users.'
                )
            )
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        try:
            with transaction.atomic():
                # Delete all UserProfiles first (CASCADE will handle User deletion too, but let's be explicit)
                UserProfile.objects.all().delete()
                
                # Delete all remaining Users (in case some don't have profiles)
                User.objects.all().delete()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted all existing users.')
                )

                # Create new users
                created_count = 0
                for user_data in users_to_create:
                    # Create Django user
                    user = User.objects.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_superuser=(user_data['user_type'] == 'super_admin'),
                        is_staff=(user_data['user_type'] in ['super_admin', 'admin']),
                        is_active=True
                    )

                    # Create user profile (first superadmin creates others, so use None for created_by)
                    UserProfile.objects.create(
                        user=user,
                        user_type=user_data['user_type'],
                        is_active=True,
                        created_by=None
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created {user_data["user_type"]} user: {user_data["username"]}'
                        )
                    )
                    created_count += 1

                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(
                    self.style.SUCCESS('Users reset completed successfully!')
                )
                self.stdout.write('=' * 70 + '\n')
                
                # Display credentials
                self.stdout.write(
                    self.style.SUCCESS('New User Credentials:')
                )
                self.stdout.write('=' * 70)
                
                for user_data in users_to_create:
                    self.stdout.write(f'\n{user_data["user_type"].upper().replace("_", " ")}:')
                    self.stdout.write(f'  Username: {user_data["username"]}')
                    self.stdout.write(f'  Password: {user_data["password"]}')
                    self.stdout.write(f'  Email: {user_data["email"]}')

                self.stdout.write('\n' + '=' * 70 + '\n')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error resetting users: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            raise

