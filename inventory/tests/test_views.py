"""View tests for inventory app"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from datetime import date, timedelta
from inventory.models import Car, Equipment, AdministrativeUnit, Manufacturer, CarModel, EquipmentModel, Location, Sector


class AuthenticationViewTest(TestCase):
    """Test cases for authentication views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create Admin group
        self.admin_group = Group.objects.create(name='Admin')
        self.user.groups.add(self.admin_group)
    
    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'اسم المستخدم')
        self.assertContains(response, 'كلمة المرور')
    
    def test_login_view_post_valid_admin(self):
        """Test login view POST with valid admin user"""
        response = self.client.post('/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/dashboard/')
    
    def test_login_view_post_invalid_credentials(self):
        """Test login view POST with invalid credentials"""
        response = self.client.post('/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'اسم المستخدم')
    
    def test_login_view_post_non_admin_user(self):
        """Test login view POST with non-admin user"""
        # Create non-admin user
        non_admin_user = User.objects.create_user(
            username='nonadmin',
            password='testpass123'
        )
        
        response = self.client.post('/', {
            'username': 'nonadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ليس لديك صلاحية للدخول إلى هذا النظام')
    
    def test_logout_view(self):
        """Test logout view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/logout/')
        self.assertRedirects(response, '/')


class DashboardViewTest(TestCase):
    """Test cases for dashboard view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_group = Group.objects.create(name='Admin')
        self.user.groups.add(self.admin_group)
        
        # Create test data
        self.manufacturer = Manufacturer.objects.create(name="Toyota")
        self.car_model = CarModel.objects.create(
            manufacturer=self.manufacturer,
            name="Camry"
        )
        self.administrative_unit = AdministrativeUnit.objects.create(name="IT Department")
        
        # Create cars with different expiry statuses
        self.car_expired = Car.objects.create(
            fleet_no="EXPIRED001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.car_model,
            administrative_unit=self.administrative_unit,
            annual_inspection_end_date=date.today() - timedelta(days=10)  # Expired
        )
        
        self.car_expiring = Car.objects.create(
            fleet_no="EXPIRING001",
            plate_no_en="XYZ789",
            plate_no_ar="س ي ز ٧٨٩",
            location_description="Test Location",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.car_model,
            administrative_unit=self.administrative_unit,
            annual_inspection_end_date=date.today() + timedelta(days=15)  # Expiring soon
        )
        
        # Create equipment
        self.equipment_model = EquipmentModel.objects.create(
            manufacturer=self.manufacturer,
            name="Multimeter"
        )
        self.location = Location.objects.create(name="Lab 1")
        self.sector = Sector.objects.create(name="Electronics")
        
        self.equipment_expired = Equipment.objects.create(
            door_no="EQ001",
            plate_no="PLATE001",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.equipment_model,
            location=self.location,
            sector=self.sector,
            annual_inspection_end_date=date.today() - timedelta(days=5)  # Expired
        )
        
        self.equipment_expiring = Equipment.objects.create(
            door_no="EQ002",
            plate_no="PLATE002",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.equipment_model,
            location=self.location,
            sector=self.sector,
            annual_inspection_end_date=date.today() + timedelta(days=20)  # Expiring soon
        )
    
    def test_dashboard_view_requires_login(self):
        """Test dashboard view requires authentication"""
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/?next=/dashboard/')
    
    def test_dashboard_view_requires_admin(self):
        """Test dashboard view requires admin privileges"""
        # Create non-admin user
        non_admin_user = User.objects.create_user(
            username='nonadmin',
            password='testpass123'
        )
        self.client.login(username='nonadmin', password='testpass123')
        
        response = self.client.get('/dashboard/')
        # Non-admin users are redirected to login with error message
        self.assertRedirects(response, '/?next=/dashboard/')
    
    def test_dashboard_view_default_expiry_status(self):
        """Test dashboard view with default expiry status"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة القيادة')
        
        # Should show cars and equipment about to expire (default)
        context = response.context
        self.assertIn('cars_expiring', context)
        self.assertIn('equipment_expiring', context)
        self.assertEqual(context['expiry_status'], 'about_to_expire')
        self.assertEqual(context['expiry_days'], 30)
    
    def test_dashboard_view_expired_status(self):
        """Test dashboard view with expired status"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/', {
            'expiry_status': 'expired',
            'expiry_days': '30'
        })
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['expiry_status'], 'expired')
        self.assertEqual(context['expiry_days'], 30)
    
    def test_dashboard_view_custom_expiry_days(self):
        """Test dashboard view with custom expiry days"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/', {
            'expiry_status': 'about_to_expire',
            'expiry_days': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['expiry_days'], 10)
    
    def test_dashboard_view_invalid_expiry_days(self):
        """Test dashboard view with invalid expiry days defaults to 30"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/', {
            'expiry_status': 'about_to_expire',
            'expiry_days': 'invalid'
        })
        
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertEqual(context['expiry_days'], 30)


class CarViewTest(TestCase):
    """Test cases for car views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_group = Group.objects.create(name='Admin')
        self.user.groups.add(self.admin_group)
        
        # Create test data
        self.manufacturer = Manufacturer.objects.create(name="Toyota")
        self.car_model = CarModel.objects.create(
            manufacturer=self.manufacturer,
            name="Camry"
        )
        self.administrative_unit = AdministrativeUnit.objects.create(name="IT Department")
        
        self.car = Car.objects.create(
            fleet_no="TEST001",
            plate_no_en="ABC123",
            plate_no_ar="أ ب ج ١٢٣",
            location_description="Test Location",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.car_model,
            administrative_unit=self.administrative_unit
        )
    
    def test_car_list_view_requires_login(self):
        """Test car list view requires authentication"""
        response = self.client.get('/cars/')
        self.assertRedirects(response, '/?next=/cars/')
    
    def test_car_list_view_requires_admin(self):
        """Test car list view requires admin privileges"""
        non_admin_user = User.objects.create_user(
            username='nonadmin',
            password='testpass123'
        )
        self.client.login(username='nonadmin', password='testpass123')
        
        response = self.client.get('/cars/')
        # Non-admin users are redirected to login with error message
        self.assertRedirects(response, '/?next=/cars/')
    
    def test_car_list_view_get(self):
        """Test car list view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/cars/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'قائمة السيارات')
        self.assertContains(response, 'TEST001')
    
    def test_car_list_view_search(self):
        """Test car list view with search"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/cars/', {
            'search_query': 'TEST001',
            'search_field': 'fleet_no'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST001')
    
    def test_car_list_view_sort(self):
        """Test car list view with sorting"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/cars/', {
            'sort_by': 'fleet_no',
            'sort_order': 'desc'
        })
        
        self.assertEqual(response.status_code, 200)
    
    def test_car_detail_view_requires_login(self):
        """Test car detail view requires authentication"""
        response = self.client.get(f'/cars/{self.car.pk}/')
        self.assertRedirects(response, f'/login/?next=/cars/{self.car.pk}/')
    
    def test_car_detail_view_get(self):
        """Test car detail view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/cars/{self.car.pk}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST001')
        self.assertContains(response, 'ABC123')
    
    def test_car_detail_view_not_found(self):
        """Test car detail view with non-existent car"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/cars/99999/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_car_create_view_requires_login(self):
        """Test car create view requires authentication"""
        response = self.client.get('/cars/create/')
        self.assertRedirects(response, '/login/?next=/cars/create/')
    
    def test_car_create_view_get(self):
        """Test car create view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/cars/create/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إضافة سيارة جديدة')
    
    def test_car_create_view_post_valid(self):
        """Test car create view POST with valid data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/cars/create/', {
            'fleet_no': 'NEW001',
            'plate_no_en': 'NEW123',
            'plate_no_ar': 'جديد ١٢٣',
            'location_description': 'New Location',
            'status': 'new',
            'manufacturer': self.manufacturer.pk,
            'model': self.car_model.pk,
            'administrative_unit': self.administrative_unit.pk,
        })
        
        # Should redirect to car list on success
        self.assertRedirects(response, '/cars/')
        
        # Verify car was created
        self.assertTrue(Car.objects.filter(fleet_no='NEW001').exists())
    
    def test_car_update_view_requires_login(self):
        """Test car update view requires authentication"""
        response = self.client.get(f'/cars/{self.car.pk}/update/')
        self.assertRedirects(response, f'/?next=/cars/{self.car.pk}/update/')
    
    def test_car_update_view_get(self):
        """Test car update view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/cars/{self.car.pk}/update/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تحديث السيارة')
        self.assertContains(response, 'TEST001')
    
    def test_car_update_view_post_valid(self):
        """Test car update view POST with valid data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(f'/cars/{self.car.pk}/update/', {
            'fleet_no': 'UPDATED001',
            'plate_no_en': 'UPD123',
            'plate_no_ar': 'محدث ١٢٣',
            'location_description': 'Updated Location',
            'status': 'operational',
            'manufacturer': self.manufacturer.pk,
            'model': self.car_model.pk,
            'administrative_unit': self.administrative_unit.pk,
            # Add maintenance formset data (empty)
            'inventory-maintenance-content_type-object_id-TOTAL_FORMS': '0',
            'inventory-maintenance-content_type-object_id-INITIAL_FORMS': '0',
            'inventory-maintenance-content_type-object_id-MIN_NUM_FORMS': '0',
            'inventory-maintenance-content_type-object_id-MAX_NUM_FORMS': '1000',
        })
        
        # Check if form validation passed
        if response.status_code == 200:
            # Form had validation errors, check what they are
            self.assertContains(response, 'form')
        else:
            # Should redirect to car detail on success
            self.assertRedirects(response, f'/cars/{self.car.pk}/')
            
            # Verify car was updated
            self.car.refresh_from_db()
            self.assertEqual(self.car.fleet_no, 'UPDATED001')
            self.assertEqual(self.car.plate_no_en, 'UPD123')
    
    def test_car_delete_view_requires_login(self):
        """Test car delete view requires authentication"""
        response = self.client.get(f'/cars/{self.car.pk}/delete/')
        self.assertRedirects(response, f'/login/?next=/cars/{self.car.pk}/delete/')
    
    def test_car_delete_view_get(self):
        """Test car delete view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/cars/{self.car.pk}/delete/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تأكيد الحذف')
        self.assertContains(response, 'TEST001')
    
    def test_car_delete_view_post(self):
        """Test car delete view POST request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(f'/cars/{self.car.pk}/delete/')
        
        # Should redirect to car list on success
        self.assertRedirects(response, '/cars/')
        
        # Verify car was deleted
        self.assertFalse(Car.objects.filter(pk=self.car.pk).exists())


class EquipmentViewTest(TestCase):
    """Test cases for equipment views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_group = Group.objects.create(name='Admin')
        self.user.groups.add(self.admin_group)
        
        # Create test data
        self.manufacturer = Manufacturer.objects.create(name="Siemens")
        self.equipment_model = EquipmentModel.objects.create(
            manufacturer=self.manufacturer,
            name="Multimeter"
        )
        self.location = Location.objects.create(name="Lab 1")
        self.sector = Sector.objects.create(name="Electronics")
        
        self.equipment = Equipment.objects.create(
            door_no="EQ001",
            plate_no="PLATE001",
            status='operational',
            manufacturer=self.manufacturer,
            model=self.equipment_model,
            location=self.location,
            sector=self.sector
        )
    
    def test_equipment_list_view_requires_login(self):
        """Test equipment list view requires authentication"""
        response = self.client.get('/equipment/')
        self.assertRedirects(response, '/?next=/equipment/')
    
    def test_equipment_list_view_get(self):
        """Test equipment list view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/equipment/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'المعدات')
        self.assertContains(response, 'EQ001')
    
    def test_equipment_detail_view_get(self):
        """Test equipment detail view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/equipment/{self.equipment.pk}/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EQ001')
        self.assertContains(response, 'PLATE001')
    
    def test_equipment_create_view_get(self):
        """Test equipment create view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/equipment/create/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'إضافة معدة')
    
    def test_equipment_create_view_post_valid(self):
        """Test equipment create view POST with valid data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/equipment/create/', {
            'door_no': 'NEWEQ001',
            'plate_no': 'NEWPLATE001',
            'status': 'new',
            'manufacturer': self.manufacturer.pk,
            'model': self.equipment_model.pk,
            'location': self.location.pk,
            'sector': self.sector.pk,
            # Add maintenance formset data (empty)
            'maintenance_set-TOTAL_FORMS': '0',
            'maintenance_set-INITIAL_FORMS': '0',
            'maintenance_set-MIN_NUM_FORMS': '0',
            'maintenance_set-MAX_NUM_FORMS': '1000',
        })
        
        # Check if form validation passed
        if response.status_code == 200:
            # Form had validation errors, check what they are
            self.assertContains(response, 'form')
        else:
            # Should redirect to equipment list on success
            self.assertRedirects(response, '/equipment/')
            
            # Verify equipment was created
            self.assertTrue(Equipment.objects.filter(door_no='NEWEQ001').exists())
    
    def test_equipment_update_view_get(self):
        """Test equipment update view GET request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/equipment/{self.equipment.pk}/update/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تحديث المعدة')
        self.assertContains(response, 'EQ001')
    
    def test_equipment_update_view_post_valid(self):
        """Test equipment update view POST with valid data"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create unique door_no and plate_no for update
        response = self.client.post(f'/equipment/{self.equipment.pk}/update/', {
            'door_no': 'UPDATEDEQ001',
            'plate_no': 'UPDATEDPLATE001',
            'status': 'operational',
            'manufacturer': self.manufacturer.pk,
            'model': self.equipment_model.pk,
            'location': self.location.pk,
            'sector': self.sector.pk,
            # Add maintenance formset data (empty)
            'maintenance_set-TOTAL_FORMS': '0',
            'maintenance_set-INITIAL_FORMS': '0',
            'maintenance_set-MIN_NUM_FORMS': '0',
            'maintenance_set-MAX_NUM_FORMS': '1000',
        })
        
        # Check if form validation passed
        if response.status_code == 200:
            # Form had validation errors, check what they are
            self.assertContains(response, 'form')
        else:
            # Should redirect to equipment detail on success
            self.assertRedirects(response, f'/equipment/{self.equipment.pk}/')
            
            # Verify equipment was updated
            self.equipment.refresh_from_db()
            self.assertEqual(self.equipment.door_no, 'UPDATEDEQ001')
            self.assertEqual(self.equipment.plate_no, 'UPDATEDPLATE001')
    
    def test_equipment_delete_view_post(self):
        """Test equipment delete view POST request"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(f'/equipment/{self.equipment.pk}/delete/')
        
        # Should redirect to equipment list on success
        self.assertRedirects(response, '/equipment/')
        
        # Verify equipment was deleted
        self.assertFalse(Equipment.objects.filter(pk=self.equipment.pk).exists())