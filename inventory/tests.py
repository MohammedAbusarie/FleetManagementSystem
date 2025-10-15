from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Equipment, CalibrationCertificateImage, Manufacturer, EquipmentModel, Location, Sector


class EquipmentCertificateDeletionTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user and admin group
        self.user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            email='admin@test.com'
        )
        self.admin_group = Group.objects.create(name='Admin')
        self.user.groups.add(self.admin_group)
        
        # Create required related objects
        self.manufacturer = Manufacturer.objects.create(name='Test Manufacturer')
        self.model = EquipmentModel.objects.create(name='Test Model', manufacturer=self.manufacturer)
        self.location = Location.objects.create(name='Test Location')
        self.sector = Sector.objects.create(name='Test Sector')
        
        # Create test equipment
        self.equipment = Equipment.objects.create(
            door_no='TEST001',
            plate_no='PLATE001',
            manufacture_year=2020,
            manufacturer=self.manufacturer,
            model=self.model,
            location=self.location,
            sector=self.sector,
            status='operational'
        )
        
        # Create test certificate images
        self.cert1 = CalibrationCertificateImage.objects.create(
            equipment=self.equipment,
            image=SimpleUploadedFile(
                "cert1.jpg",
                b"fake image content",
                content_type="image/jpeg"
            )
        )
        self.cert2 = CalibrationCertificateImage.objects.create(
            equipment=self.equipment,
            image=SimpleUploadedFile(
                "cert2.jpg",
                b"fake image content",
                content_type="image/jpeg"
            )
        )
        
        self.client = Client()
        self.client.login(username='testadmin', password='testpass123')
    
    def test_certificate_deletion_functionality(self):
        """Test that certificates can be marked for deletion during equipment update"""
        # Get the equipment update page
        response = self.client.get(reverse('equipment_update', kwargs={'pk': self.equipment.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Verify certificates are displayed
        self.assertContains(response, 'شهادات المعايرة الموجودة')
        self.assertContains(response, 'حذف الشهادة')
        self.assertContains(response, f'data-cert-id="{self.cert1.id}"')
        self.assertContains(response, f'data-cert-id="{self.cert2.id}"')
        
        # Test certificate deletion via POST
        update_data = {
            'door_no': 'TEST001',
            'plate_no': 'PLATE001',
            'manufacture_year': 2020,
            'manufacturer': self.manufacturer.id,
            'model': self.model.id,
            'location': self.location.id,
            'sector': self.sector.id,
            'status': 'operational',
            'certificates_to_delete': f'{self.cert1.id}',  # Mark cert1 for deletion
            'maintenance_set-TOTAL_FORMS': '0',
            'maintenance_set-INITIAL_FORMS': '0',
            'maintenance_set-MIN_NUM_FORMS': '0',
            'maintenance_set-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(
            reverse('equipment_update', kwargs={'pk': self.equipment.pk}),
            data=update_data
        )
        
        # Should redirect to equipment list
        self.assertEqual(response.status_code, 302)
        
        # Verify cert1 was deleted but cert2 remains
        self.assertFalse(CalibrationCertificateImage.objects.filter(id=self.cert1.id).exists())
        self.assertTrue(CalibrationCertificateImage.objects.filter(id=self.cert2.id).exists())
    
    def test_multiple_certificate_deletion(self):
        """Test deleting multiple certificates at once"""
        update_data = {
            'door_no': 'TEST001',
            'plate_no': 'PLATE001',
            'manufacture_year': 2020,
            'manufacturer': self.manufacturer.id,
            'model': self.model.id,
            'location': self.location.id,
            'sector': self.sector.id,
            'status': 'operational',
            'certificates_to_delete': f'{self.cert1.id},{self.cert2.id}',  # Mark both for deletion
            'maintenance_set-TOTAL_FORMS': '0',
            'maintenance_set-INITIAL_FORMS': '0',
            'maintenance_set-MIN_NUM_FORMS': '0',
            'maintenance_set-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(
            reverse('equipment_update', kwargs={'pk': self.equipment.pk}),
            data=update_data
        )
        
        # Should redirect to equipment list
        self.assertEqual(response.status_code, 302)
        
        # Verify both certificates were deleted
        self.assertFalse(CalibrationCertificateImage.objects.filter(id=self.cert1.id).exists())
        self.assertFalse(CalibrationCertificateImage.objects.filter(id=self.cert2.id).exists())
    
    def test_certificate_appending_with_deletion(self):
        """Test that new certificates are appended while existing ones can be deleted"""
        # Create a new certificate file
        new_cert_file = SimpleUploadedFile(
            "new_cert.jpg",
            b"new fake image content",
            content_type="image/jpeg"
        )
        
        update_data = {
            'door_no': 'TEST001',
            'plate_no': 'PLATE001',
            'manufacture_year': 2020,
            'manufacturer': self.manufacturer.id,
            'model': self.model.id,
            'location': self.location.id,
            'sector': self.sector.id,
            'status': 'operational',
            'certificates_to_delete': f'{self.cert1.id}',  # Delete cert1
            'calibration_certificates': [new_cert_file],  # Add new certificate
            'maintenance_set-TOTAL_FORMS': '0',
            'maintenance_set-INITIAL_FORMS': '0',
            'maintenance_set-MIN_NUM_FORMS': '0',
            'maintenance_set-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(
            reverse('equipment_update', kwargs={'pk': self.equipment.pk}),
            data=update_data
        )
        
        # Should redirect to equipment list
        self.assertEqual(response.status_code, 302)
        
        # Verify cert1 was deleted, cert2 remains, and new cert was added
        self.assertFalse(CalibrationCertificateImage.objects.filter(id=self.cert1.id).exists())
        self.assertTrue(CalibrationCertificateImage.objects.filter(id=self.cert2.id).exists())
        
        # Check that new certificate was added
        new_certs = CalibrationCertificateImage.objects.filter(equipment=self.equipment)
        self.assertEqual(new_certs.count(), 2)  # cert2 + new cert
        self.assertTrue(any('new_cert.jpg' in str(cert.image) for cert in new_certs))
