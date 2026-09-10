from django.contrib import admin
from .models import ApplicationCorrection, ApplicationTimelineEvent, BankNotification, MortgageApplication, RepaymentSchedule, MortgageDocument

class MortgageDocumentInline(admin.TabularInline):
    model = MortgageDocument
    extra = 0
    readonly_fields = ('uploaded_at',)

class RepaymentScheduleInline(admin.TabularInline):
    model = RepaymentSchedule
    extra = 0


class TimelineInline(admin.TabularInline):
    model = ApplicationTimelineEvent
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(MortgageApplication)
class MortgageApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_number', 'customer', 'property', 'bank', 'loan_amount', 'status', 'review_stage', 'mortgage_type', 'affordability_score', 'risk_score', 'created_at')
    list_filter = ('status', 'review_stage', 'mortgage_type', 'loan_type', 'employment_status')
    search_fields = ('customer__email', 'property__title', 'bank__email')
    readonly_fields = ('application_number', 'affordability_score', 'risk_score', 'dti_ratio', 'monthly_installment', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('application_number', 'customer', 'property', 'bank', 'status', 'review_stage', 'review_note', 'mortgage_type', 'loan_type', 'current_step')}),
        ('Financials', {'fields': ('loan_amount', 'down_payment', 'repayment_period', 'monthly_income', 'monthly_expenses', 'monthly_installment', 'affordability_score', 'risk_score', 'dti_ratio')}),
        ('Employment', {'fields': ('employment_status',)}),
        ('Documents', {'fields': ('documents', 'notes')}),
    )
    inlines = [MortgageDocumentInline, RepaymentScheduleInline, TimelineInline]

@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    list_display = ('mortgage', 'installment_number', 'due_date', 'amount_due', 'status')
    list_filter = ('status',)
    search_fields = ('mortgage__customer__email',)

@admin.register(MortgageDocument)
class MortgageDocumentAdmin(admin.ModelAdmin):
    list_display = ('mortgage', 'doc_type', 'file', 'uploaded_at')
    list_filter = ('doc_type',)


@admin.register(ApplicationTimelineEvent)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('application', 'stage', 'title', 'created_by', 'created_at')
    list_filter = ('stage',)


@admin.register(ApplicationCorrection)
class CorrectionAdmin(admin.ModelAdmin):
    list_display = ('application', 'kind', 'target', 'status', 'created_by', 'created_at')
    list_filter = ('kind', 'status')


@admin.register(BankNotification)
class BankNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)
