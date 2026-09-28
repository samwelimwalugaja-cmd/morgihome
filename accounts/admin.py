from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import User

# Admin site customization - MorgiHome
admin.site.site_header = "MorgiHome Admin"
admin.site.site_title = "MorgiHome Administration"
admin.site.index_title = "Welcome to MorgiHome Admin Panel"


@admin.action(description='Verify selected users email addresses manually')
def verify_email_manually(modeladmin, request, queryset):
    """Admin can mark users as email-verified without requiring the verification link."""
    count = queryset.update(
        email_verified=True,
        email_verified_at=timezone.now(),
        email_verification_token='',
    )
    modeladmin.message_user(request, f'{count} user(s) had their email verified manually.')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'email_verified', 'is_verified', 'business_license_verified', 'tax_clearance_verified', 'company_registration_verified', 'is_staff')
    list_filter = ('role', 'email_verified', 'is_verified', 'business_license_verified', 'tax_clearance_verified', 'company_registration_verified', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    actions = [verify_email_manually]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'role', 'profile_image')}),
        # Email Verification is kept visible (not collapsed) so admins can manually
        # verify a user's email when the verification link cannot be delivered/clicked.
        ('Email Verification', {'fields': ('email_verified', 'email_verified_at', 'email_verification_token', 'email_verification_sent_at')}),
        ('Bank info (for role=bank)', {'fields': ('interest_rate', 'processing_fee', 'min_loan_amount', 'max_loan_amount', 'max_repayment_period', 'bank_requirements')}),
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
    readonly_fields = ('email_verified_at', 'email_verification_sent_at')

    def save_model(self, request, obj, form, change):
        # When an admin manually checks email_verified, record the timestamp and
        # clear the one-time token so the user can log in immediately.
        if 'email_verified' in form.changed_data and obj.email_verified:
            obj.email_verified_at = timezone.now()
            obj.email_verification_token = ''
        super().save_model(request, obj, form, change)


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
    list_display = ('email', 'first_name', 'role', 'email_verified', 'is_verified', 'interest_rate', 'is_staff')
    list_filter = ('email_verified', 'is_verified',)
    search_fields = ('email', 'first_name')
    actions = [verify_email_manually]
    readonly_fields = ('email_verified_at', 'email_verification_sent_at')
    # User has no `username` (email is the identifier) - fieldsets must be rewritten
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Bank info', {'fields': ('first_name', 'phone_number', 'profile_image')}),
        ('Email Verification', {'fields': ('email_verified', 'email_verified_at', 'email_verification_token', 'email_verification_sent_at')}),
        ('Loan terms', {'fields': ('interest_rate', 'processing_fee', 'min_loan_amount', 'max_loan_amount', 'max_repayment_period', 'bank_requirements')}),
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
        # When an admin manually checks email_verified, record the timestamp and
        # clear the one-time token so the user can log in immediately.
        if 'email_verified' in form.changed_data and obj.email_verified:
            obj.email_verified_at = timezone.now()
            obj.email_verification_token = ''
        super().save_model(request, obj, form, change)

@admin.register(RealEstateProxy)
class RealEstateAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'email_verified', 'is_verified')
    list_filter = ('email_verified', 'is_verified',)
    search_fields = ('email', 'first_name', 'last_name')
    actions = [verify_email_manually]
    readonly_fields = ('email_verified_at', 'email_verification_sent_at')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Company info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_image')}),
        ('Email Verification', {'fields': ('email_verified', 'email_verified_at', 'email_verification_token', 'email_verification_sent_at')}),
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
        # When an admin manually checks email_verified, record the timestamp and
        # clear the one-time token so the user can log in immediately.
        if 'email_verified' in form.changed_data and obj.email_verified:
            obj.email_verified_at = timezone.now()
            obj.email_verification_token = ''
        super().save_model(request, obj, form, change)
