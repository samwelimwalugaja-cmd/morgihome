from django.contrib import admin
from .models import Contract, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('reference_number', 'created_at')

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    def mortgage_number(self, obj):
        try:
            return obj.mortgage.application_number
        except Exception:
            return '-'
    mortgage_number.short_description = 'Application No'
    list_display = ('id', 'mortgage_number', 'mortgage', 'customer', 'seller', 'bank', 'status', 'customer_signed', 'seller_signed', 'bank_signed', 'created_at')
    list_filter = ('status', 'customer_signed', 'seller_signed', 'bank_signed')
    search_fields = ('customer__email', 'seller__email', 'bank__email', 'mortgage__property__title')
    readonly_fields = ('mortgage_number', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('mortgage_number', 'mortgage', 'customer', 'seller', 'bank', 'status', 'contract_file')}),
        ('Signatures', {'fields': ('customer_signed', 'seller_signed', 'bank_signed', 'signed_date', 'executed_date')}),
        ('Notes', {'fields': ('notes',)}),
    )
    inlines = [TransactionInline]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'contract', 'amount', 'transaction_type', 'status', 'payment_date', 'created_at')
    list_filter = ('transaction_type', 'status')
    search_fields = ('reference_number', 'contract__customer__email')
    readonly_fields = ('reference_number', 'created_at')
