import secrets
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class User(AbstractUser):
    # Pilot bank - mfumo unauzwa bank moja moja. Kwa sasa pilot ni NCBA pekee.
    # Customer na watumiaji wengine wanaona/omba kupitia bank hii tu.
    # Website ya mbele (index.html #banks) inabaki na bank zote kwa matangazo.
    PILOT_BANK_SLUG = 'ncba'
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
    notify_email = models.BooleanField(default=True, help_text="Receive application updates via email")
    notifications_seen_at = models.DateTimeField(null=True, blank=True, help_text="When the user last read notifications (bell badge)")

    # Email verification (required for customer/seller self-registration)
    email_verified = models.BooleanField(default=False, help_text="Email address has been verified via verification link")
    email_verification_token = models.CharField(max_length=255, blank=True, default='', help_text="One-time token sent by email")
    email_verification_sent_at = models.DateTimeField(null=True, blank=True, help_text="When the verification email was last sent")
    email_verified_at = models.DateTimeField(null=True, blank=True, help_text="When the email was verified")

    # Social signup role selection pending
    role_selection_pending = models.BooleanField(default=False, help_text="New social user still needs to select customer/realestate role")

    # Bank specific
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Yearly interest rate in PERCENT (e.g. 12.50 means 12.5% p.a. - this is NOT the fee)")
    processing_fee = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Processing fee in PERCENT (e.g. 1.00 means 1% - applicants see 1%)")
    min_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Minimum loan amount TZS")
    max_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Maximum loan amount TZS")
    max_repayment_period = models.IntegerField(null=True, blank=True, help_text="Maximum repayment period in MONTHS (e.g. 180 for 15 years - NMB max 180)")
    bank_requirements = models.TextField(blank=True, null=True, help_text="Bank requirements (comma separated)")

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

    def get_account_deletion_blockers(self):
        """Return a list of reasons why this user cannot delete their account.
        Empty list means deletion is allowed."""
        from django.db.models import Q
        blockers = []

        # 1) Verification requirements per role
        if self.role == 'customer':
            if not self.email_verified:
                blockers.append("Email address is not verified. Please verify your email first.")
        elif self.role in ['bank', 'realestate']:
            if not self.is_fully_verified():
                blockers.append("Business documents are not fully verified. Complete verification first.")

        # 2) Active / pending loans or mortgage applications
        try:
            from mortgages.models import MortgageApplication
            active_loans = MortgageApplication.objects.filter(
                customer=self,
                status__in=['pending', 'document_verification', 'crb_check', 'valuation',
                            'credit_assessment', 'approved', 'disbursed']
            )
            if active_loans.exists():
                statuses = set(active_loans.values_list('status', flat=True))
                if 'approved' in statuses or 'disbursed' in statuses:
                    blockers.append("You have an active mortgage loan. Close or complete it first.")
                else:
                    blockers.append("You have a mortgage application in progress or pending. Cancel or complete it first.")
        except Exception:
            pass

        # 3) Active hold by a bank
        try:
            from mortgages.models import CustomerHold
            active_holds = CustomerHold.objects.filter(customer=self, is_active=True).select_related('bank')
            if active_holds.exists():
                hold = active_holds.first()
                bank_name = hold.bank.get_full_name() if hold.bank else 'a partner bank'
                reason = f" Reason: {hold.reason}" if hold.reason else ''
                blockers.append(f"Your account is on hold by {bank_name}.{reason} Contact the bank to release the hold before deleting your account.")
        except Exception:
            pass

        return blockers

    def can_delete_account(self):
        return len(self.get_account_deletion_blockers()) == 0

    @classmethod
    def get_pilot_bank(cls):
        """Rudisha bank ya pilot (NCBA). None kama haipo."""
        from django.db.models import Q
        pilot = cls.objects.filter(
            role='bank', is_active=True
        ).filter(
            Q(first_name__icontains=cls.PILOT_BANK_SLUG)
            | Q(last_name__icontains=cls.PILOT_BANK_SLUG)
            | Q(email__icontains=cls.PILOT_BANK_SLUG)
        ).order_by('id').first()
        return pilot

    @classmethod
    def get_pilot_banks_qs(cls):
        """Queryset ya bank za kuonyesha kwa customer/users - pilot pekee (NCBA)."""
        from django.db.models import Q
        return cls.objects.filter(role='bank', is_active=True).filter(
            Q(first_name__icontains=cls.PILOT_BANK_SLUG)
            | Q(last_name__icontains=cls.PILOT_BANK_SLUG)
            | Q(email__icontains=cls.PILOT_BANK_SLUG)
        ).order_by('id')
