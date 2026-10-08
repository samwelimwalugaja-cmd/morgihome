import builtins

from django.conf import settings
from django.db import models

from properties.models import Property


REVIEW_STAGES = (
    ('received', 'Received by Bank'),
    ('document_verification', 'Document Verification'),
    ('crb_check', 'CRB / Credit Reference Check'),
    ('valuation', 'Property Valuation'),
    ('credit_assessment', 'Credit Assessment'),
    ('approval_decision', 'Approval Decision'),
    ('disbursed', 'Disbursed'),
)

COUNTRY_CHOICES = (
    ('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AD', 'Andorra'),
    ('AO', 'Angola'), ('AG', 'Antigua and Barbuda'), ('AR', 'Argentina'), ('AM', 'Armenia'),
    ('AU', 'Australia'), ('AT', 'Austria'), ('AZ', 'Azerbaijan'), ('BS', 'Bahamas'),
    ('BH', 'Bahrain'), ('BD', 'Bangladesh'), ('BB', 'Barbados'), ('BY', 'Belarus'),
    ('BE', 'Belgium'), ('BZ', 'Belize'), ('BJ', 'Benin'), ('BT', 'Bhutan'),
    ('BO', 'Bolivia'), ('BA', 'Bosnia and Herzegovina'), ('BW', 'Botswana'), ('BR', 'Brazil'),
    ('BN', 'Brunei'), ('BG', 'Bulgaria'), ('BF', 'Burkina Faso'), ('BI', 'Burundi'),
    ('CV', 'Cabo Verde'), ('KH', 'Cambodia'), ('CM', 'Cameroon'), ('CA', 'Canada'),
    ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'),
    ('CO', 'Colombia'), ('KM', 'Comoros'), ('CG', 'Congo'), ('CD', 'Congo, Democratic Republic'),
    ('CR', 'Costa Rica'), ('HR', 'Croatia'), ('CU', 'Cuba'), ('CY', 'Cyprus'),
    ('CZ', 'Czech Republic'), ('DK', 'Denmark'), ('DJ', 'Djibouti'), ('DM', 'Dominica'),
    ('DO', 'Dominican Republic'), ('EC', 'Ecuador'), ('EG', 'Egypt'), ('SV', 'El Salvador'),
    ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('EE', 'Estonia'), ('SZ', 'Eswatini'),
    ('ET', 'Ethiopia'), ('FJ', 'Fiji'), ('FI', 'Finland'), ('FR', 'France'),
    ('GA', 'Gabon'), ('GM', 'Gambia'), ('GE', 'Georgia'), ('DE', 'Germany'),
    ('GH', 'Ghana'), ('GR', 'Greece'), ('GD', 'Grenada'), ('GT', 'Guatemala'),
    ('GN', 'Guinea'), ('GW', 'Guinea-Bissau'), ('GY', 'Guyana'), ('HT', 'Haiti'),
    ('HN', 'Honduras'), ('HU', 'Hungary'), ('IS', 'Iceland'), ('IN', 'India'),
    ('ID', 'Indonesia'), ('IR', 'Iran'), ('IQ', 'Iraq'), ('IE', 'Ireland'),
    ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'), ('JP', 'Japan'),
    ('JO', 'Jordan'), ('KZ', 'Kazakhstan'), ('KE', 'Kenya'), ('KI', 'Kiribati'),
    ('KP', 'Korea, North'), ('KR', 'Korea, South'), ('KW', 'Kuwait'), ('KG', 'Kyrgyzstan'),
    ('LA', 'Laos'), ('LV', 'Latvia'), ('LB', 'Lebanon'), ('LS', 'Lesotho'),
    ('LR', 'Liberia'), ('LY', 'Libya'), ('LI', 'Liechtenstein'), ('LT', 'Lithuania'),
    ('LU', 'Luxembourg'), ('MG', 'Madagascar'), ('MW', 'Malawi'), ('MY', 'Malaysia'),
    ('MV', 'Maldives'), ('ML', 'Mali'), ('MT', 'Malta'), ('MH', 'Marshall Islands'),
    ('MR', 'Mauritania'), ('MU', 'Mauritius'), ('MX', 'Mexico'), ('FM', 'Micronesia'),
    ('MD', 'Moldova'), ('MC', 'Monaco'), ('MN', 'Mongolia'), ('ME', 'Montenegro'),
    ('MA', 'Morocco'), ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'),
    ('NR', 'Nauru'), ('NP', 'Nepal'), ('NL', 'Netherlands'), ('NZ', 'New Zealand'),
    ('NI', 'Nicaragua'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('MK', 'North Macedonia'),
    ('NO', 'Norway'), ('OM', 'Oman'), ('PK', 'Pakistan'), ('PW', 'Palau'),
    ('PA', 'Panama'), ('PG', 'Papua New Guinea'), ('PY', 'Paraguay'), ('PE', 'Peru'),
    ('PH', 'Philippines'), ('PL', 'Poland'), ('PT', 'Portugal'), ('QA', 'Qatar'),
    ('RO', 'Romania'), ('RU', 'Russia'), ('RW', 'Rwanda'), ('KN', 'Saint Kitts and Nevis'),
    ('LC', 'Saint Lucia'), ('VC', 'Saint Vincent and the Grenadines'), ('WS', 'Samoa'),
    ('SM', 'San Marino'), ('ST', 'Sao Tome and Principe'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'),
    ('RS', 'Serbia'), ('SC', 'Seychelles'), ('SL', 'Sierra Leone'), ('SG', 'Singapore'),
    ('SK', 'Slovakia'), ('SI', 'Slovenia'), ('SB', 'Solomon Islands'), ('SO', 'Somalia'),
    ('ZA', 'South Africa'), ('SS', 'South Sudan'), ('ES', 'Spain'), ('LK', 'Sri Lanka'),
    ('SD', 'Sudan'), ('SR', 'Suriname'), ('SE', 'Sweden'), ('CH', 'Switzerland'),
    ('SY', 'Syria'), ('TJ', 'Tajikistan'), ('TZ', 'Tanzania'), ('TH', 'Thailand'),
    ('TL', 'Timor-Leste'), ('TG', 'Togo'), ('TO', 'Tonga'), ('TT', 'Trinidad and Tobago'),
    ('TN', 'Tunisia'), ('TR', 'Turkey'), ('TM', 'Turkmenistan'), ('TV', 'Tuvalu'),
    ('UG', 'Uganda'), ('UA', 'Ukraine'), ('AE', 'United Arab Emirates'), ('GB', 'United Kingdom'),
    ('US', 'United States'), ('UY', 'Uruguay'), ('UZ', 'Uzbekistan'), ('VU', 'Vanuatu'),
    ('VA', 'Vatican City'), ('VE', 'Venezuela'), ('VN', 'Vietnam'), ('YE', 'Yemen'),
    ('ZM', 'Zambia'), ('ZW', 'Zimbabwe'),
)

# Customer-facing message per stage (English, shown live on web + mobile)
REVIEW_STAGE_MESSAGES = {
    'received': 'Your application has been sent directly to the bank. The bank has received it and review is starting.',
    'document_verification': 'Your application is under review — the bank is now verifying your documents.',
    'crb_check': 'Your application is under review — the bank is now at the CRB stage, checking your credit history with the Credit Reference Bureau.',
    'valuation': 'Your application is under review — the bank is now valuing the property.',
    'credit_assessment': 'Your application is under review — the bank is now doing the final credit assessment (income, affordability, employment).',
    'approval_decision': 'Your application is under review — the bank is now making the final approval decision.',
    'approved': 'Congratulations! Your application has been approved by the bank.',
    'rejected': 'The bank has finished review — unfortunately this application was rejected. Check the reason and notes.',
    'disbursed': 'Your loan has been disbursed.',
}


class MortgageApplication(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft - Incomplete'),
        ('pending', 'Pending'),
        ('document_verification', 'Document Verification'),
        ('crb_check', 'CRB Check'),
        ('valuation', 'Valuation'),
        ('credit_assessment', 'Credit Assessment'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
    )
    LOAN_TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('refinance', 'Refinance/Equity Release'),
        ('semi_finish', 'Semi Finish'),
        ('construction', 'Construction'),
        ('commercial', 'Commercial'),
    )
    MORTGAGE_TYPE_CHOICES = (
        ('residential', 'Residential'),
        ('construction', 'Home Construction'),
        ('renovation', 'Renovation'),
        ('commercial', 'Commercial'),
    )

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'customer'}, related_name='mortgage_applications')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='mortgage_applications', null=True, blank=True)
    bank = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'bank'}, related_name='bank_mortgages', help_text="Bank selected by customer")

    class Meta:
        ordering = ['-created_at']

    loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    down_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    repayment_period = models.IntegerField(help_text="Repayment period in months", null=True, blank=True)

    monthly_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    monthly_expenses = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    employment_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=(
            ('employed', 'Employed'),
            ('self_employed', 'Self-Employed'),
            ('business_owner', 'Business Owner'),
            ('business', 'Business Owner'),
            ('unemployed', 'Unemployed'),
        )
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')

    # --- Customer personal / NIDA / marital ---
    marital_status = models.CharField(max_length=20, blank=True, null=True, choices=(('single','Single'),('married','Married')), help_text="Single or Married")
    dob = models.DateField(blank=True, null=True, help_text="Birth date - must be 18-57 years, must match NIDA")
    nida_number = models.CharField(max_length=30, blank=True, null=True, help_text="NIDA number 20 digits - first 8 encode DOB YYYYMMDD")
    gender = models.CharField(max_length=10, blank=True, null=True, choices=(('male','Male'),('female','Female')), help_text="Gender")
    dependents = models.IntegerField(blank=True, null=True, default=0, help_text="Number of dependents")
    nationality = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='TZ', blank=True, null=True, help_text="Applicant nationality - default Tanzania")
    # --- Employment details (persisted so bank always sees them, not only draft_data) ---
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    years_employed = models.IntegerField(blank=True, null=True)
    contract_type = models.CharField(max_length=20, blank=True, null=True, choices=(('permanent','Permanent'),('contract','Contract')))
    # --- Bank account details (Step 5 - required) ---
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, help_text="Customer account number at the selected bank")
    bank_account_name = models.CharField(max_length=200, blank=True, null=True, help_text="Account holder name at the selected bank")
    marriage_certificate_number = models.CharField(max_length=50, blank=True, null=True, help_text="Marriage certificate card number (if married)")
    marriage_certificate_file = models.FileField(upload_to='mortgage_documents/marriage/', blank=True, null=True)

    # --- Business / employment extra ---
    business_name = models.CharField(max_length=200, blank=True, null=True, help_text="Business name")
    business_years = models.IntegerField(blank=True, null=True, help_text="Years in business")
    business_type = models.CharField(max_length=20, blank=True, null=True, choices=(('wholesale','Wholesale'),('retail','Retail')), help_text="Wholesale or Retail only")
    business_registration_number = models.CharField(max_length=50, blank=True, null=True, help_text="BRELA BRL-... or Halmashauri LIC-... number")
    annual_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Average annual income for business owner")

    # --- Statutory deductions (based on income) ---
    employment_sector = models.CharField(max_length=20, blank=True, null=True, choices=(('public','Public Sector'),('private','Private Sector')), help_text="Public vs Private sector - PSSSF 5% applies only to public")
    deduction_psssf = models.BooleanField(default=False, help_text="PSSSF 5% of salary - public sector employees only")
    deduction_heslb = models.BooleanField(default=False, help_text="HESLB 15% of salary - for those with education loan")
    deduction_paye = models.BooleanField(default=False, help_text="PAYE 0-30% based on income bracket")
    psssf_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Computed PSSSF 5%")
    heslb_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Computed HESLB 15%")
    paye_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Computed PAYE per bracket")
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Total deductions")
    net_monthly_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Net monthly income after deductions")

    # --- Existing / Other loan (Step 6) ---
    has_other_loan = models.CharField(max_length=10, blank=True, null=True, choices=(('yes','Yes'),('no','No')), help_text="Do you have another loan at a different bank?")
    other_loan_bank = models.CharField(max_length=150, blank=True, null=True, help_text="Existing loan bank name")
    other_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Original amount of existing loan")
    other_loan_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Outstanding balance")
    other_loan_monthly_payment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Monthly payment of existing loan")
    other_loan_consolidate = models.CharField(max_length=10, blank=True, null=True, choices=(('yes','Yes - Consolidate'),('no','No - Keep Separate')), help_text="Should the new loan consolidate the old debt? (Takeover)")
    # legacy alias from Step 3 (has_existing_loan) -> mapped to has_other_loan
    has_existing_loan = models.CharField(max_length=10, blank=True, null=True, choices=(('yes','Yes'),('no','No')))
    existing_loan_bank = models.CharField(max_length=150, blank=True, null=True)
    existing_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    existing_loan_repayment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    existing_loan_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    # Bank step-by-step review tracking - customer sees this live
    review_stage = models.CharField(max_length=30, default='received', help_text="Current bank review stage")
    review_note = models.TextField(blank=True, null=True, help_text="Latest bank note shown to customer")

    # Draft tracking - user wanted saving at step 3 to resume right there
    loan_type = models.CharField(max_length=30, choices=LOAN_TYPE_CHOICES, blank=True, null=True, help_text="Type of loan - purchase/construction etc")
    mortgage_type = models.CharField(max_length=30, choices=MORTGAGE_TYPE_CHOICES, blank=True, null=True, help_text="Mortgage category from ?type= param")
    current_step = models.IntegerField(default=1, help_text="Wizard step where user saved - 1..8")
    draft_data = models.JSONField(default=dict, blank=True, help_text="Full form draft for resume")

    # AI Features - Calculated automatically
    affordability_score = models.FloatField(null=True, blank=True, help_text="Affordability score (0-100)")
    risk_score = models.FloatField(null=True, blank=True, help_text="Risk score (0-100, higher = higher risk)")
    monthly_installment = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    dti_ratio = models.FloatField(null=True, blank=True, help_text="Debt-to-Income Ratio")

    documents = models.FileField(upload_to='mortgage_documents/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @builtins.property
    def application_number(self):
        """Designed code: MORG-TYPE-XXXXXX - e.g. MORG-RES-000042, MORG-CON-000042, MORG-LND-000042"""
        type_map = {
            'residential': 'RES',
            'construction': 'CON',
            'renovation': 'REN',
            'commercial': 'COM',
        }
        prefix = type_map.get(self.mortgage_type or self.loan_type or 'residential', 'GEN')
        try:
            pid = self.id or 0
        except:
            pid = 0
        return f"MORG-{prefix}-{pid:06d}"

    @builtins.property
    def application_code(self):
        return self.application_number

    def __str__(self):
        try:
            prop = self.property.title if self.property_id and self.property else 'No Property'
        except:
            prop = 'No Property'
        try:
            code = self.application_number
        except:
            code = f"APP-{self.id}"
        return f"{code} | {self.customer.email} - {prop} - {self.loan_amount} TZS"


class ApplicationTimelineEvent(models.Model):
    """Every bank confirmation step - shown live to the customer (web + mobile)."""
    STAGE_CHOICES = (
        ('received', 'Received by Bank'),
        ('document_verification', 'Document Verification'),
        ('crb_check', 'CRB / Credit Reference Check'),
        ('valuation', 'Property Valuation'),
        ('credit_assessment', 'Credit Assessment'),
        ('approval_decision', 'Approval Decision'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('note', 'General Update'),
    )
    application = models.ForeignKey(MortgageApplication, on_delete=models.CASCADE, related_name='timeline_events')
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default='received')
    title = models.CharField(max_length=200, default='')
    message = models.TextField(default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='timeline_updates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.application_id} | {self.stage} | {self.created_at:%Y-%m-%d %H:%M}"

    @staticmethod
    def log(application, stage, title='', message='', user=None):
        from .models import REVIEW_STAGE_MESSAGES
        if not message:
            message = REVIEW_STAGE_MESSAGES.get(stage, title or stage)
        if not title:
            title = dict(ApplicationTimelineEvent.STAGE_CHOICES).get(stage, stage)
        return ApplicationTimelineEvent.objects.create(
            application=application, stage=stage, title=title, message=message, created_by=user,
        )


class ApplicationCorrection(models.Model):
    """Bank asks the customer to fix/resend something (e.g. re-upload a title
    deed that is not clear, or type in the NIDA number). The customer sees it
    on their track page with instructions + an input field, responds there,
    and both sides are notified through the timeline."""
    KIND_CHOICES = (
        ('document', 'Document re-upload'),
        ('nida', 'NIDA / ID number'),
        ('info', 'Information / text'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending customer action'),
        ('resolved', 'Resolved'),
    )
    application = models.ForeignKey(MortgageApplication, on_delete=models.CASCADE, related_name='corrections')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='document')
    target = models.CharField(max_length=200, blank=True, default='', help_text="Which document/field, e.g. 'hati', 'NIDA'")
    instructions = models.TextField(help_text="Bank instructions shown to the customer")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_text = models.TextField(blank=True, default='')
    response_file = models.FileField(upload_to='correction_responses/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requested_corrections')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application_id} | {self.get_kind_display()} {self.target} | {self.status}"


class BankNotification(models.Model):
    """Persistent bank notifications - stored in the DB so they never vanish.
    Created on: new application received, customer correction submitted, etc.
    Read state is stored per row (mark-all/single)."""
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=300, blank=True, default='')
    icon = models.CharField(max_length=50, default='file-text')
    color = models.CharField(max_length=20, default='blue')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient_id} | {self.title} | {'read' if self.is_read else 'unread'}"

    @staticmethod
    def notify(bank_user, title, message, link='', icon='file-text', color='blue'):
        if bank_user is None or not getattr(bank_user, 'id', None):
            return None
        try:
            return BankNotification.objects.create(
                recipient=bank_user, title=title, message=message,
                link=link, icon=icon, color=color)
        except Exception:
            return None


class RepaymentSchedule(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    )

    mortgage = models.ForeignKey(MortgageApplication, on_delete=models.CASCADE, related_name='repayment_schedule')
    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_remaining = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.mortgage} - Instalment #{self.installment_number}"


class MortgageHousePhoto(models.Model):
    """Semi-Finish / Renovation applicant uploads photos of their own house
    at lintel stage. Min 10, max 20. One is chosen as cover."""
    mortgage = models.ForeignKey(MortgageApplication, on_delete=models.CASCADE, related_name='house_photos')
    image = models.ImageField(upload_to='mortgage_houses/')
    is_cover = models.BooleanField(default=False, help_text="Cover photo shown to the bank")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"House photo {self.id} for mortgage {self.mortgage_id} {'(Cover)' if self.is_cover else ''}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_cover:
            MortgageHousePhoto.objects.filter(mortgage=self.mortgage).exclude(id=self.id).update(is_cover=False)


class MortgageDocument(models.Model):
    DOC_TYPE_CHOICES = (
        ('id_passport', 'ID/Passport Copy'),
        ('payslip', 'Pay Slip'),
        ('bank_statement', 'Bank Statement'),
        ('tax_clearance', 'Tax Clearance'),
        ('other', 'Other'),
    )
    mortgage = models.ForeignKey(MortgageApplication, on_delete=models.CASCADE, related_name='document_files')
    file = models.FileField(upload_to='mortgage_documents/')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='other')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mortgage.customer.email} - {self.get_doc_type_display()} - {self.file.name}"


class CustomerHold(models.Model):
    """A bank can place a hold on a customer (e.g. during review / dispute).
    While an active hold exists, the customer cannot delete their account."""
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'customer'}, related_name='bank_holds')
    bank = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'bank'}, related_name='held_customers')
    reason = models.TextField(blank=True, default='', help_text="Reason for holding the customer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [['customer', 'bank', 'is_active']]

    def __str__(self):
        return f"Hold: {self.customer.email} by {self.bank.get_full_name()}"


# Auto-clean orphan bank notifications when an application is deleted,
# so the bank bell never points to a 404 URL.
try:
    from django.db.models.signals import post_delete
    from django.dispatch import receiver as _receiver

    @_receiver(post_delete, sender=MortgageApplication)
    def _delete_orphan_bank_notifications(sender, instance, **kwargs):
        try:
            pk = getattr(instance, 'pk', None) or getattr(instance, 'id', None)
            if pk:
                BankNotification.objects.filter(
                    link__contains=f'/bank/applications/{pk}/').delete()
        except Exception:
            pass
except Exception:
    pass
