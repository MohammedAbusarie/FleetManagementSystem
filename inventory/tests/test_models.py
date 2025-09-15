"""Model tests for inventory app"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
from inventory.models import Car, Equipment, Maintenance, AdministrativeUnit, Department, Driver, CarClass, Manufacturer, CarModel, EquipmentModel, FunctionalLocation, Room, Location, Sector, NotificationRecipient, ContractType, Activity, Region, CalibrationCertificateImage
from inventory.constants import CAR_STATUS_CHOICES, EQUIPMENT_STATUS_CHOICES


class CarModelTest(TestCase):
    """Test cases for Car model"""
    
    def setUp(self):
        """Set up test data"""
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
    
    def test_car_creation_minimal(self):
        """Test car can be created with minimal required fields"""
        car = Car.objects.create(
            fleet_no="TEST001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
        self.assertEqual(car.fleet_no, "TEST001")
        self.assertEqual(car.plate_no_en, "ABC123")
        self.assertEqual(car.plate_no_ar, "أ ب ج ١٢٣")
        self.assertEqual(car.status, 'new')
        self.assertTrue(car.pk is not None)
    
    def test_car_creation_with_related_objects(self):
        """Test car can be created with related objects"""
        car = Car.objects.create(
            fleet_no="TEST002",
            plate_no_en="XYZ789",
            plate_no_ar="س ي ز ٧٨٩",
            location_description="Full Test Location",
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
        
        # Test all fields are saved correctly
        self.assertEqual(car.fleet_no, "TEST002")
        self.assertEqual(car.manufacturer, self.manufacturer)
        self.assertEqual(car.model, self.car_model)
        self.assertEqual(car.status, 'operational')
    
    def test_car_fleet_no_unique(self):
        """Test that fleet_no must be unique"""
        Car.objects.create(
            fleet_no="UNIQUE001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
        
        with self.assertRaises(IntegrityError):
            Car.objects.create(
                fleet_no="UNIQUE001",  # Same fleet_no
                plate_no_en="XYZ789",
                plate_no_ar="س ي ز ٧٨٩",
                location_description="Another Location",
                status='new'
            )
    
    def test_car_status_choices(self):
        """Test car status field accepts valid choices"""
        for i, (status, _) in enumerate(CAR_STATUS_CHOICES):
            car = Car.objects.create(
                fleet_no=f"STATUS_{status}_{i}",
                plate_no_en=f"ABC{i:03d}",
                plate_no_ar=f"أ ب ج {i:03d}",
                location_description="Test Location",
                status=status
            )
            self.assertEqual(car.status, status)
    
    def test_car_string_representation(self):
        """Test car string representation"""
        car = Car.objects.create(
            fleet_no="STR001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
        # The __str__ method should return fleet_no - plate_no_en
        self.assertEqual(str(car), "STR001 - ABC123")
    
    def test_car_inspection_expired_property(self):
        """Test car inspection expiry properties"""
        # Car with expired inspection
        expired_car = Car.objects.create(
            fleet_no="EXPIRED001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new',
            annual_inspection_end_date=date.today() - timedelta(days=10)
        )
        self.assertTrue(expired_car.is_inspection_expired)
        self.assertEqual(expired_car.days_until_inspection_expiry, -10)  # Negative days for expired
        
        # Car with valid inspection
        valid_car = Car.objects.create(
            fleet_no="VALID001",
            plate_no_en="XYZ789",
            plate_no_ar="س ي ز ٧٨٩",
            location_description="Test Location",
            status='new',
            annual_inspection_end_date=date.today() + timedelta(days=30)
        )
        self.assertFalse(valid_car.is_inspection_expired)
        self.assertEqual(valid_car.days_until_inspection_expiry, 30)
        
        # Car with no inspection date
        no_date_car = Car.objects.create(
            fleet_no="NODATE001",
            plate_no_en="DEF456",
            plate_no_ar="د ه ف ٤٥٦",
            location_description="Test Location",
            status='new'
        )
        self.assertTrue(no_date_car.is_inspection_expired)
        self.assertIsNone(no_date_car.days_until_inspection_expiry)
    
    def test_car_visited_regions_m2m(self):
        """Test many-to-many relationship with regions"""
        car = Car.objects.create(
            fleet_no="REGION001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='new'
        )
        
        # Add regions
        car.visited_regions.add(self.region)
        self.assertEqual(car.visited_regions.count(), 1)
        self.assertIn(self.region, car.visited_regions.all())


class EquipmentModelTest(TestCase):
    """Test cases for Equipment model"""
    
    def setUp(self):
        """Set up test data"""
        self.manufacturer = Manufacturer.objects.create(name="Siemens")
        self.equipment_model = EquipmentModel.objects.create(
            manufacturer=self.manufacturer,
            name="Multimeter"
        )
        self.location = Location.objects.create(name="Lab 1")
        self.sector = Sector.objects.create(name="Electronics")
    
    def test_equipment_creation_minimal(self):
        """Test equipment can be created with minimal required fields"""
        equipment = Equipment.objects.create(
            door_no="EQ001",
            plate_no="PLATE001",
            status='new'
        )
        self.assertEqual(equipment.door_no, "EQ001")
        self.assertEqual(equipment.plate_no, "PLATE001")
        self.assertEqual(equipment.status, 'new')
        self.assertTrue(equipment.pk is not None)
    
    def test_equipment_creation_with_related_objects(self):
        """Test equipment can be created with related objects"""
        equipment = Equipment.objects.create(
            door_no="EQ002",
            plate_no="PLATE002",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.equipment_model,
            location=self.location,
            sector=self.sector,
            annual_inspection_end_date=date.today() + timedelta(days=30),
            equipment_license_end_date=date.today() + timedelta(days=60)
        )
        
        self.assertEqual(equipment.door_no, "EQ002")
        self.assertEqual(equipment.manufacturer, self.manufacturer)
        self.assertEqual(equipment.model, self.equipment_model)
        self.assertEqual(equipment.status, 'operational')
    
    def test_equipment_status_choices(self):
        """Test equipment status field accepts valid choices"""
        for status, _ in EQUIPMENT_STATUS_CHOICES:
            equipment = Equipment.objects.create(
                door_no=f"STATUS_{status}",
                plate_no=f"PLATE_{status}",
                status=status
            )
            self.assertEqual(equipment.status, status)
    
    def test_equipment_string_representation(self):
        """Test equipment string representation"""
        equipment = Equipment.objects.create(
            door_no="STR001",
            plate_no="PLATE001",
            status='new'
        )
        # The __str__ method should return door_no - plate_no
        self.assertEqual(str(equipment), "STR001 - PLATE001")
    
    def test_equipment_inspection_expired_property(self):
        """Test equipment inspection expiry properties"""
        # Equipment with expired inspection
        expired_equipment = Equipment.objects.create(
            door_no="EXPIRED001",
            plate_no="PLATE001",
            status='new',
            annual_inspection_end_date=date.today() - timedelta(days=10)
        )
        self.assertTrue(expired_equipment.is_inspection_expired)
        self.assertEqual(expired_equipment.days_until_inspection_expiry, -10)  # Negative days for expired
        
        # Equipment with valid inspection
        valid_equipment = Equipment.objects.create(
            door_no="VALID001",
            plate_no="PLATE002",
            status='new',
            annual_inspection_end_date=date.today() + timedelta(days=30)
        )
        self.assertFalse(valid_equipment.is_inspection_expired)
        self.assertEqual(valid_equipment.days_until_inspection_expiry, 30)


class MaintenanceModelTest(TestCase):
    """Test cases for Maintenance model"""
    
    def setUp(self):
        """Set up test data"""
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
    
    def test_maintenance_creation_for_car(self):
        """Test maintenance record can be created for a car"""
        maintenance = Maintenance.objects.create(
            content_object=self.car,
            maintenance_date=date.today(),
            cost=500.00,
            description="Regular maintenance"
        )
        
        self.assertEqual(maintenance.content_object, self.car)
        self.assertEqual(maintenance.cost, 500.00)
        self.assertEqual(maintenance.maintenance_date, date.today())
    
    def test_maintenance_creation_for_equipment(self):
        """Test maintenance record can be created for equipment"""
        maintenance = Maintenance.objects.create(
            content_object=self.equipment,
            maintenance_date=date.today(),
            cost=200.00,
            description="Calibration"
        )
        
        self.assertEqual(maintenance.content_object, self.equipment)
        self.assertEqual(maintenance.cost, 200.00)
        self.assertEqual(maintenance.maintenance_date, date.today())
    
    def test_maintenance_string_representation(self):
        """Test maintenance string representation"""
        maintenance = Maintenance.objects.create(
            content_object=self.car,
            maintenance_date=date.today(),
            cost=500.00,
            description="Test maintenance"
        )
        # Should include the content object and date
        self.assertIn("MAINT001", str(maintenance))
        self.assertIn(str(date.today()), str(maintenance))


class CalibrationCertificateImageModelTest(TestCase):
    """Test cases for CalibrationCertificateImage model"""
    
    def setUp(self):
        """Set up test data"""
        self.equipment = Equipment.objects.create(
            door_no="CERT001",
            plate_no="PLATE001",
            status='new'
        )
    
    def test_calibration_certificate_creation(self):
        """Test calibration certificate can be created"""
        certificate = CalibrationCertificateImage.objects.create(
            equipment=self.equipment
        )
        
        self.assertEqual(certificate.equipment, self.equipment)
        self.assertTrue(certificate.pk is not None)
    
    def test_calibration_certificate_string_representation(self):
        """Test calibration certificate string representation"""
        certificate = CalibrationCertificateImage.objects.create(
            equipment=self.equipment
        )
        # Should include equipment door_no
        self.assertIn("CERT001", str(certificate))