import logging

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Mute expected 401/axes warnings - these are expected for test_login_invalid & test_profile_requires_auth, not errors
        logging.getLogger('django.request').setLevel(logging.ERROR)
        logging.getLogger('axes.handlers.database').setLevel(logging.ERROR)

    def test_signup(self):
        response = self.client.post(reverse('signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'customer@morgihome.com',
            'phone_number': '+255712345678',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123',
            'role': 'customer',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email='customer@morgihome.com').exists())

    def test_login_success(self):
        User.objects.create_user(email='seller@test.com', first_name='Seller', last_name='Ji', phone_number='+255700000001', password='TestPassword123')
        response = self.client.post(reverse('login'), {
            'email': 'seller@test.com',
            'password': 'TestPassword123',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid(self):
        response = self.client.post(reverse('login'), {
            'email': 'nobody@test.com',
            'password': 'wrong-password',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_profile_requires_auth(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 401)
