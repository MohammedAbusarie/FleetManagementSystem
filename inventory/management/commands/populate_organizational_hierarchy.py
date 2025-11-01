"""Management command to populate organizational hierarchy test data"""
from django.core.management.base import BaseCommand
from inventory.models import Sector, Department, Division


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
            Car.objects.update(division=None, department=None, sector=None, department_code=None)
            self.stdout.write(self.style.SUCCESS('  Cleared Car references'))
            
            # Clear references in Equipment model (including sector field)
            Equipment.objects.update(division=None, department=None, sector=None)
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
        
        dummy_department, _ = Department.objects.get_or_create(
            name='غير محدد',
            defaults={'sector': dummy_sector, 'is_dummy': True}
        )
        
        dummy_division, _ = Division.objects.get_or_create(
            name='غير محدد',
            defaults={'department': dummy_department, 'is_dummy': True}
        )
        
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
        
        # Create test Departments for each sector
        departments_data = [
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
        
        created_departments = []
        for dept_data in departments_data:
            department, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'sector': dept_data['sector'], 'is_dummy': False}
            )
            # If department already existed, make sure it's linked to the correct sector
            if not created and department.sector != dept_data['sector']:
                department.sector = dept_data['sector']
                department.is_dummy = False
                department.save()
            created_departments.append(department)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Department: {department.id}'))
        
        # Create dummy departments for valid sectors (to support: Valid Sector → Dummy Department)
        # Since name must be unique, we'll use "غير محدد" for each sector
        # But handle existing ones that might have longer names
        dummy_depts_for_valid_sectors = []
        for sector in created_sectors:  # Create dummy depts for all valid sectors
            # Check if a dummy department already exists for this sector
            existing_dummy = Department.objects.filter(
                sector=sector,
                is_dummy=True
            ).first()
            
            if existing_dummy:
                # Use existing dummy department
                dummy_dept = existing_dummy
                # Update name to just "غير محدد" if it has a longer name
                if existing_dummy.name != 'غير محدد' and 'غير محدد' in existing_dummy.name:
                    # Try to update, but if unique constraint fails, keep existing name
                    try:
                        existing_dummy.name = 'غير محدد'
                        existing_dummy.save()
                    except:
                        pass  # Keep existing name if update fails due to uniqueness
            else:
                # Create new dummy department with unique name
                # Use sector ID to make it unique
                dummy_dept, created = Department.objects.get_or_create(
                    name=f'غير محدد ({sector.id})',
                    defaults={'sector': sector, 'is_dummy': True}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created Dummy Department for Sector: {dummy_dept.id}'))
            
            dummy_depts_for_valid_sectors.append(dummy_dept)
        
        # Create test Divisions for each department
        divisions_data = [
            # إدارة تقنية المعلومات
            {'name': 'دائرة تطوير الأنظمة', 'department': created_departments[0]},
            {'name': 'دائرة الدعم الفني', 'department': created_departments[0]},
            {'name': 'دائرة الأمان السيبراني', 'department': created_departments[0]},
            
            # إدارة البرمجيات
            {'name': 'دائرة التطوير', 'department': created_departments[1]},
            {'name': 'دائرة الاختبار', 'department': created_departments[1]},
            
            # إدارة الشبكات
            {'name': 'دائرة البنية التحتية', 'department': created_departments[2]},
            {'name': 'دائرة الاتصالات', 'department': created_departments[2]},
            
            # إدارة الخدمات العامة
            {'name': 'دائرة الصيانة العامة', 'department': created_departments[3]},
            {'name': 'دائرة النظافة', 'department': created_departments[3]},
            
            # إدارة الصيانة
            {'name': 'دائرة صيانة المباني', 'department': created_departments[4]},
            {'name': 'دائرة صيانة المعدات', 'department': created_departments[4]},
            
            # إدارة النقل
            {'name': 'دائرة الأسطول', 'department': created_departments[5]},
            {'name': 'دائرة اللوجستيات', 'department': created_departments[5]},
            
            # إدارة التخطيط
            {'name': 'دائرة التخطيط الاستراتيجي', 'department': created_departments[6]},
            {'name': 'دائرة الدراسات', 'department': created_departments[6]},
            
            # إدارة المتابعة
            {'name': 'دائرة المتابعة والرقابة', 'department': created_departments[7]},
            
            # إدارة التوظيف
            {'name': 'دائرة التوظيف والاختيار', 'department': created_departments[8]},
            {'name': 'دائرة التعيينات', 'department': created_departments[8]},
            
            # إدارة التدريب
            {'name': 'دائرة التدريب والتطوير', 'department': created_departments[9]},
            
            # إدارة المحاسبة
            {'name': 'دائرة الحسابات', 'department': created_departments[10]},
            {'name': 'دائرة المراجعة', 'department': created_departments[10]},
            
            # إدارة الميزانية
            {'name': 'دائرة التخطيط المالي', 'department': created_departments[11]},
            {'name': 'دائرة الرقابة المالية', 'department': created_departments[11]},
        ]
        
        # IMPORTANT: Create valid divisions that belong to dummy department (dummy sector)
        # This allows: Dummy Sector → Dummy Department → Valid Division
        valid_divisions_for_dummy_dept = [
            {'name': 'دائرة عامة', 'department': dummy_department, 'is_dummy': False},
            {'name': 'دائرة مؤقتة', 'department': dummy_department, 'is_dummy': False},
            {'name': 'دائرة غير مصنفة', 'department': dummy_department, 'is_dummy': False},
        ]
        
        for div_data in valid_divisions_for_dummy_dept:
            division, created = Division.objects.get_or_create(
                name=div_data['name'],
                defaults={'department': div_data['department'], 'is_dummy': div_data['is_dummy']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Valid Division for Dummy Dept: {division.id}'))
        
        # Create dummy divisions for dummy departments (both dummy sector and valid sector dummy depts)
        # This allows: Valid Sector → Dummy Department → Dummy Division
        # This allows: Dummy Sector → Dummy Department → Dummy Division
        dummy_divisions = []
        for dummy_dept in [dummy_department] + dummy_depts_for_valid_sectors:
            dummy_div_name = f'غير محدد - {dummy_dept.sector.name if dummy_dept.sector else "عام"}'
            dummy_div, created = Division.objects.get_or_create(
                name=dummy_div_name,
                defaults={'department': dummy_dept, 'is_dummy': True}
            )
            dummy_divisions.append(dummy_div)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Dummy Division: {dummy_div.id}'))
        
        # Create valid divisions for dummy departments under valid sectors
        # This allows: Valid Sector → Dummy Department → Valid Division
        for dummy_dept in dummy_depts_for_valid_sectors:
            valid_divs_for_dummy_dept = [
                {'name': f'دائرة عامة - {dummy_dept.sector.name}', 'department': dummy_dept, 'is_dummy': False},
                {'name': f'دائرة مؤقتة - {dummy_dept.sector.name}', 'department': dummy_dept, 'is_dummy': False},
            ]
            for div_data in valid_divs_for_dummy_dept:
                division, created = Division.objects.get_or_create(
                    name=div_data['name'],
                    defaults={'department': div_data['department'], 'is_dummy': div_data['is_dummy']}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Created Valid Division for Valid Sector Dummy Dept: {division.id}'))
        
        # Create divisions for regular departments
        for div_data in divisions_data:
            division, created = Division.objects.get_or_create(
                name=div_data['name'],
                defaults={'department': div_data['department'], 'is_dummy': False}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created Division: {division.id}'))
        
        # Summary
        total_sectors = Sector.objects.count()
        total_departments = Department.objects.count()
        total_divisions = Division.objects.count()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Organizational Hierarchy Population Complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Total Sectors: {total_sectors}'))
        self.stdout.write(self.style.SUCCESS(f'Total Departments: {total_departments}'))
        self.stdout.write(self.style.SUCCESS(f'Total Divisions: {total_divisions}'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.WARNING('\nNote: All combinations are now supported:'))
        self.stdout.write(self.style.WARNING('  - Valid Sector -> Dummy Department -> Dummy Division'))
        self.stdout.write(self.style.WARNING('  - Valid Sector -> Dummy Department -> Valid Division'))
        self.stdout.write(self.style.WARNING('  - Dummy Sector -> Dummy Department -> Dummy Division'))
        self.stdout.write(self.style.WARNING('  - Dummy Sector -> Dummy Department -> Valid Division'))
        self.stdout.write(self.style.WARNING('  - Valid Sector -> Valid Department -> Valid Division'))

