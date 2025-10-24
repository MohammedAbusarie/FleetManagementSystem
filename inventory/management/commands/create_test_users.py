"""
Management command to create test users for RBAC system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from inventory.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users for RBAC system testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users for RBAC system...')
        
        # Test users data
        test_users = [
            # Super Admins
            {
                'username': 'superadmin1',
                'email': 'superadmin1@test.com',
                'password': 'super123',
                'first_name': 'Super',
                'last_name': 'Admin One',
                'user_type': 'super_admin'
            },
            {
                'username': 'superadmin2',
                'email': 'superadmin2@test.com',
                'password': 'super456',
                'first_name': 'Super',
                'last_name': 'Admin Two',
                'user_type': 'super_admin'
            },
            # Admins
            {
                'username': 'admin1',
                'email': 'admin1@test.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'One',
                'user_type': 'admin'
            },
            {
                'username': 'admin2',
                'email': 'admin2@test.com',
                'password': 'admin456',
                'first_name': 'Admin',
                'last_name': 'Two',
                'user_type': 'admin'
            },
            {
                'username': 'admin3',
                'email': 'admin3@test.com',
                'password': 'admin789',
                'first_name': 'Admin',
                'last_name': 'Three',
                'user_type': 'admin'
            },
            # Normal Users
            {
                'username': 'user1',
                'email': 'user1@test.com',
                'password': 'user123',
                'first_name': 'Normal',
                'last_name': 'User One',
                'user_type': 'normal'
            },
            {
                'username': 'user2',
                'email': 'user2@test.com',
                'password': 'user456',
                'first_name': 'Normal',
                'last_name': 'User Two',
                'user_type': 'normal'
            },
            {
                'username': 'user3',
                'email': 'user3@test.com',
                'password': 'user789',
                'first_name': 'Normal',
                'last_name': 'User Three',
                'user_type': 'normal'
            },
            {
                'username': 'user4',
                'email': 'user4@test.com',
                'password': 'user000',
                'first_name': 'Normal',
                'last_name': 'User Four',
                'user_type': 'normal'
            }
        ]

        created_count = 0
        skipped_count = 0

        try:
            with transaction.atomic():
                for user_data in test_users:
                    username = user_data['username']
                    
                    # Check if user already exists
                    if User.objects.filter(username=username).exists():
                        self.stdout.write(
                            self.style.WARNING(f'User "{username}" already exists, skipping...')
                        )
                        skipped_count += 1
                        continue

                    # Create Django user
                    user = User.objects.create_user(
                        username=username,
                        email=user_data['email'],
                        password=user_data['password'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_superuser=(user_data['user_type'] == 'super_admin'),
                        is_staff=(user_data['user_type'] in ['super_admin', 'admin']),
                        is_active=True
                    )

                    # Create user profile
                    UserProfile.objects.create(
                        user=user,
                        user_type=user_data['user_type'],
                        is_active=True
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created {user_data["user_type"]} user: {username}'
                        )
                    )
                    created_count += 1

            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(
                self.style.SUCCESS(f'Test users creation completed!')
            )
            self.stdout.write(f'Users created: {created_count}')
            self.stdout.write(f'Users skipped: {skipped_count}')
            
            # Display credentials
            self.stdout.write('\nTest User Credentials:')
            self.stdout.write('=' * 50)
            
            for user_data in test_users:
                if not User.objects.filter(username=user_data['username']).exists():
                    continue
                    
                self.stdout.write(f'{user_data["user_type"].upper()}:')
                self.stdout.write(f'  Username: {user_data["username"]}')
                self.stdout.write(f'  Password: {user_data["password"]}')
                self.stdout.write(f'  Email: {user_data["email"]}')
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating test users: {str(e)}')
            )
            raise
