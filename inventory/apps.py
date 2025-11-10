import logging

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    logger = logging.getLogger(__name__)
    
    def ready(self):
        """Auto-create default 'غير محدد' records if they don't exist and register signals"""
        # Import signals to register them
        import inventory.signals  # noqa: F401
        
        # Import here to avoid circular imports
        from django.db import connection
        from django.core.management import call_command
        
        # Only create if database tables exist (migrations have been run)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_sector'")
                if cursor.fetchone():
                    # Tables exist, create default records
                    self._ensure_default_records()
                    self._ensure_superuser()
        except Exception:
            # For PostgreSQL/MySQL, try a different approach
            try:
                from .models import Sector, Department, Division
                # Check if Sector model table exists by trying to query
                Sector.objects.exists()
                self._ensure_default_records()
                self._ensure_superuser()
            except Exception:
                # Database not ready yet, skip
                pass
    
    def _ensure_default_records(self):
        """Ensure default 'غير محدد' records exist"""
        from .models import Sector, AdministrativeUnit, Department, Division
        
        # Create dummy Sector if it doesn't exist
        dummy_sector, _ = Sector.objects.get_or_create(
            name='غير محدد',
            defaults={'is_dummy': True}
        )
        
        # Create dummy Administrative Unit linked to dummy Sector if it doesn't exist
        dummy_admin_unit, _ = AdministrativeUnit.objects.get_or_create(
            name='غير محدد',
            defaults={'sector': dummy_sector, 'is_dummy': True}
        )
        
        if dummy_admin_unit.sector != dummy_sector or not dummy_admin_unit.is_dummy:
            AdministrativeUnit.objects.filter(pk=dummy_admin_unit.pk).update(
                sector=dummy_sector,
                is_dummy=True
            )
            dummy_admin_unit.refresh_from_db()
        
        # Create dummy Division linked to dummy Administrative Unit if it doesn't exist
        dummy_division, _ = Division.objects.get_or_create(
            name='غير محدد',
            defaults={'administrative_unit': dummy_admin_unit, 'is_dummy': True}
        )

        # Create dummy Department linked to dummy Division if it doesn't exist
        dummy_department, _ = Department.objects.get_or_create(
            name='غير محدد',
            defaults={'division': dummy_division, 'is_dummy': True}
        )
        
        # Ensure department is linked to dummy division (in case it wasn't)
        if dummy_department.division != dummy_division:
            Department.objects.filter(pk=dummy_department.pk).update(
                division=dummy_division,
                is_dummy=True
            )

    def _ensure_superuser(self):
        """Ensure the designated superuser exists."""
        from django.contrib.auth import get_user_model
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError

        User = get_user_model()

        try:
            if 'auth_user' not in connection.introspection.table_names():
                return
        except (OperationalError, ProgrammingError):
            return

        username = 'superadmin2'
        email = 'superadmin1@fleet.com'
        password = 'SuperAdmin456!'

        try:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                },
            )
        except (OperationalError, ProgrammingError):
            return

        if created:
            user.set_password(password)
            user.save(update_fields=['password'])
            self.logger.info("Created default superuser '%s'.", username)
            return

        updates = {}
        if user.email != email:
            updates['email'] = email
        if not user.is_staff:
            updates['is_staff'] = True
        if not user.is_superuser:
            updates['is_superuser'] = True

        if updates:
            for field, value in updates.items():
                setattr(user, field, value)
            user.save(update_fields=list(updates.keys()))
            self.logger.info("Updated default superuser '%s' attributes.", username)