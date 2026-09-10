from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User

# Admin site customization - MorgiHome
admin.site.site_header = "MorgiHome Admin"
admin.site.site_title = "MorgiHome Administration"
admin.site.index_title = "Welcome to MorgiHome Admin Panel"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'business_license_verified', 'tax_clearance_verified', 'company_registration_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'business_license_verified', 'tax_clearance_verified', 'company_registration_verified', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'role', 'profile_image')}),
        ('Bank info (for role=bank)', {'fields': ('interest_rate', 'processing_fee', 'min_loan_amount', 'max_loan_amount', 'bank_requirements')}),
        ('Business Verification (Bank/RealEstate)', {'fields': ('business_license', 'business_license_verified', 'business_license_status', 'tax_clearance', 'tax_clearance_verified', 'tax_clearance_status', 'company_registration', 'company_registration_verified', 'company_registration_status', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )


# Proxy models for Bank and RealEstate filtering in Admin
class BankProxy(User):
    class Meta:
        proxy = True
        verbose_name = "Bank"
        verbose_name_plural = "Banks"

class RealEstateProxy(User):
    class Meta:
        proxy = True
        verbose_name = "Real Estate"
        verbose_name_plural = "Real Estates"

@admin.register(BankProxy)
class BankAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'role', 'is_verified', 'interest_rate', 'is_staff')
    list_filter = ('is_verified',)
    search_fields = ('email', 'first_name')
    # User has no `username` (email is the identifier) - fieldsets must be rewritten
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Bank info', {'fields': ('first_name', 'phone_number', 'profile_image')}),
        ('Loan terms', {'fields': ('interest_rate', 'processing_fee', 'min_loan_amount', 'max_loan_amount', 'bank_requirements')}),
        ('Business Verification', {'fields': ('business_license', 'business_license_verified', 'business_license_status', 'tax_clearance', 'tax_clearance_verified', 'tax_clearance_status', 'company_registration', 'company_registration_verified', 'company_registration_status', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'phone_number', 'password1', 'password2'),
        }),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='bank')
    def save_model(self, request, obj, form, change):
        # Add via Bank admin -> always role bank
        if not change:
            obj.role = 'bank'
            if not obj.last_name:
                obj.last_name = 'Bank'
        super().save_model(request, obj, form, change)

@admin.register(RealEstateProxy)
class RealEstateAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Company info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_image')}),
        ('Business Verification', {'fields': ('business_license', 'business_license_verified', 'business_license_status', 'company_registration', 'company_registration_verified', 'company_registration_status', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2'),
        }),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='realestate')
    def save_model(self, request, obj, form, change):
        # Add via Real Estate admin -> always role realestate
        if not change:
            obj.role = 'realestate'
        super().save_model(request, obj, form, change)
