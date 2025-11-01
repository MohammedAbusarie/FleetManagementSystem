from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    
    def ready(self):
        """Auto-create default 'غير محدد' records if they don't exist"""
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
        except Exception:
            # For PostgreSQL/MySQL, try a different approach
            try:
                from .models import Sector, Department, Division
                # Check if Sector model table exists by trying to query
                Sector.objects.exists()
                self._ensure_default_records()
            except Exception:
                # Database not ready yet, skip
                pass
    
    def _ensure_default_records(self):
        """Ensure default 'غير محدد' records exist"""
        from .models import Sector, Department, Division
        
        # Create dummy Sector if it doesn't exist
        dummy_sector, _ = Sector.objects.get_or_create(
            name='غير محدد',
            defaults={'is_dummy': True}
        )
        
        # Create dummy Department linked to dummy Sector if it doesn't exist
        dummy_department, created = Department.objects.get_or_create(
            name='غير محدد',
            defaults={'sector': dummy_sector, 'is_dummy': True}
        )
        
        # Ensure department is linked to dummy sector (in case it wasn't)
        # Use update() to bypass the save() method protection
        if dummy_department.sector != dummy_sector:
            Department.objects.filter(pk=dummy_department.pk).update(
                sector=dummy_sector,
                is_dummy=True
            )
            dummy_department.refresh_from_db()
        
        # Create dummy Division linked to dummy Department if it doesn't exist
        Division.objects.get_or_create(
            name='غير محدد',
            defaults={'department': dummy_department, 'is_dummy': True}
        )