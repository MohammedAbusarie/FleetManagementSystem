"""Management command to populate organizational hierarchy test data"""
from django.core.management.base import BaseCommand
from inventory.models import Sector, AdministrativeUnit, Department, Division


class Command(BaseCommand):
    help = 'Populate organizational hierarchy with test data (Sector, Department, Division)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing hierarchy data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing all hierarchy data...'))
            
            # First, set all references to NULL to avoid PROTECT constraint issues
            from inventory.models import Car, Equipment
            
            # Clear references in Car model (including old department_code field)
            Car.objects.update(
                division=None,
                administrative_unit=None,
                department=None,
                sector=None,
                department_code=None
            )
            self.stdout.write(self.style.SUCCESS('  Cleared Car references'))
            
            # Clear references in Equipment model (including sector field)
            Equipment.objects.update(
                division=None,
                administrative_unit=None,
                department=None,
                sector=None
            )
            self.stdout.write(self.style.SUCCESS('  Cleared Equipment references'))
            
            # Now delete in reverse order to avoid foreign key constraints
            Division.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('  Deleted all Divisions'))
            
            Department.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('  Deleted all Departments'))
            
            Sector.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('  Deleted all Sectors'))
            
            self.stdout.write(self.style.SUCCESS('All hierarchy data cleared.'))
        
        self.stdout.write(self.style.WARNING('Populating organizational hierarchy...'))
        
        # Get or create dummy records
        dummy_sector, _ = Sector.objects.get_or_create(
            name='غير محدد',
            defaults={'is_dummy': True}
        )
        
        dummy_admin_unit, _ = AdministrativeUnit.objects.get_or_create(
            name='غير محدد',
            defaults={'sector': dummy_sector, 'is_dummy': True}
        )
        
        dummy_division, _ = Division.objects.get_or_create(
            name='غير محدد',
            defaults={'administrative_unit': dummy_admin_unit, 'is_dummy': True}
        )

        dummy_department, _ = Department.objects.get_or_create(
            name='غير محدد',
            defaults={'division': dummy_division, 'is_dummy': True}
        )
        if dummy_department.division != dummy_division:
            Department.objects.filter(pk=dummy_department.pk).update(
                division=dummy_division,
                is_dummy=True
            )
            dummy_department.refresh_from_db()
        
        self.stdout.write(self.style.SUCCESS('Dummy records ready'))
        
        # Create test Sectors
        sectors_data = [
            {'name': 'قطاع التقنية والابتكار', 'is_dummy': False},
            {'name': 'قطاع الخدمات', 'is_dummy': False},
            {'name': 'قطاع الإدارة', 'is_dummy': False},
            {'name': 'قطاع الموارد البشرية', 'is_dummy': False},
            {'name': 'قطاع المالية', 'is_dummy': False},
        ]
        
        created_sectors = []
        for sector_data in sectors_data:
            sector, created = Sector.objects.get_or_create(
                name=sector_data['name'],
                defaults={'is_dummy': sector_data['is_dummy']}
            )
            created_sectors.append(sector)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Sector: {sector.id}'))
        
        # Create test Administrative Units for each sector
        administrative_units_data = [
            # قطاع التقنية والابتكار
            {'name': 'إدارة تقنية المعلومات', 'sector': created_sectors[0]},
            {'name': 'إدارة البرمجيات', 'sector': created_sectors[0]},
            {'name': 'إدارة الشبكات', 'sector': created_sectors[0]},
            
            # قطاع الخدمات
            {'name': 'إدارة الخدمات العامة', 'sector': created_sectors[1]},
            {'name': 'إدارة الصيانة', 'sector': created_sectors[1]},
            {'name': 'إدارة النقل', 'sector': created_sectors[1]},
            
            # قطاع الإدارة
            {'name': 'إدارة التخطيط', 'sector': created_sectors[2]},
            {'name': 'إدارة المتابعة', 'sector': created_sectors[2]},
            
            # قطاع الموارد البشرية
            {'name': 'إدارة التوظيف', 'sector': created_sectors[3]},
            {'name': 'إدارة التدريب', 'sector': created_sectors[3]},
            
            # قطاع المالية
            {'name': 'إدارة المحاسبة', 'sector': created_sectors[4]},
            {'name': 'إدارة الميزانية', 'sector': created_sectors[4]},
        ]
        
        created_administrative_units = []
        for unit_data in administrative_units_data:
            admin_unit, created = AdministrativeUnit.objects.get_or_create(
                name=unit_data['name'],
                defaults={'sector': unit_data['sector'], 'is_dummy': False}
            )
            if not created:
                updated = False
                if admin_unit.sector != unit_data['sector']:
                    admin_unit.sector = unit_data['sector']
                    updated = True
                if admin_unit.is_dummy:
                    admin_unit.is_dummy = False
                    updated = True
                if updated:
                    admin_unit.save()
            created_administrative_units.append(admin_unit)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Administrative Unit: {admin_unit.id}'))
        
        # Create test Divisions for each administrative unit
        divisions_data = [
            # إدارة تقنية المعلومات
            {'name': 'دائرة تطوير الأنظمة', 'administrative_unit': created_administrative_units[0]},
            {'name': 'دائرة الدعم الفني', 'administrative_unit': created_administrative_units[0]},
            {'name': 'دائرة الأمان السيبراني', 'administrative_unit': created_administrative_units[0]},
            
            # إدارة البرمجيات
            {'name': 'دائرة التطوير', 'administrative_unit': created_administrative_units[1]},
            {'name': 'دائرة الاختبار', 'administrative_unit': created_administrative_units[1]},
            
            # إدارة الشبكات
            {'name': 'دائرة البنية التحتية', 'administrative_unit': created_administrative_units[2]},
            {'name': 'دائرة الاتصالات', 'administrative_unit': created_administrative_units[2]},
            
            # إدارة الخدمات العامة
            {'name': 'دائرة الصيانة العامة', 'administrative_unit': created_administrative_units[3]},
            {'name': 'دائرة النظافة', 'administrative_unit': created_administrative_units[3]},
            
            # إدارة الصيانة
            {'name': 'دائرة صيانة المباني', 'administrative_unit': created_administrative_units[4]},
            {'name': 'دائرة صيانة المعدات', 'administrative_unit': created_administrative_units[4]},
            
            # إدارة النقل
            {'name': 'دائرة الأسطول', 'administrative_unit': created_administrative_units[5]},
            {'name': 'دائرة اللوجستيات', 'administrative_unit': created_administrative_units[5]},
            
            # إدارة التخطيط
            {'name': 'دائرة التخطيط الاستراتيجي', 'administrative_unit': created_administrative_units[6]},
            {'name': 'دائرة الدراسات', 'administrative_unit': created_administrative_units[6]},
            
            # إدارة المتابعة
            {'name': 'دائرة المتابعة والرقابة', 'administrative_unit': created_administrative_units[7]},
            
            # إدارة التوظيف
            {'name': 'دائرة التوظيف والاختيار', 'administrative_unit': created_administrative_units[8]},
            {'name': 'دائرة التعيينات', 'administrative_unit': created_administrative_units[8]},
            
            # إدارة التدريب
            {'name': 'دائرة التدريب والتطوير', 'administrative_unit': created_administrative_units[9]},
            
            # إدارة المحاسبة
            {'name': 'دائرة الحسابات', 'administrative_unit': created_administrative_units[10]},
            {'name': 'دائرة المراجعة', 'administrative_unit': created_administrative_units[10]},
            
            # إدارة الميزانية
            {'name': 'دائرة التخطيط المالي', 'administrative_unit': created_administrative_units[11]},
            {'name': 'دائرة الرقابة المالية', 'administrative_unit': created_administrative_units[11]},
        ]
        
        # IMPORTANT: Create valid divisions that belong to dummy administrative unit (dummy sector)
        # This allows: Dummy Sector → Dummy Administrative Unit → Valid Division
        valid_divisions_for_dummy_unit = [
            {'name': 'دائرة عامة', 'administrative_unit': dummy_admin_unit, 'is_dummy': False},
            {'name': 'دائرة مؤقتة', 'administrative_unit': dummy_admin_unit, 'is_dummy': False},
            {'name': 'دائرة غير مصنفة', 'administrative_unit': dummy_admin_unit, 'is_dummy': False},
        ]
        division_lookup = {}
        
        for div_data in valid_divisions_for_dummy_unit:
            division, created = Division.objects.get_or_create(
                name=div_data['name'],
                defaults={'administrative_unit': div_data['administrative_unit'], 'is_dummy': div_data['is_dummy']}
            )
            division_lookup[division.name] = division
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Valid Division for Dummy Administrative Unit: {division.id}'))
        
        # Create dummy division for the main dummy administrative unit only
        # This allows: Dummy Sector → Dummy Administrative Unit → Dummy Division
        # Note: We only create one dummy division linked to the main dummy administrative unit
        # Users can always select the main dummy unit and dummy division regardless of sector
        dummy_div, created = Division.objects.get_or_create(
            name='غير محدد',
            defaults={'administrative_unit': dummy_admin_unit, 'is_dummy': True}
        )
        division_lookup[dummy_div.name] = dummy_div
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created Dummy Division: {dummy_div.id}'))
        
        # Create divisions for regular administrative units
        for div_data in divisions_data:
            division, created = Division.objects.get_or_create(
                name=div_data['name'],
                defaults={'administrative_unit': div_data['administrative_unit'], 'is_dummy': False}
            )
            division_lookup[division.name] = division
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Division: {division.id}'))

        # Create representative Departments (أقسام) linked to specific divisions
        departments_data = [
            {'name': 'قسم العمليات', 'division_name': 'دائرة تطوير الأنظمة'},
            {'name': 'قسم الدعم', 'division_name': 'دائرة الدعم الفني'},
            {'name': 'قسم الخدمات الميدانية', 'division_name': 'دائرة الصيانة العامة'},
            {'name': 'قسم اللوجستيات', 'division_name': 'دائرة اللوجستيات'},
            {'name': 'قسم التخطيط', 'division_name': 'دائرة التخطيط الاستراتيجي'},
            {'name': 'قسم المتابعة', 'division_name': 'دائرة المتابعة والرقابة'},
            {'name': 'قسم التوظيف', 'division_name': 'دائرة التوظيف والاختيار'},
            {'name': 'قسم التدريب', 'division_name': 'دائرة التدريب والتطوير'},
            {'name': 'قسم المحاسبة', 'division_name': 'دائرة الحسابات'},
            {'name': 'قسم الميزانية', 'division_name': 'دائرة التخطيط المالي'},
        ]

        created_departments = []
        for dept_data in departments_data:
            target_division = division_lookup.get(dept_data['division_name'], dummy_div)

            department, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'division': target_division, 'is_dummy': False}
            )
            if not created:
                updated = False
                if department.division != target_division:
                    department.division = target_division
                    updated = True
                if department.is_dummy:
                    department.is_dummy = False
                    updated = True
                if updated:
                    department.save()
            created_departments.append(department)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Department: {department.id}'))
        
        # Summary
        total_sectors = Sector.objects.count()
        total_administrative_units = AdministrativeUnit.objects.count()
        total_departments = Department.objects.count()
        total_divisions = Division.objects.count()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Organizational Hierarchy Population Complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Total Sectors: {total_sectors}'))
        self.stdout.write(self.style.SUCCESS(f'Total Administrative Units: {total_administrative_units}'))
        self.stdout.write(self.style.SUCCESS(f'Total Departments: {total_departments}'))
        self.stdout.write(self.style.SUCCESS(f'Total Divisions: {total_divisions}'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.WARNING('\nNote: Organizational hierarchy structure:'))
        self.stdout.write(self.style.WARNING('  - Only ONE main dummy administrative unit "غير محدد" exists'))
        self.stdout.write(self.style.WARNING('  - Only ONE main dummy division "غير محدد" exists'))
        self.stdout.write(self.style.WARNING('  - Users can select dummy administrative unit/division regardless of sector'))
        self.stdout.write(self.style.WARNING('  - Valid Sector -> Valid Administrative Unit -> Valid Division'))
        self.stdout.write(self.style.WARNING('  - Departments (الأقسام) مرتبطة مباشرة بالإدارة ضمن التسلسل الهرمي'))

