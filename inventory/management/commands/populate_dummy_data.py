import os
import random
import shutil
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db import transaction
from django.utils import timezone
import pandas as pd

from inventory.models import (
    AdministrativeUnit, Department, Driver, CarClass, Manufacturer, CarModel, EquipmentModel,
    FunctionalLocation, Room, Location, Sector, NotificationRecipient, ContractType, 
    Activity, Region, Car, Equipment, CalibrationCertificateImage, Maintenance
)


class Command(BaseCommand):
    help = 'Clear database and populate with dummy data from Excel files and images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-only',
            action='store_true',
            help='Only clear the database without populating new data',
        )

    def handle(self, *args, **options):
        if options['clear_only']:
            self.clear_database()
            return

        self.stdout.write(self.style.WARNING('Starting database population...'))
        
        # Clear existing data
        self.clear_database()
        
        # Create lookup tables
        self.create_lookup_tables()
        
        # Populate cars from Excel
        self.populate_cars()
        
        # Populate equipment from Excel
        self.populate_equipment()
        
        # Create maintenance records
        self.create_maintenance_records()
        
        self.stdout.write(self.style.SUCCESS('Database population completed successfully!'))

    def clear_database(self):
        """Clear all data from the database"""
        self.stdout.write(self.style.WARNING('Clearing existing data...'))
        
        # Delete in reverse order to avoid foreign key constraints
        Maintenance.objects.all().delete()
        CalibrationCertificateImage.objects.all().delete()
        Equipment.objects.all().delete()
        Car.objects.all().delete()
        
        # Clear lookup tables
        Region.objects.all().delete()
        Activity.objects.all().delete()
        ContractType.objects.all().delete()
        NotificationRecipient.objects.all().delete()
        Sector.objects.all().delete()
        Location.objects.all().delete()
        Room.objects.all().delete()
        FunctionalLocation.objects.all().delete()
        EquipmentModel.objects.all().delete()
        CarModel.objects.all().delete()
        Manufacturer.objects.all().delete()
        CarClass.objects.all().delete()
        Driver.objects.all().delete()
        Department.objects.all().delete()
        AdministrativeUnit.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Database cleared successfully!'))

    def create_lookup_tables(self):
        """Create lookup tables based on Excel data"""
        self.stdout.write(self.style.WARNING('Creating lookup tables...'))
        
        # Read Excel files
        excel_files = [f for f in os.listdir('dummy_media') if f.endswith('.xlsx')]
        cars_df = pd.read_excel(f'dummy_media/{excel_files[0]}')
        equipment_df = pd.read_excel(f'dummy_media/{excel_files[1]}')
        
        # Create Administrative Units from cars data
        admin_units = cars_df['الإدارة'].dropna().unique()
        for unit in admin_units:
            AdministrativeUnit.objects.get_or_create(name=str(unit))
        
        # Create Departments from cars data
        departments = cars_df['Department'].dropna().unique()
        for dept in departments:
            Department.objects.get_or_create(name=str(dept))
        
        # Create Car Classes from cars data
        car_classes = cars_df['Class'].dropna().unique()
        for car_class in car_classes:
            CarClass.objects.get_or_create(name=str(car_class))
        
        # Create Manufacturers from both cars and equipment data
        manufacturers_cars = cars_df['Manufacturer'].dropna().unique()
        manufacturers_equipment = equipment_df['المصـــنع'].dropna().unique()
        all_manufacturers = set(manufacturers_cars) | set(manufacturers_equipment)
        
        for mfr in all_manufacturers:
            Manufacturer.objects.get_or_create(name=str(mfr))
        
        # Create Car Models
        car_models_created = set()
        for _, row in cars_df.iterrows():
            if pd.notna(row['Manufacturer']) and pd.notna(row['Model No']):
                manufacturer, created = Manufacturer.objects.get_or_create(name=str(row['Manufacturer']))
                model_name = str(row['Model No'])
                if model_name not in car_models_created:
                    try:
                        CarModel.objects.get_or_create(
                            name=model_name,
                            manufacturer=manufacturer,
                            defaults={'year': random.randint(2015, 2024)}
                        )
                        car_models_created.add(model_name)
                    except Exception as e:
                        # Skip if there's a duplicate
                        continue
        
        # Create Equipment Models
        equipment_models_created = set()
        for _, row in equipment_df.iterrows():
            if pd.notna(row['المصـــنع']) and pd.notna(row['الموديل']):
                manufacturer, created = Manufacturer.objects.get_or_create(name=str(row['المصـــنع']))
                model_name = str(row['الموديل'])
                if model_name not in equipment_models_created:
                    try:
                        EquipmentModel.objects.get_or_create(
                            name=model_name,
                            manufacturer=manufacturer
                        )
                        equipment_models_created.add(model_name)
                    except Exception as e:
                        # Skip if there's a duplicate
                        continue
        
        # Create Functional Locations
        func_locations = cars_df['Functional Location'].dropna().unique()
        for loc in func_locations:
            FunctionalLocation.objects.get_or_create(name=str(loc))
        
        # Create Rooms
        rooms = cars_df['Room'].dropna().unique()
        for room in rooms:
            Room.objects.get_or_create(
                name=str(room),
                defaults={'building': f'Building {random.choice(["A", "B", "C"])}', 'floor': str(random.randint(1, 5))}
            )
        
        # Create Locations for equipment
        locations = equipment_df['الموقع'].dropna().unique()
        for loc in locations:
            Location.objects.get_or_create(name=str(loc))
        
        # Create Sectors
        sectors = equipment_df['القطاع'].dropna().unique()
        for sector in sectors:
            Sector.objects.get_or_create(name=str(sector))
        
        # Create Notification Recipients
        recipients = cars_df['مستلم الاشعار'].dropna().unique()
        for recipient in recipients:
            NotificationRecipient.objects.get_or_create(
                name=str(recipient),
                defaults={'email': f'{str(recipient).lower().replace(" ", ".")}@company.com', 'phone': f'+966{random.randint(500000000, 599999999)}'}
            )
        
        # Create Contract Types
        contract_types = cars_df['العقد'].dropna().unique()
        for contract in contract_types:
            ContractType.objects.get_or_create(name=str(contract))
        
        # Create Activities
        activities = cars_df['النشاط'].dropna().unique()
        for activity in activities:
            Activity.objects.get_or_create(name=str(activity))
        
        # Create Regions
        regions = ['المنطقة الوسطى', 'المنطقة الغربية', 'المنطقة الشرقية', 'المنطقة الشمالية', 'المنطقة الجنوبية']
        for region in regions:
            Region.objects.get_or_create(name=region)
        
        # Create Drivers
        driver_names = ['أحمد محمد', 'خالد عبدالله', 'محمد علي', 'عبدالرحمن حسن', 'سعد إبراهيم', 'فهد سالم', 'عمر ناصر', 'يوسف أحمد']
        for driver in driver_names:
            Driver.objects.get_or_create(
                name=driver,
                defaults={'license_number': f'LIC{random.randint(1000, 9999)}', 'phone': f'+966{random.randint(500000000, 599999999)}'}
            )
        
        self.stdout.write(self.style.SUCCESS('Lookup tables created successfully!'))

    def populate_cars(self):
        """Populate cars from Excel data"""
        self.stdout.write(self.style.WARNING('Populating cars...'))
        
        excel_files = [f for f in os.listdir('dummy_media') if f.endswith('.xlsx')]
        cars_df = pd.read_excel(f'dummy_media/{excel_files[0]}')
        
        car_images_dir = 'dummy_media/cars'
        car_image_folders = [f for f in os.listdir(car_images_dir) if os.path.isdir(os.path.join(car_images_dir, f))]
        
        created_count = 0
        
        for _, row in cars_df.iterrows():
            try:
                # Get random car image
                random_folder = random.choice(car_image_folders)
                image_files = [f for f in os.listdir(os.path.join(car_images_dir, random_folder)) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                random_image = random.choice(image_files)
                image_path = os.path.join(car_images_dir, random_folder, random_image)
                
                # Create car with all fields
                fleet_no = str(row['Fleet No']) if pd.notna(row['Fleet No']) else f'FLEET{random.randint(1000, 9999)}'
                plate_no_en = str(row['Plate No(EN)']) if pd.notna(row['Plate No(EN)']) else f'EN{random.randint(1000, 9999)}'
                plate_no_ar = str(row['Plate No(AR)']) if pd.notna(row['Plate No(AR)']) else f'AR{random.randint(1000, 9999)}'
                
                # Ensure unique fleet number
                counter = 1
                original_fleet = fleet_no
                while Car.objects.filter(fleet_no=fleet_no).exists():
                    fleet_no = f"{original_fleet}_{counter}"
                    counter += 1
                
                # Ensure unique plate numbers
                counter = 1
                original_plate_en = plate_no_en
                while Car.objects.filter(plate_no_en=plate_no_en).exists():
                    plate_no_en = f"{original_plate_en}_{counter}"
                    counter += 1
                
                counter = 1
                original_plate_ar = plate_no_ar
                while Car.objects.filter(plate_no_ar=plate_no_ar).exists():
                    plate_no_ar = f"{original_plate_ar}_{counter}"
                    counter += 1
                
                car = Car.objects.create(
                    fleet_no=fleet_no,
                    plate_no_en=plate_no_en,
                    plate_no_ar=plate_no_ar,
                    
                    # Foreign keys
                    administrative_unit=AdministrativeUnit.objects.filter(name=str(row['الإدارة'])).first() if pd.notna(row['الإدارة']) else None,
                    department_code=Department.objects.filter(name=str(row['Department'])).first() if pd.notna(row['Department']) else None,
                    driver_name=Driver.objects.order_by('?').first(),
                    car_class=CarClass.objects.filter(name=str(row['Class'])).first() if pd.notna(row['Class']) else None,
                    manufacturer=Manufacturer.objects.filter(name=str(row['Manufacturer'])).first() if pd.notna(row['Manufacturer']) else None,
                    model=CarModel.objects.filter(name=str(row['Model No'])).first() if pd.notna(row['Model No']) else None,
                    functional_location=FunctionalLocation.objects.filter(name=str(row['Functional Location'])).first() if pd.notna(row['Functional Location']) else None,
                    room=Room.objects.filter(name=str(row['Room'])).first() if pd.notna(row['Room']) else None,
                    notification_recipient=NotificationRecipient.objects.filter(name=str(row['مستلم الاشعار'])).first() if pd.notna(row['مستلم الاشعار']) else None,
                    contract_type=ContractType.objects.filter(name=str(row['العقد'])).first() if pd.notna(row['العقد']) else None,
                    activity=Activity.objects.filter(name=str(row['النشاط'])).first() if pd.notna(row['النشاط']) else None,
                    
                    # Ownership and status
                    ownership_type=self._map_ownership_type(str(row['Owned/Leased'])) if pd.notna(row['Owned/Leased']) else 'owned',
                    status=random.choice(['operational', 'new', 'defective', 'under_maintenance']),
                    
                    # Location details
                    location_description=str(row['Location Description']) if pd.notna(row['Location Description']) else 'موقع افتراضي',
                    address_details_1=str(row['Address Details 1']) if pd.notna(row['Address Details 1']) else '',
                    
                    # Dates
                    car_license_start_date=self._generate_random_date(2020, 2024),
                    car_license_end_date=self._generate_random_date(2024, 2026),
                    annual_inspection_start_date=self._generate_random_date(2023, 2024),
                    annual_inspection_end_date=self._generate_mixed_expiry_date(),
                )
                
                # Add image
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        car.car_image.save(random_image, File(f), save=True)
                
                # Add visited regions
                regions = Region.objects.all()
                if regions.exists():
                    car.visited_regions.set(random.sample(list(regions), random.randint(1, 3)))
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating car: {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} cars successfully!'))

    def populate_equipment(self):
        """Populate equipment from Excel data"""
        self.stdout.write(self.style.WARNING('Populating equipment...'))
        
        excel_files = [f for f in os.listdir('dummy_media') if f.endswith('.xlsx')]
        equipment_df = pd.read_excel(f'dummy_media/{excel_files[1]}')
        
        equipment_images_dir = 'dummy_media/equipments'
        equipment_image_files = [f for f in os.listdir(equipment_images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        created_count = 0
        
        for _, row in equipment_df.iterrows():
            try:
                # Get random equipment image
                random_image = random.choice(equipment_image_files)
                image_path = os.path.join(equipment_images_dir, random_image)
                
                # Create equipment
                plate_no = str(row['رقم اللوحة']) if pd.notna(row['رقم اللوحة']) else f'PLATE{random.randint(1000, 9999)}'
                # Ensure unique plate number
                counter = 1
                original_plate = plate_no
                while Equipment.objects.filter(plate_no=plate_no).exists():
                    plate_no = f"{original_plate}_{counter}"
                    counter += 1
                
                door_no = str(row['رقم الباب']) if pd.notna(row['رقم الباب']) else f'DOOR{random.randint(1000, 9999)}'
                # Ensure unique door number
                counter = 1
                original_door = door_no
                while Equipment.objects.filter(door_no=door_no).exists():
                    door_no = f"{original_door}_{counter}"
                    counter += 1
                
                # Handle manufacture year
                try:
                    manufacture_year = int(row['سنةالصنع']) if pd.notna(row['سنةالصنع']) else random.randint(2015, 2024)
                except (ValueError, TypeError):
                    manufacture_year = random.randint(2015, 2024)
                
                equipment = Equipment.objects.create(
                    door_no=door_no,
                    plate_no=plate_no,
                    manufacture_year=manufacture_year,
                    
                    # Foreign keys
                    manufacturer=Manufacturer.objects.filter(name=str(row['المصـــنع'])).first() if pd.notna(row['المصـــنع']) else None,
                    model=EquipmentModel.objects.filter(name=str(row['الموديل'])).first() if pd.notna(row['الموديل']) else None,
                    location=Location.objects.filter(name=str(row['الموقع'])).first() if pd.notna(row['الموقع']) else None,
                    sector=Sector.objects.filter(name=str(row['القطاع'])).first() if pd.notna(row['القطاع']) else None,
                    
                    # Status
                    status=self._map_equipment_status(str(row['حاله المعدة'])) if pd.notna(row['حاله المعدة']) else 'operational',
                    
                    # Dates
                    equipment_license_start_date=self._generate_random_date(2020, 2024),
                    equipment_license_end_date=self._generate_random_date(2024, 2026),
                    annual_inspection_start_date=self._generate_random_date(2023, 2024),
                    annual_inspection_end_date=self._generate_mixed_expiry_date(),
                )
                
                # Add image
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        equipment.equipment_image.save(random_image, File(f), save=True)
                
                # Add calibration certificates
                certificates_dir = 'dummy_media/certificates'
                if os.path.exists(certificates_dir):
                    cert_files = [f for f in os.listdir(certificates_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf'))]
                    # Add 1-3 random certificates
                    num_certs = random.randint(1, 3)
                    selected_certs = random.sample(cert_files, min(num_certs, len(cert_files)))
                    
                    for cert_file in selected_certs:
                        cert_path = os.path.join(certificates_dir, cert_file)
                        with open(cert_path, 'rb') as f:
                            CalibrationCertificateImage.objects.create(
                                equipment=equipment,
                                image=File(f, name=cert_file)
                            )
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating equipment: {str(e)}'))
                continue
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} equipment successfully!'))

    def create_maintenance_records(self):
        """Create maintenance records for cars and equipment"""
        self.stdout.write(self.style.WARNING('Creating maintenance records...'))
        
        cars = Car.objects.all()
        equipment = Equipment.objects.all()
        
        created_count = 0
        
        # Create maintenance records for cars
        for car in cars:
            # Create 1-5 maintenance records per car
            num_records = random.randint(1, 5)
            for _ in range(num_records):
                maintenance_date = self._generate_random_date(2020, 2024)
                restoration_date = maintenance_date + timedelta(days=random.randint(1, 30))
                
                Maintenance.objects.create(
                    content_object=car,
                    maintenance_date=maintenance_date,
                    restoration_date=restoration_date,
                    cost=Decimal(random.uniform(100, 5000)).quantize(Decimal('0.01')),
                    description=f'صيانة دورية للسيارة {car.fleet_no} - {random.choice(["تغيير الزيت", "فحص المكابح", "صيانة المحرك", "فحص الإطارات", "صيانة نظام التبريد"])}'
                )
                created_count += 1
        
        # Create maintenance records for equipment
        for equip in equipment:
            # Create 1-3 maintenance records per equipment
            num_records = random.randint(1, 3)
            for _ in range(num_records):
                maintenance_date = self._generate_random_date(2020, 2024)
                restoration_date = maintenance_date + timedelta(days=random.randint(1, 15))
                
                Maintenance.objects.create(
                    content_object=equip,
                    maintenance_date=maintenance_date,
                    restoration_date=restoration_date,
                    cost=Decimal(random.uniform(500, 10000)).quantize(Decimal('0.01')),
                    description=f'صيانة دورية للمعدة {equip.door_no} - {random.choice(["فحص الهيدروليك", "صيانة المحرك", "فحص الأنظمة الكهربائية", "تنظيف وفحص", "معايرة الأجهزة"])}'
                )
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} maintenance records successfully!'))

    def _map_ownership_type(self, ownership_str):
        """Map ownership string to model choice"""
        ownership_mapping = {
            'owned': 'owned',
            'leased': 'leased_regular',
            'rental': 'leased_non_regular',
            'employee': 'leased_emp_24hrs'
        }
        return ownership_mapping.get(ownership_str.lower(), 'owned')

    def _map_equipment_status(self, status_str):
        """Map equipment status string to model choice"""
        status_mapping = {
            'عاملة': 'operational',
            'جديدة': 'new',
            'معطلة': 'defective',
            'مكهنة': 'defective',
            'تحت الصيانة': 'under_maintenance'
        }
        return status_mapping.get(status_str, 'operational')

    def _generate_random_date(self, start_year, end_year):
        """Generate a random date between start_year and end_year"""
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 12, 31)
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randint(0, days_between)
        return start_date + timedelta(days=random_days)

    def _generate_about_to_expire_date(self):
        """Generate a future date that is about to expire (1-90 days from today)"""
        today = date.today()
        # Generate future dates between 1 and 90 days from today
        days_from_today = random.randint(1, 90)
        return today + timedelta(days=days_from_today)

    def _generate_mixed_expiry_date(self):
        """Generate a mix of about-to-expire (future) and expired dates"""
        today = date.today()
        # 70% chance of about-to-expire (future dates), 30% chance of expired (past dates)
        if random.random() < 0.7:
            # About to expire (future dates: 1-90 days from today)
            days_from_today = random.randint(1, 90)
            return today + timedelta(days=days_from_today)
        else:
            # Expired (past dates: 1-60 days ago)
            days_ago = random.randint(1, 60)
            return today - timedelta(days=days_ago)
