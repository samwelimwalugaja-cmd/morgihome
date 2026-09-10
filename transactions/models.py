from django.conf import settings
from django.db import models

from mortgages.models import MortgageApplication


class Contract(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('executed', 'Executed'),
    )

    mortgage = models.ForeignKey(MortgageApplication, on_delete=models.CASCADE, related_name='contracts')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_contracts', limit_choices_to={'role': 'customer'})
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_contracts', limit_choices_to={'role': 'seller'})
    bank = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_contracts', limit_choices_to={'role': 'bank'})

    contract_file = models.FileField(upload_to='contracts/', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    # Signatures tracking - Lawyer removed, now Admin/Bank handles creation and execution
    customer_signed = models.BooleanField(default=False)
    seller_signed = models.BooleanField(default=False)
    bank_signed = models.BooleanField(default=False)

    signed_date = models.DateField(null=True, blank=True)
    executed_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contract: {self.mortgage} - {self.status}"

    def is_fully_signed(self):
        return all([self.customer_signed, self.seller_signed, self.bank_signed])


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('mortgage_disbursement', 'Mortgage Disbursement'),
        ('installment', 'Installment'),
        ('legal_fee', 'Legal Fee'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.reference_number}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            import uuid
            self.reference_number = f"TRX-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
