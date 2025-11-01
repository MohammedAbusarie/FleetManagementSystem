"""Management command to clean up duplicate dummy departments"""
from django.core.management.base import BaseCommand
from inventory.models import Sector, Department, Division, Car, Equipment


class Command(BaseCommand):
    help = 'Clean up duplicate dummy departments, keeping only one main "غير محدد" department'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find the main dummy department (linked to dummy sector)
        dummy_sector = Sector.objects.filter(name='غير محدد', is_dummy=True).first()
        
        if not dummy_sector:
            self.stdout.write(self.style.ERROR('Dummy sector "غير محدد" not found!'))
            return
        
        # Find the main dummy department (the one linked to dummy sector with exact name "غير محدد")
        main_dummy_dept = Department.objects.filter(
            name='غير محدد',
            sector=dummy_sector,
            is_dummy=True
        ).first()
        
        if not main_dummy_dept:
            # Try to find any dummy department linked to dummy sector
            main_dummy_dept = Department.objects.filter(
                sector=dummy_sector,
                is_dummy=True
            ).first()
            
            if not main_dummy_dept:
                self.stdout.write(self.style.ERROR('Main dummy department not found!'))
                return
            
            # Rename it to "غير محدد" if possible
            if main_dummy_dept.name != 'غير محدد':
                if dry_run:
                    self.stdout.write(self.style.WARNING(f'Would rename department {main_dummy_dept.id} from "{main_dummy_dept.name}" to "غير محدد"'))
                else:
                    try:
                        main_dummy_dept.name = 'غير محدد'
                        main_dummy_dept.save()
                        self.stdout.write(self.style.SUCCESS(f'Renamed department {main_dummy_dept.id} to "غير محدد"'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Could not rename: {e}'))
                        return
        
        self.stdout.write(self.style.SUCCESS(f'Main dummy department found: ID {main_dummy_dept.id}, Name: "{main_dummy_dept.name}"'))
        
        # Find all other dummy departments (those that are NOT the main one)
        duplicate_dummy_depts = Department.objects.filter(
            is_dummy=True
        ).exclude(id=main_dummy_dept.id)
        
        count = duplicate_dummy_depts.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No duplicate dummy departments found. Everything is clean!'))
            return
        
        self.stdout.write(self.style.WARNING(f'Found {count} duplicate dummy department(s) to clean up:'))
        
        for dept in duplicate_dummy_depts:
            self.stdout.write(f'  - ID {dept.id}: "{dept.name}" (Sector: {dept.sector.name if dept.sector else "None"})')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nIn real mode, would:'))
            self.stdout.write('  1. Migrate all Car references to main dummy department')
            self.stdout.write('  2. Migrate all Equipment references to main dummy department')
            self.stdout.write('  3. Migrate all Division references to main dummy department')
            self.stdout.write('  4. Delete duplicate dummy departments')
            return
        
        # Migrate all references from duplicate departments to main dummy department
        migrated_cars = 0
        migrated_equipment = 0
        migrated_divisions = 0
        
        for dept in duplicate_dummy_depts:
            # Migrate Car references
            cars_count = Car.objects.filter(department=dept).count()
            if cars_count > 0:
                Car.objects.filter(department=dept).update(department=main_dummy_dept)
                migrated_cars += cars_count
                self.stdout.write(self.style.SUCCESS(f'  Migrated {cars_count} car(s) from department {dept.id}'))
            
            # Also check department_code field in Car
            cars_code_count = Car.objects.filter(department_code=dept).count()
            if cars_code_count > 0:
                Car.objects.filter(department_code=dept).update(department_code=main_dummy_dept)
                migrated_cars += cars_code_count
                self.stdout.write(self.style.SUCCESS(f'  Migrated {cars_code_count} car department_code(s) from department {dept.id}'))
            
            # Migrate Equipment references
            equipment_count = Equipment.objects.filter(department=dept).count()
            if equipment_count > 0:
                Equipment.objects.filter(department=dept).update(department=main_dummy_dept)
                migrated_equipment += equipment_count
                self.stdout.write(self.style.SUCCESS(f'  Migrated {equipment_count} equipment from department {dept.id}'))
            
            # Migrate Division references
            divisions_count = Division.objects.filter(department=dept).count()
            if divisions_count > 0:
                # Check if we can migrate divisions
                for division in Division.objects.filter(department=dept):
                    # Try to migrate division to main dummy department
                    # But first check if a division with same name already exists under main dummy
                    existing_division = Division.objects.filter(
                        name=division.name,
                        department=main_dummy_dept
                    ).first()
                    
                    if existing_division:
                        # Migrate references from this division to existing one
                        Car.objects.filter(division=division).update(division=existing_division)
                        Equipment.objects.filter(division=division).update(division=existing_division)
                        division.delete()
                        migrated_divisions += 1
                    else:
                        # Just update the department reference
                        division.department = main_dummy_dept
                        division.save()
                        migrated_divisions += 1
                
                self.stdout.write(self.style.SUCCESS(f'  Migrated {divisions_count} division(s) from department {dept.id}'))
        
        # Now delete the duplicate departments
        deleted_count = 0
        for dept in duplicate_dummy_depts:
            try:
                dept.delete()
                deleted_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Deleted duplicate department {dept.id}: "{dept.name}"'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Could not delete department {dept.id}: {e}'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Cleanup Complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated_cars} car reference(s)'))
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated_equipment} equipment reference(s)'))
        self.stdout.write(self.style.SUCCESS(f'Migrated {migrated_divisions} division(s)'))
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} duplicate dummy department(s)'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        # Verify final state
        remaining_dummy_depts = Department.objects.filter(is_dummy=True).count()
        if remaining_dummy_depts == 1:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Perfect! Only {remaining_dummy_depts} dummy department remains'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠ Warning: {remaining_dummy_depts} dummy department(s) still exist'))

