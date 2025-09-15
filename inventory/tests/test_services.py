"""Service layer tests for inventory app"""
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta
from inventory.services import CarService, EquipmentService, MaintenanceService
from inventory.models import Car, Equipment, Maintenance, AdministrativeUnit, Department, Driver, CarClass, Manufacturer, CarModel, EquipmentModel, FunctionalLocation, Room, Location, Sector, NotificationRecipient, ContractType, Activity, Region


class CarServiceTest(TestCase):
    """Test cases for CarService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = CarService()
        
        # Create required related objects
        self.manufacturer = Manufacturer.objects.create(name="Toyota")
        self.car_model = CarModel.objects.create(
            manufacturer=self.manufacturer,
            name="Camry"
        )
        self.administrative_unit = AdministrativeUnit.objects.create(name="IT Department")
        self.department = Department.objects.create(name="Software")
        self.driver = Driver.objects.create(name="Ahmed Ali")
        self.car_class = CarClass.objects.create(name="Sedan")
        self.functional_location = FunctionalLocation.objects.create(name="Office Building")
        self.room = Room.objects.create(name="Room 101")
        self.notification_recipient = NotificationRecipient.objects.create(name="Maintenance Team")
        self.contract_type = ContractType.objects.create(name="Owned")
        self.activity = Activity.objects.create(name="Transportation")
        self.region = Region.objects.create(name="Central Region")
        
        # Create test cars
        self.car1 = Car.objects.create(
            fleet_no="SERVICE001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location 1",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.car_model,
            administrative_unit=self.administrative_unit,
            department_code=self.department,
            car_class=self.car_class,
            driver_name=self.driver,
            functional_location=self.functional_location,
            room=self.room,
            notification_recipient=self.notification_recipient,
            contract_type=self.contract_type,
            activity=self.activity,
            annual_inspection_end_date=date.today() + timedelta(days=30),
            car_license_end_date=date.today() + timedelta(days=60)
        )
        
        self.car2 = Car.objects.create(
            fleet_no="SERVICE002",
            plate_no_en="XYZ789",
            plate_no_ar="س ي ز ٧٨٩",
            location_description="Test Location 2",
            status='new',
            annual_inspection_end_date=date.today() - timedelta(days=10),  # Expired
            car_license_end_date=date.today() + timedelta(days=30)
        )
        
        self.car3 = Car.objects.create(
            fleet_no="SERVICE003",
            plate_no_en="DEF456",
            plate_no_ar="د ه ف ٤٥٦",
            location_description="Test Location 3",
            status='defective',
            annual_inspection_end_date=date.today() + timedelta(days=15),  # About to expire
            car_license_end_date=date.today() + timedelta(days=45)
        )
        
        # Add regions to car1
        self.car1.visited_regions.add(self.region)
    
    def test_get_all_cars(self):
        """Test service can retrieve all cars"""
        cars = self.service.get_all()
        self.assertEqual(cars.count(), 3)
        self.assertIn(self.car1, cars)
        self.assertIn(self.car2, cars)
        self.assertIn(self.car3, cars)
    
    def test_get_by_id(self):
        """Test service can retrieve car by ID"""
        car = self.service.get_by_id(self.car1.pk)
        self.assertEqual(car, self.car1)
        self.assertEqual(car.fleet_no, "SERVICE001")
    
    def test_get_cars_with_related(self):
        """Test service retrieves cars with related objects prefetched"""
        cars = self.service.get_cars_with_related()
        self.assertEqual(cars.count(), 3)
        
        # Test that related objects are prefetched (no additional queries)
        car = cars.first()
        with self.assertNumQueries(0):
            if car.manufacturer:
                _ = car.manufacturer.name
            if car.model:
                _ = car.model.name
            if car.administrative_unit:
                _ = car.administrative_unit.name
            if car.department_code:
                _ = car.department_code.name
            if car.car_class:
                _ = car.car_class.name
            if car.driver_name:
                _ = car.driver_name.name
            if car.functional_location:
                _ = car.functional_location.name
            if car.room:
                _ = car.room.name
            if car.notification_recipient:
                _ = car.notification_recipient.name
            if car.contract_type:
                _ = car.contract_type.name
            if car.activity:
                _ = car.activity.name
            _ = list(car.visited_regions.all())
    
    def test_get_cars_with_maintenance(self):
        """Test service retrieves cars with maintenance annotations"""
        # Create maintenance records
        Maintenance.objects.create(
            content_object=self.car1,
            maintenance_date=date.today() - timedelta(days=10),
            cost=500.00,
            description="Regular maintenance"
        )
        Maintenance.objects.create(
            content_object=self.car1,
            maintenance_date=date.today() - timedelta(days=5),
            cost=300.00,
            description="Oil change"
        )
        
        cars = self.service.get_cars_with_maintenance()
        car_with_maintenance = cars.get(fleet_no="SERVICE001")
        
        # Should have the latest maintenance info
        self.assertEqual(car_with_maintenance.last_maintenance_date, date.today() - timedelta(days=5))
        self.assertEqual(car_with_maintenance.last_maintenance_cost, 300.00)
    
    def test_get_expiring_cars_about_to_expire(self):
        """Test service retrieves cars about to expire"""
        cars = self.service.get_expiring_cars(expiry_status='about_to_expire', days=30)
        
        # Should include car1 (expires in 30 days) and car3 (expires in 15 days)
        # Should not include car2 (already expired)
        self.assertEqual(cars.count(), 2)
        self.assertIn(self.car1, cars)
        self.assertIn(self.car3, cars)
        self.assertNotIn(self.car2, cars)
    
    def test_get_expiring_cars_expired(self):
        """Test service retrieves expired cars"""
        cars = self.service.get_expiring_cars(expiry_status='expired', days=30)
        
        # Should include car2 (expired) and cars with no inspection date
        self.assertEqual(cars.count(), 1)
        self.assertIn(self.car2, cars)
        self.assertNotIn(self.car1, cars)
        self.assertNotIn(self.car3, cars)
    
    def test_search_cars(self):
        """Test service can search cars"""
        # Search by fleet_no
        cars = self.service.search(Car.objects.all(), 'fleet_no', 'SERVICE001')
        self.assertEqual(cars.count(), 1)
        self.assertEqual(cars.first(), self.car1)
        
        # Search by plate_no_en
        cars = self.service.search(Car.objects.all(), 'plate_no_en', 'ABC')
        self.assertEqual(cars.count(), 1)
        self.assertEqual(cars.first(), self.car1)
        
        # Search by location_description
        cars = self.service.search(Car.objects.all(), 'location_description', 'Location 2')
        self.assertEqual(cars.count(), 1)
        self.assertEqual(cars.first(), self.car2)
        
        # Search with no results
        cars = self.service.search(Car.objects.all(), 'fleet_no', 'NONEXISTENT')
        self.assertEqual(cars.count(), 0)
    
    def test_sort_cars(self):
        """Test service can sort cars"""
        # Sort by fleet_no ascending
        cars = self.service.sort(Car.objects.all(), 'fleet_no', 'asc')
        fleet_nos = [car.fleet_no for car in cars]
        self.assertEqual(fleet_nos, ['SERVICE001', 'SERVICE002', 'SERVICE003'])
        
        # Sort by fleet_no descending
        cars = self.service.sort(Car.objects.all(), 'fleet_no', 'desc')
        fleet_nos = [car.fleet_no for car in cars]
        self.assertEqual(fleet_nos, ['SERVICE003', 'SERVICE002', 'SERVICE001'])
        
        # Sort by status
        cars = self.service.sort(Car.objects.all(), 'status', 'asc')
        statuses = [car.status for car in cars]
        self.assertEqual(statuses, ['defective', 'new', 'operational'])
    
    def test_paginate_cars(self):
        """Test service can paginate cars"""
        # Test pagination with 2 items per page
        page = self.service.paginate(Car.objects.all(), page_number=1, per_page=2)
        self.assertEqual(len(page), 2)
        self.assertTrue(page.has_next())
        self.assertFalse(page.has_previous())
        
        # Test second page
        page = self.service.paginate(Car.objects.all(), page_number=2, per_page=2)
        self.assertEqual(len(page), 1)
        self.assertFalse(page.has_next())
        self.assertTrue(page.has_previous())


class EquipmentServiceTest(TestCase):
    """Test cases for EquipmentService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = EquipmentService()
        
        # Create required related objects
        self.manufacturer = Manufacturer.objects.create(name="Siemens")
        self.equipment_model = EquipmentModel.objects.create(
            manufacturer=self.manufacturer,
            name="Multimeter"
        )
        self.location = Location.objects.create(name="Lab 1")
        self.sector = Sector.objects.create(name="Electronics")
        
        # Create test equipment
        self.equipment1 = Equipment.objects.create(
            door_no="EQ001",
            plate_no="PLATE001",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.equipment_model,
            location=self.location,
            sector=self.sector,
            annual_inspection_end_date=date.today() + timedelta(days=30),
            equipment_license_end_date=date.today() + timedelta(days=60)
        )
        
        self.equipment2 = Equipment.objects.create(
            door_no="EQ002",
            plate_no="PLATE002",
            status='new',
            annual_inspection_end_date=date.today() - timedelta(days=10),  # Expired
            equipment_license_end_date=date.today() + timedelta(days=30)
        )
        
        self.equipment3 = Equipment.objects.create(
            door_no="EQ003",
            plate_no="PLATE003",
            status='defective',
            annual_inspection_end_date=date.today() + timedelta(days=15),  # About to expire
            equipment_license_end_date=date.today() + timedelta(days=45)
        )
    
    def test_get_all_equipment(self):
        """Test service can retrieve all equipment"""
        equipment = self.service.get_all()
        self.assertEqual(equipment.count(), 3)
        self.assertIn(self.equipment1, equipment)
        self.assertIn(self.equipment2, equipment)
        self.assertIn(self.equipment3, equipment)
    
    def test_get_by_id(self):
        """Test service can retrieve equipment by ID"""
        equipment = self.service.get_by_id(self.equipment1.pk)
        self.assertEqual(equipment, self.equipment1)
        self.assertEqual(equipment.door_no, "EQ001")
    
    def test_get_equipment_with_related(self):
        """Test service retrieves equipment with related objects prefetched"""
        equipment = self.service.get_equipment_with_related()
        self.assertEqual(equipment.count(), 3)
        
        # Test that related objects are prefetched (no additional queries)
        eq = equipment.first()
        with self.assertNumQueries(0):
            if eq.manufacturer:
                _ = eq.manufacturer.name
            if eq.model:
                _ = eq.model.name
            if eq.location:
                _ = eq.location.name
            if eq.sector:
                _ = eq.sector.name
            _ = list(eq.calibration_certificates.all())
    
    def test_get_equipment_with_maintenance(self):
        """Test service retrieves equipment with maintenance annotations"""
        # Create maintenance records
        Maintenance.objects.create(
            content_object=self.equipment1,
            maintenance_date=date.today() - timedelta(days=10),
            cost=200.00,
            description="Calibration"
        )
        Maintenance.objects.create(
            content_object=self.equipment1,
            maintenance_date=date.today() - timedelta(days=5),
            cost=150.00,
            description="Repair"
        )
        
        equipment = self.service.get_equipment_with_maintenance()
        eq_with_maintenance = equipment.get(door_no="EQ001")
        
        # Should have the latest maintenance info
        self.assertEqual(eq_with_maintenance.last_maintenance_date, date.today() - timedelta(days=5))
        self.assertEqual(eq_with_maintenance.last_maintenance_cost, 150.00)
    
    def test_get_expiring_equipment_about_to_expire(self):
        """Test service retrieves equipment about to expire"""
        equipment = self.service.get_expiring_equipment(expiry_status='about_to_expire', days=30)
        
        # Should include equipment1 (expires in 30 days) and equipment3 (expires in 15 days)
        # Should not include equipment2 (already expired)
        self.assertEqual(equipment.count(), 2)
        self.assertIn(self.equipment1, equipment)
        self.assertIn(self.equipment3, equipment)
        self.assertNotIn(self.equipment2, equipment)
    
    def test_get_expiring_equipment_expired(self):
        """Test service retrieves expired equipment"""
        equipment = self.service.get_expiring_equipment(expiry_status='expired', days=30)
        
        # Should include equipment2 (expired)
        self.assertEqual(equipment.count(), 1)
        self.assertIn(self.equipment2, equipment)
        self.assertNotIn(self.equipment1, equipment)
        self.assertNotIn(self.equipment3, equipment)
    
    def test_search_equipment(self):
        """Test service can search equipment"""
        # Search by door_no
        equipment = self.service.search(Equipment.objects.all(), 'door_no', 'EQ001')
        self.assertEqual(equipment.count(), 1)
        self.assertEqual(equipment.first(), self.equipment1)
        
        # Search by plate_no
        equipment = self.service.search(Equipment.objects.all(), 'plate_no', 'PLATE002')
        self.assertEqual(equipment.count(), 1)
        self.assertEqual(equipment.first(), self.equipment2)
    
    def test_sort_equipment(self):
        """Test service can sort equipment"""
        # Sort by door_no ascending
        equipment = self.service.sort(Equipment.objects.all(), 'door_no', 'asc')
        door_nos = [eq.door_no for eq in equipment]
        self.assertEqual(door_nos, ['EQ001', 'EQ002', 'EQ003'])
        
        # Sort by door_no descending
        equipment = self.service.sort(Equipment.objects.all(), 'door_no', 'desc')
        door_nos = [eq.door_no for eq in equipment]
        self.assertEqual(door_nos, ['EQ003', 'EQ002', 'EQ001'])
    
    def test_paginate_equipment(self):
        """Test service can paginate equipment"""
        # Test pagination with 2 items per page
        page = self.service.paginate(Equipment.objects.all(), page_number=1, per_page=2)
        self.assertEqual(len(page), 2)
        self.assertTrue(page.has_next())
        self.assertFalse(page.has_previous())


class MaintenanceServiceTest(TestCase):
    """Test cases for MaintenanceService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = MaintenanceService()
        
        # Create test objects
        self.car = Car.objects.create(
            fleet_no="MAINT001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
        
        self.equipment = Equipment.objects.create(
            door_no="EQ001",
            plate_no="PLATE001",
            status='new'
        )
        
        # Create test maintenance records
        self.maintenance1 = Maintenance.objects.create(
            content_object=self.car,
            maintenance_date=date.today() - timedelta(days=10),
            cost=500.00,
            description="Regular maintenance"
        )
        
        self.maintenance2 = Maintenance.objects.create(
            content_object=self.car,
            maintenance_date=date.today() - timedelta(days=5),
            cost=300.00,
            description="Oil change"
        )
        
        self.maintenance3 = Maintenance.objects.create(
            content_object=self.equipment,
            maintenance_date=date.today() - timedelta(days=3),
            cost=200.00,
            description="Calibration"
        )
    
    def test_get_all_maintenance(self):
        """Test service can retrieve all maintenance records"""
        maintenance = self.service.get_all()
        self.assertEqual(maintenance.count(), 3)
        self.assertIn(self.maintenance1, maintenance)
        self.assertIn(self.maintenance2, maintenance)
        self.assertIn(self.maintenance3, maintenance)
    
    def test_get_by_id(self):
        """Test service can retrieve maintenance by ID"""
        maintenance = self.service.get_by_id(self.maintenance1.pk)
        self.assertEqual(maintenance, self.maintenance1)
        self.assertEqual(maintenance.cost, 500.00)
    
    def test_get_maintenance_for_object(self):
        """Test service retrieves maintenance for specific object"""
        # Get maintenance for car
        car_maintenance = self.service.get_maintenance_for_object(self.car)
        self.assertEqual(car_maintenance.count(), 2)
        self.assertIn(self.maintenance1, car_maintenance)
        self.assertIn(self.maintenance2, car_maintenance)
        self.assertNotIn(self.maintenance3, car_maintenance)
        
        # Verify ordering (most recent first)
        self.assertEqual(car_maintenance.first(), self.maintenance2)
        self.assertEqual(car_maintenance.last(), self.maintenance1)
        
        # Get maintenance for equipment
        equipment_maintenance = self.service.get_maintenance_for_object(self.equipment)
        self.assertEqual(equipment_maintenance.count(), 1)
        self.assertIn(self.maintenance3, equipment_maintenance)
        self.assertNotIn(self.maintenance1, equipment_maintenance)
        self.assertNotIn(self.maintenance2, equipment_maintenance)
    
    def test_create_maintenance(self):
        """Test service can create maintenance record"""
        maintenance = self.service.create_maintenance(
            content_object=self.car,
            maintenance_date=date.today(),
            cost=100.00,
            description="Test maintenance"
        )
        
        self.assertEqual(maintenance.content_object, self.car)
        self.assertEqual(maintenance.cost, 100.00)
        self.assertEqual(maintenance.description, "Test maintenance")
        self.assertTrue(maintenance.pk is not None)
        
        # Verify it was saved to database
        self.assertEqual(Maintenance.objects.count(), 4)
        self.assertTrue(Maintenance.objects.filter(pk=maintenance.pk).exists())
    
    def test_search_maintenance(self):
        """Test service can search maintenance records"""
        # Search by description
        maintenance = self.service.search(Maintenance.objects.all(), 'description', 'maintenance')
        self.assertEqual(maintenance.count(), 1)  # Only one has "maintenance" in description
        
        # Search by description
        maintenance = self.service.search(Maintenance.objects.all(), 'description', 'Oil')
        self.assertEqual(maintenance.count(), 1)  # One has "Oil" in description
        
        # Search by description
        maintenance = self.service.search(Maintenance.objects.all(), 'description', 'Calibration')
        self.assertEqual(maintenance.count(), 1)  # One calibration record
    
    def test_sort_maintenance(self):
        """Test service can sort maintenance records"""
        # Sort by maintenance_date descending (default)
        maintenance = self.service.sort(Maintenance.objects.all(), 'maintenance_date', 'desc')
        dates = [m.maintenance_date for m in maintenance]
        self.assertEqual(dates, [
            date.today() - timedelta(days=3),  # maintenance3
            date.today() - timedelta(days=5),  # maintenance2
            date.today() - timedelta(days=10)   # maintenance1
        ])
        
        # Sort by cost ascending
        maintenance = self.service.sort(Maintenance.objects.all(), 'cost', 'asc')
        costs = [m.cost for m in maintenance]
        self.assertEqual(costs, [200.00, 300.00, 500.00])
    
    def test_paginate_maintenance(self):
        """Test service can paginate maintenance records"""
        # Test pagination with 2 items per page
        page = self.service.paginate(Maintenance.objects.all(), page_number=1, per_page=2)
        self.assertEqual(len(page), 2)
        self.assertTrue(page.has_next())
        self.assertFalse(page.has_previous())
        
        # Test second page
        page = self.service.paginate(Maintenance.objects.all(), page_number=2, per_page=2)
        self.assertEqual(len(page), 1)
        self.assertFalse(page.has_next())
        self.assertTrue(page.has_previous())