from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Vendor, VendorService
from django.core.files.uploadedfile import SimpleUploadedFile

class VendorTestCase(APITestCase):
    def setUp(self):
        self.registration_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'company_name': 'Test Company',
            'description': 'Test description',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'country': 'Test Country',
            'zip_code': '12345',
            'phone': '+1234567890',
        }
        
    def test_vendor_registration(self):
        url = reverse('vendor-register')
        response = self.client.post(url, self.registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('vendor_id', response.data)
        
        # Verify vendor was created
        vendor = Vendor.objects.get(email=self.registration_data['email'])
        self.assertEqual(vendor.company_name, self.registration_data['company_name'])
        self.assertEqual(vendor.status, 'pending')
        
    def test_vendor_login(self):
        # First register
        register_url = reverse('vendor-register')
        self.client.post(register_url, self.registration_data, format='json')
        
        # Then login
        login_url = reverse('vendor-login')
        login_data = {
            'email': self.registration_data['email'],
            'password': self.registration_data['password']
        }
        
        response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('vendor', response.data)
        
    def test_vendor_profile_access(self):
        # Register and login first
        register_url = reverse('vendor-register')
        self.client.post(register_url, self.registration_data, format='json')
        
        login_url = reverse('vendor-login')
        login_data = {
            'email': self.registration_data['email'],
            'password': self.registration_data['password']
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['token']
        
        # Access profile with token
        profile_url = reverse('vendor-profile')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.registration_data['email'])
        
class VendorServiceTestCase(APITestCase):
    def setUp(self):
        # Create a vendor
        self.vendor = Vendor.objects.create_user(
            email='vendor@example.com',
            password='testpass123',
            company_name='Test Vendor'
        )
        self.vendor.status = 'approved'
        self.vendor.save()
        
        # Get auth token
        login_url = reverse('vendor-login')
        login_data = {
            'email': 'vendor@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(login_url, login_data, format='json')
        self.token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Create service category
        self.category = VendorServiceCategory.objects.create(
            name='Web Development',
            description='Web development services'
        )
        
    def test_create_service(self):
        url = reverse('vendor-services')
        service_data = {
            'category': self.category.id,
            'name': 'Basic Website',
            'description': 'Basic website development',
            'base_price': '500.00',
        }
        
        response = self.client.post(url, service_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], service_data['name'])
        
        # Verify service was created
        service = VendorService.objects.get(name=service_data['name'])
        self.assertEqual(service.vendor, self.vendor)
        self.assertEqual(str(service.base_price), service_data['base_price'])