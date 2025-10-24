"""
Management command to create initial super admin user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from inventory.models import UserProfile


class Command(BaseCommand):
    help = 'Create initial super admin user for RBAC system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the super admin (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email for the super admin (default: admin@example.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the super admin (default: admin123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Super',
            help='First name for the super admin (default: Super)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Admin',
            help='Last name for the super admin (default: Admin)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if user already exists'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        force = options['force']

        self.stdout.write('Creating initial super admin user...')

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            if not force:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{username}" already exists. Use --force to overwrite.'
                    )
                )
                return
            else:
                # Delete existing user
                User.objects.filter(username=username).delete()
                self.stdout.write(f'Deleted existing user "{username}"')

        try:
            with transaction.atomic():
                # Create super user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_superuser=True,
                    is_staff=True,
                    is_active=True
                )

                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    user_type='super_admin',
                    is_active=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created super admin user: {username}'
                    )
                )
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Password: {password}')
                self.stdout.write(
                    self.style.WARNING(
                        'Please change the password after first login!'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating super admin user: {str(e)}')
            )
            raise
