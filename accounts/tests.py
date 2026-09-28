import logging

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


class DashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            email='dashcustomer@test.com', first_name='Dash', last_name='Customer',
            phone_number='+255700000005', password='TestPassword123', role='customer',
            email_verified=True
        )
        self.bank = User.objects.create_user(
            email='dashbank@test.com', first_name='Dash', last_name='Bank',
            phone_number='+255700000006', password='TestPassword123', role='bank',
            email_verified=True, interest_rate=12.00
        )
        self.seller = User.objects.create_user(
            email='dashseller@test.com', first_name='Dash', last_name='Seller',
            phone_number='+255700000007', password='TestPassword123', role='seller',
            email_verified=True
        )

    def test_customer_dashboard_payment_stats(self):
        from properties.models import Property
        from mortgages.models import MortgageApplication, RepaymentSchedule
        prop = Property.objects.create(
            title='Test House', price=100000000, location='Dar es Salaam',
            status='available', seller=self.seller, area=500
        )
        mortgage = MortgageApplication.objects.create(
            customer=self.customer, property=prop, bank=self.bank,
            loan_amount=80000000, repayment_period=24,
            monthly_installment=4000000, status='disbursed'
        )
        # Create 24 repayment schedules; mark 5 as paid
        for i in range(1, 25):
            RepaymentSchedule.objects.create(
                mortgage=mortgage, installment_number=i,
                due_date='2026-01-01', amount_due=4000000,
                balance_remaining=80000000 - i * 3333333,
                status='paid' if i <= 5 else 'pending'
            )
        self.client.force_login(self.customer)
        response = self.client.get(reverse('customer_dashboard_apex'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['payments_paid'], 5)
        self.assertEqual(response.context['stats']['payments_total'], 24)
        self.assertEqual(response.context['stats']['monthly_payment'], 4000000)


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
        user = User.objects.create_user(email='seller@test.com', first_name='Seller', last_name='Ji', phone_number='+255700000001', password='TestPassword123')
        user.email_verified = True
        user.save(update_fields=['email_verified'])
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

    @override_settings(DEBUG=True, EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST_PASSWORD='invalid-password')
    def test_signup_email_failure_reported(self):
        # Simulate SMTP failure (bad credentials). The view should NOT pretend success.
        response = self.client.post(reverse('signup'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@morgihome.com',
            'phone_number': '+255712345679',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123',
            'role': 'customer',
        }, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.data)
        self.assertIn('debug_verification_url', response.data)
        user = User.objects.filter(email='jane@morgihome.com').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.email_verified)

    def test_resend_verification_invalidates_old_token(self):
        user = User.objects.create_user(
            email='resend@test.com', first_name='Resend', last_name='Test',
            phone_number='+255700000002', password='TestPassword123',
            email_verified=False,
            email_verification_token='OLD_TOKEN_123'
        )
        response = self.client.post(reverse('resend_verification'), {
            'email': 'resend@test.com',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertNotEqual(user.email_verification_token, 'OLD_TOKEN_123')
        self.assertTrue(user.email_verification_token)

    def test_resend_verification_cooldown(self):
        user = User.objects.create_user(
            email='cooldown@test.com', first_name='Cooldown', last_name='Test',
            phone_number='+255700000003', password='TestPassword123',
            email_verified=False,
            email_verification_token='TOKEN_1'
        )
        # First resend should succeed.
        r1 = self.client.post(reverse('resend_verification'), {
            'email': 'cooldown@test.com',
        }, format='json')
        self.assertEqual(r1.status_code, 200)
        # Immediate second resend should be rate limited.
        r2 = self.client.post(reverse('resend_verification'), {
            'email': 'cooldown@test.com',
        }, format='json')
        self.assertEqual(r2.status_code, 429)
        self.assertIn('retry_after', r2.data)

    def test_resend_verification_already_verified(self):
        user = User.objects.create_user(
            email='verified@test.com', first_name='Verified', last_name='Test',
            phone_number='+255700000004', password='TestPassword123',
            email_verified=True,
            email_verification_token=''
        )
        response = self.client.post(reverse('resend_verification'), {
            'email': 'verified@test.com',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('already verified', response.data['error'].lower())

    def test_resend_verification_page_reachable(self):
        response = self.client.get(reverse('resend_verification_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resend_verification.html')

    def test_profile_requires_auth(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 401)

    def tearDown(self):
        cache.clear()
