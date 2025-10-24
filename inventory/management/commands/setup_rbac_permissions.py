"""
Management command to set up default RBAC permissions
"""
from django.core.management.base import BaseCommand
from inventory.models import ModulePermission


class Command(BaseCommand):
    help = 'Set up default module permissions for RBAC system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default module permissions...')

        # Define default permissions for each module
        modules = ['cars', 'equipment', 'generic_tables']
        permissions = ['create', 'read', 'update', 'delete']

        created_count = 0

        for module in modules:
            for permission in permissions:
                permission_obj, created = ModulePermission.objects.get_or_create(
                    module_name=module,
                    permission_type=permission,
                    defaults={
                        'description': f'Permission {permission} for {module}'
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'Created permission: {module} - {permission}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up {created_count} default permissions'
            )
        )
