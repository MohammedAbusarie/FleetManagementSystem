from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from inventory.models import (
    Department, Driver, CarClass, Manufacturer, CarModel, EquipmentModel,
    FunctionalLocation, Room, Location, Sector, NotificationRecipient,
    ContractType, Activity, Region
)


class Command(BaseCommand):
    help = 'Create initial admin user and seed data'

    def handle(self, *args, **kwargs):
        # Create Admin group
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created:
            self.stdout.write(self.style.SUCCESS('Admin group created'))
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            user.groups.add(admin_group)
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created with password "admin123"'))
        else:
            user = User.objects.get(username='admin')
            user.groups.add(admin_group)
            self.stdout.write(self.style.WARNING('Superuser "admin" already exists'))
        
        # Seed Departments
        departments = ['IT Department', 'Operations', 'Maintenance', 'Logistics']
        for dept_name in departments:
            Department.objects.get_or_create(name=dept_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(departments)} departments'))
        
        # Seed Drivers
        drivers = ['John Doe', 'Ahmed Ali', 'Mohammed Hassan', 'Khalid Ibrahim']
        for driver_name in drivers:
            Driver.objects.get_or_create(
                name=driver_name,
                defaults={'license_number': f'LIC{drivers.index(driver_name)+1000}'}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(drivers)} drivers'))
        
        # Seed Car Classes
        car_classes = ['Sedan', 'SUV', 'Truck', 'Van']
        for class_name in car_classes:
            CarClass.objects.get_or_create(name=class_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(car_classes)} car classes'))
        
        # Seed Manufacturers
        manufacturers = ['Toyota', 'Ford', 'Chevrolet', 'Honda', 'Nissan', 'Caterpillar', 'Komatsu']
        for mfr_name in manufacturers:
            Manufacturer.objects.get_or_create(name=mfr_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(manufacturers)} manufacturers'))
        
        # Seed Car Models
        toyota = Manufacturer.objects.get(name='Toyota')
        ford = Manufacturer.objects.get(name='Ford')
        car_models = [
            ('Camry', toyota, 2023),
            ('Corolla', toyota, 2022),
            ('F-150', ford, 2023),
            ('Explorer', ford, 2022),
        ]
        for model_name, mfr, year in car_models:
            CarModel.objects.get_or_create(
                name=model_name,
                manufacturer=mfr,
                defaults={'year': year}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(car_models)} car models'))
        
        # Seed Equipment Models
        cat = Manufacturer.objects.get(name='Caterpillar')
        komatsu = Manufacturer.objects.get(name='Komatsu')
        equipment_models = [
            ('Excavator 320', cat),
            ('Bulldozer D6', cat),
            ('Loader PC200', komatsu),
        ]
        for model_name, mfr in equipment_models:
            EquipmentModel.objects.get_or_create(
                name=model_name,
                manufacturer=mfr
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(equipment_models)} equipment models'))
        
        # Seed Functional Locations
        func_locations = ['Main Office', 'Warehouse A', 'Warehouse B', 'Field Site 1']
        for loc_name in func_locations:
            FunctionalLocation.objects.get_or_create(name=loc_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(func_locations)} functional locations'))
        
        # Seed Rooms
        rooms = [
            ('Room 101', 'Building A', '1'),
            ('Room 202', 'Building A', '2'),
            ('Room 301', 'Building B', '3'),
        ]
        for room_name, building, floor in rooms:
            Room.objects.get_or_create(
                name=room_name,
                defaults={'building': building, 'floor': floor}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(rooms)} rooms'))
        
        # Seed Locations
        locations = ['Riyadh', 'Jeddah', 'Dammam', 'Mecca']
        for loc_name in locations:
            Location.objects.get_or_create(name=loc_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(locations)} locations'))
        
        # Seed Sectors
        sectors = ['Construction', 'Mining', 'Transportation', 'Utilities']
        for sector_name in sectors:
            Sector.objects.get_or_create(name=sector_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(sectors)} sectors'))
        
        # Seed Notification Recipients
        recipients = [
            ('Fleet Manager', 'fleet@example.com', '+966501234567'),
            ('Operations Manager', 'ops@example.com', '+966501234568'),
        ]
        for name, email, phone in recipients:
            NotificationRecipient.objects.get_or_create(
                name=name,
                defaults={'email': email, 'phone': phone}
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(recipients)} notification recipients'))
        
        # Seed Contract Types
        contract_types = ['Agency', 'Management Purchase', 'Lease', 'Rental']
        for ct_name in contract_types:
            ContractType.objects.get_or_create(name=ct_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(contract_types)} contract types'))
        
        # Seed Activities
        activities = ['Passenger Transport', 'Cargo Transport', 'Construction', 'Maintenance']
        for activity_name in activities:
            Activity.objects.get_or_create(name=activity_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(activities)} activities'))
        
        # Seed Regions
        regions = ['Central Region', 'Western Region', 'Eastern Region', 'Northern Region', 'Southern Region']
        for region_name in regions:
            Region.objects.get_or_create(name=region_name)
        self.stdout.write(self.style.SUCCESS(f'Created {len(regions)} regions'))
        
        self.stdout.write(self.style.SUCCESS('Initial data setup completed successfully!'))

