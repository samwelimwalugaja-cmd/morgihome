import secrets
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class User(AbstractUser):
    # Remove username completely - use email as identifier
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    objects = CustomUserManager()

    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('bank', 'Bank'),
        ('realestate', 'Real Estate Company'),
    )
    email = models.EmailField(unique=True, verbose_name='email address')
    first_name = models.CharField(max_length=50, verbose_name='first name')
    last_name = models.CharField(max_length=50, verbose_name='last name')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    notify_email = models.BooleanField(default=True, help_text="Pokea updates za applications kwa email")
    notifications_seen_at = models.DateTimeField(null=True, blank=True, help_text="Mteja alisoma notifications lini mwisho (badge ya kengele)")

    # Bank specific
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Yearly interest rate in PERCENT (e.g. 12.50 means 12.5% p.a. - this is NOT the fee)")
    processing_fee = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="One-time processing fee as TZS AMOUNT (e.g. 500000 - fill this so applicants see it instead of —)")
    min_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Minimum loan amount TZS")
    max_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Maximum loan amount TZS")
    bank_requirements = models.TextField(blank=True, null=True, help_text="Mahitaji ya bank (comma separated)")

    # === REMAINING for Bank/RealEstate ===
    bank_doc_status_choices = (('not_submitted','Not Submitted'),('pending','Pending'),('verified','Verified'),('rejected','Rejected'))
    business_license = models.FileField(upload_to='bank_docs/business_license/', blank=True, null=True)
    business_license_status = models.CharField(max_length=20, default='not_submitted', choices=bank_doc_status_choices)
    business_license_verified = models.BooleanField(default=False)
    business_license_submitted_at = models.DateTimeField(blank=True, null=True)
    business_license_verified_at = models.DateTimeField(blank=True, null=True)
    business_license_rejection_reason = models.TextField(blank=True, null=True)

    tax_clearance = models.FileField(upload_to='bank_docs/tax_clearance/', blank=True, null=True)
    tax_clearance_status = models.CharField(max_length=20, default='not_submitted', choices=bank_doc_status_choices)
    tax_clearance_verified = models.BooleanField(default=False)
    tax_clearance_submitted_at = models.DateTimeField(blank=True, null=True)
    tax_clearance_verified_at = models.DateTimeField(blank=True, null=True)
    tax_clearance_rejection_reason = models.TextField(blank=True, null=True)

    company_registration = models.FileField(upload_to='bank_docs/company_registration/', blank=True, null=True)
    company_registration_status = models.CharField(max_length=20, default='not_submitted', choices=bank_doc_status_choices)
    company_registration_verified = models.BooleanField(default=False)
    company_registration_submitted_at = models.DateTimeField(blank=True, null=True)
    company_registration_verified_at = models.DateTimeField(blank=True, null=True)
    company_registration_rejection_reason = models.TextField(blank=True, null=True)

    # === REMOVED: Email/Phone/NIN Verification ===
    # email_verified, email_verification_token, email_verification_sent_at, email_verified_at -> REMOVED
    # phone_verified, phone_otp, phone_otp_created_at, phone_otp_attempts, phone_verified_at -> REMOVED
    # identity_verified, identity_document, identity_document_type, identity_submitted_at, identity_verified_at, identity_rejection_reason, identity_status -> REMOVED
    # nin_number, nin_verified, nin_status, nin_submitted_at, nin_verified_at, nin_rejection_reason -> REMOVED

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def get_full_name(self):
        if self.role == 'bank':
            return self.first_name  # Bank name
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def is_fully_verified(self):
        """Each role has its own requirements - Customers/Sellers don't need verification"""
        if self.role == 'customer':
            return True
        elif self.role == 'seller':
            return True
        elif self.role == 'bank':
            return all([
                self.business_license_verified,
                self.tax_clearance_verified,
                self.company_registration_verified
            ])
        elif self.role == 'realestate':
            return all([
                self.business_license_verified,
                self.company_registration_verified
            ])
        return False

    def update_verification_status(self):
        # Now is_verified = is_fully_verified for all roles
        self.is_verified = self.is_fully_verified()
        self.save(update_fields=['is_verified'])

    @property
    def verification_level(self):
        if self.is_fully_verified():
            return 'fully_verified'
        # Bank/RealEstate: if one doc verified -> partially
        if self.role in ['bank','realestate']:
            if self.business_license_verified or self.tax_clearance_verified or self.company_registration_verified:
                return 'partially_verified'
        return 'not_verified'

    @property
    def verification_level_display(self):
        mapping={'not_verified':'Not Verified','partially_verified':'Partially Verified','fully_verified':'Fully Verified'}
        return mapping.get(self.verification_level, 'Not Verified')

    @property
    def initials(self):
        name = (self.first_name or self.email.split('@')[0] or 'M').strip()
        if not name:
            return 'M'
        return name[0].upper()

    @property
    def avatar_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return None
