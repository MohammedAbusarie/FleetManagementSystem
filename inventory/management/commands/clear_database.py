"""
Management command to completely clear all data from the database
"""
import sys
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from inventory.models import (
    # Main models
    Car, Equipment, Maintenance,
    # Image models
    CarImage, EquipmentImage, CalibrationCertificateImage, FireExtinguisherImage,
    # Historical records
    CarLicenseRecord, CarInspectionRecord, EquipmentLicenseRecord,
    EquipmentInspectionRecord, FireExtinguisherInspectionRecord,
    # RBAC models
    UserProfile, ModulePermission, UserPermission,
    # Logging models
    LoginLog, ActionLog,
    # DDL models
    AdministrativeUnit, Department, Driver, CarClass, Manufacturer,
    CarModel, EquipmentModel, FunctionalLocation, Room, Location,
    Sector, Division, NotificationRecipient, ContractType, Activity, Region,
)


class Command(BaseCommand):
    help = 'Clear all data from the database (preserves schema and migrations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Keep user accounts (only clear inventory data)',
        )
        parser.add_argument(
            '--keep-logs',
            action='store_true',
            help='Keep log entries (LoginLog, ActionLog)',
        )

    def _safe_write(self, message, style_func=None):
        """Write message handling encoding issues on Windows"""
        try:
            if style_func:
                self.stdout.write(style_func(message))
            else:
                self.stdout.write(message)
        except UnicodeEncodeError:
            # Fallback for Windows console encoding issues
            try:
                safe_message = message.encode('ascii', 'replace').decode('ascii')
                if style_func:
                    self.stdout.write(style_func(safe_message))
                else:
                    self.stdout.write(safe_message)
            except:
                # Last resort: write to stderr
                print(message, file=sys.stderr)

    def handle(self, *args, **options):
        self._safe_write('Starting database cleanup...', self.style.WARNING)
        
        try:
            with transaction.atomic():
                # Clear logs first if not keeping them
                if not options['keep_logs']:
                    self._clear_logs()
                
                # Clear all inventory models
                self._clear_models(options)
                
                # Clear Django admin/auth models if not keeping users
                if not options['keep_users']:
                    self._clear_auth_models()
                
                self._safe_write('All data cleared successfully!', self.style.SUCCESS)
                        
        except Exception as e:
            error_msg = f'Error clearing database: {str(e)}'
            self._safe_write(error_msg, self.style.ERROR)
            raise

    def _clear_models(self, options):
        """Clear all inventory models"""
        self._safe_write('Clearing inventory models...')
        
        # Clear in reverse dependency order to avoid foreign key issues
        # Models with is_dummy field will preserve default values
        models_to_clear = [
            # Images and attachments (depend on Car/Equipment)
            (CarImage, 'Car images'),
            (EquipmentImage, 'Equipment images'),
            (CalibrationCertificateImage, 'Calibration certificates'),
            (FireExtinguisherImage, 'Fire extinguisher images'),
            
            # Historical records (depend on Car/Equipment)
            (CarLicenseRecord, 'Car license records'),
            (CarInspectionRecord, 'Car inspection records'),
            (EquipmentLicenseRecord, 'Equipment license records'),
            (EquipmentInspectionRecord, 'Equipment inspection records'),
            (FireExtinguisherInspectionRecord, 'Fire extinguisher inspection records'),
            
            # Maintenance (depends on Car/Equipment via GenericForeignKey)
            (Maintenance, 'Maintenance records'),
            
            # Main models (must be cleared before Division/Department/Sector due to PROTECT FKs)
            (Equipment, 'Equipment'),
            (Car, 'Cars'),
            
            # DDL models with dependencies
            # Note: Division, Department, Sector are handled in _clear_sectors_and_departments()
            # AdministrativeUnit has is_dummy field and will preserve default values
            (Location, 'Locations'),
            (Room, 'Rooms'),
            (FunctionalLocation, 'Functional locations'),
            (EquipmentModel, 'Equipment models'),
            (CarModel, 'Car models'),
            (Manufacturer, 'Manufacturers'),
            (CarClass, 'Car classes'),
            (Driver, 'Drivers'),
            (Region, 'Regions'),
            (Activity, 'Activities'),
            (ContractType, 'Contract types'),
            (NotificationRecipient, 'Notification recipients'),
            (AdministrativeUnit, 'Administrative units', True),  # Has is_dummy field - will preserve defaults
        ]
        
        # Clear models first
        
        for model_info in models_to_clear:
            # Handle both tuple formats: (model, description) or (model, description, has_protected)
            if len(model_info) == 3:
                model, description, has_protected = model_info
            else:
                model, description = model_info
                has_protected = False
            
            try:
                # Check if model has is_dummy field
                has_is_dummy = hasattr(model, '_meta') and any(
                    field.name == 'is_dummy' for field in model._meta.get_fields()
                )
                
                # For models with is_dummy, only delete non-dummy records
                if has_is_dummy:
                    queryset = model.objects.filter(is_dummy=False)
                    total_count = model.objects.count()
                    dummy_count = model.objects.filter(is_dummy=True).count()
                else:
                    queryset = model.objects.all()
                    total_count = queryset.count()
                    dummy_count = 0
                
                if total_count > 0:
                    if has_protected:
                        # For models with protected records, delete individually to handle exceptions
                        deleted_count = 0
                        for instance in queryset:
                            try:
                                instance.delete()
                                deleted_count += 1
                            except (ValueError, Exception) as e:
                                # Skip protected records (like the default Department)
                                error_str = str(e)
                                if 'لا يمكن حذف' in error_str or 'cannot delete' in error_str.lower():
                                    try:
                                        self._safe_write(f'    Skipped protected record: {instance}', self.style.WARNING)
                                    except:
                                        self._safe_write('    Skipped protected record', self.style.WARNING)
                                else:
                                    raise
                        if deleted_count > 0:
                            if dummy_count > 0:
                                msg = f'  Cleared {deleted_count} {description} (kept {dummy_count} default values)'
                            else:
                                msg = f'  Cleared {deleted_count} {description}'
                            self._safe_write(msg)
                    else:
                        # Use bulk delete for better performance
                        delete_count = queryset.count()
                        if delete_count > 0:
                            queryset.delete()
                            if dummy_count > 0:
                                msg = f'  Cleared {delete_count} {description} (kept {dummy_count} default values)'
                            else:
                                msg = f'  Cleared {delete_count} {description}'
                            self._safe_write(msg)
                        elif dummy_count > 0:
                            self._safe_write(f'  Kept {dummy_count} default {description} (nothing to clear)')
            except Exception as e:
                error_msg = f'  Could not clear {description}: {str(e)}'
                self._safe_write(error_msg, self.style.WARNING)
        
        # After clearing Cars and Equipment, we can safely clear Division/Department/Sector
        # Handle special cases with foreign key constraints (preserves default/dummy values)
        self._clear_sectors_and_departments()
    
    def _clear_sectors_and_departments(self):
        """Handle Sector, Department, and Division clearing with foreign key constraints
        This is called after Cars and Equipment are cleared, so there are no PROTECT FK issues"""
        try:
            # Clear non-dummy Departments first (keep default/dummy departments)
            dept_queryset = Department.objects.filter(is_dummy=False)
            dept_delete_count = dept_queryset.count()
            dummy_dept_count = Department.objects.filter(is_dummy=True).count()
            if dept_delete_count > 0:
                dept_queryset.delete()
                if dummy_dept_count > 0:
                    self._safe_write(f'  Cleared {dept_delete_count} departments (kept {dummy_dept_count} default values)')
                else:
                    self._safe_write(f'  Cleared {dept_delete_count} departments')

            # Ensure dummy departments remain linked to the dummy division
            dummy_division = Division.objects.filter(name='غير محدد', is_dummy=True).first()
            if dummy_division:
                Department.objects.filter(is_dummy=True).update(division=dummy_division)

            # Clear non-dummy Divisions (preserve dummy ones)
            division_queryset = Division.objects.filter(is_dummy=False)
            division_count = division_queryset.count()
            dummy_division_count = Division.objects.filter(is_dummy=True).count()
            if division_count > 0:
                division_queryset.delete()
                if dummy_division_count > 0:
                    self._safe_write(f'  Cleared {division_count} divisions (kept {dummy_division_count} default values)')
                else:
                    self._safe_write(f'  Cleared {division_count} divisions')

            # Clear non-dummy Administrative Units (keep default/dummy units)
            admin_unit_queryset = AdministrativeUnit.objects.filter(is_dummy=False)
            admin_unit_delete_count = admin_unit_queryset.count()
            dummy_admin_unit_count = AdministrativeUnit.objects.filter(is_dummy=True).count()
            if admin_unit_delete_count > 0:
                admin_unit_queryset.update(sector=None)
                admin_unit_queryset.delete()
                if dummy_admin_unit_count > 0:
                    self._safe_write(f'  Cleared {admin_unit_delete_count} administrative units (kept {dummy_admin_unit_count} default values)')
                else:
                    self._safe_write(f'  Cleared {admin_unit_delete_count} administrative units')

            # Now clear non-dummy Sectors (keep default/dummy sectors)
            sector_queryset = Sector.objects.filter(is_dummy=False)
            sector_count = sector_queryset.count()
            dummy_sector_count = Sector.objects.filter(is_dummy=True).count()
            if sector_count > 0:
                sector_queryset.delete()
                if dummy_sector_count > 0:
                    self._safe_write(f'  Cleared {sector_count} sectors (kept {dummy_sector_count} default values)')
                else:
                    self._safe_write(f'  Cleared {sector_count} sectors')
        except Exception as e:
            self._safe_write(f'  Could not clear sectors/departments/divisions: {str(e)}', self.style.WARNING)
    
    def _clear_auth_models(self):
        """Clear Django auth models"""
        self._safe_write('Clearing authentication models...')
        
        # Clear RBAC models first (they depend on User)
        try:
            user_permission_count = UserPermission.objects.count()
            if user_permission_count > 0:
                UserPermission.objects.all().delete()
                self._safe_write(f'  Cleared {user_permission_count} user permissions')
        except Exception as e:
            self._safe_write(f'  Could not clear user permissions: {str(e)}', self.style.WARNING)
        
        try:
            module_permission_count = ModulePermission.objects.count()
            if module_permission_count > 0:
                ModulePermission.objects.all().delete()
                self._safe_write(f'  Cleared {module_permission_count} module permissions')
        except Exception as e:
            self._safe_write(f'  Could not clear module permissions: {str(e)}', self.style.WARNING)
        
        try:
            user_profile_count = UserProfile.objects.count()
            if user_profile_count > 0:
                UserProfile.objects.all().delete()
                self._safe_write(f'  Cleared {user_profile_count} user profiles')
        except Exception as e:
            self._safe_write(f'  Could not clear user profiles: {str(e)}', self.style.WARNING)
        
        # Clear Django sessions
        try:
            session_count = Session.objects.count()
            if session_count > 0:
                Session.objects.all().delete()
                self._safe_write(f'  Cleared {session_count} sessions')
        except Exception as e:
            self._safe_write(f'  Could not clear sessions: {str(e)}', self.style.WARNING)
        
        # Clear users last (they may be referenced by other Django tables)
        try:
            user_count = User.objects.count()
            if user_count > 0:
                User.objects.all().delete()
                self._safe_write(f'  Cleared {user_count} users')
        except Exception as e:
            self._safe_write(f'  Could not clear users: {str(e)}', self.style.WARNING)
    
    def _clear_logs(self):
        """Clear log models"""
        self._safe_write('Clearing log models...')
        
        try:
            action_log_count = ActionLog.objects.count()
            if action_log_count > 0:
                ActionLog.objects.all().delete()
                self._safe_write(f'  Cleared {action_log_count} action logs')
        except Exception as e:
            self._safe_write(f'  Could not clear action logs: {str(e)}', self.style.WARNING)
        
        try:
            login_log_count = LoginLog.objects.count()
            if login_log_count > 0:
                LoginLog.objects.all().delete()
                self._safe_write(f'  Cleared {login_log_count} login logs')
        except Exception as e:
            self._safe_write(f'  Could not clear login logs: {str(e)}', self.style.WARNING)

