from rest_framework import serializers

from properties.serializers import PropertySerializer
from .models import ApplicationCorrection, ApplicationTimelineEvent, MortgageApplication, RepaymentSchedule


class TimelineEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationTimelineEvent
        fields = ['id', 'stage', 'title', 'message', 'created_by_name', 'created_at']

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else 'Bank'


class CorrectionSerializer(serializers.ModelSerializer):
    kind_display = serializers.SerializerMethodField()
    response_file_url = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationCorrection
        fields = ['id', 'kind', 'kind_display', 'target', 'instructions', 'status',
                  'response_text', 'response_file_url', 'created_at', 'resolved_at']
        read_only_fields = ['id', 'status', 'response_text', 'response_file_url', 'created_at', 'resolved_at']

    def get_kind_display(self, obj):
        return obj.get_kind_display()

    def get_response_file_url(self, obj):
        try:
            return obj.response_file.url if obj.response_file else None
        except Exception:
            return None


class MortgageApplicationSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    customer_is_verified = serializers.SerializerMethodField()
    customer_verification_level = serializers.SerializerMethodField()
    property_details = PropertySerializer(source='property', read_only=True)
    monthly_installment_display = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    application_number = serializers.SerializerMethodField()
    review_stage_display = serializers.SerializerMethodField()
    review_message = serializers.SerializerMethodField()
    timeline = TimelineEventSerializer(source='timeline_events', many=True, read_only=True)
    corrections = CorrectionSerializer(many=True, read_only=True)

    class Meta:
        model = MortgageApplication
        fields = ['id', 'application_number', 'customer', 'customer_name', 'customer_is_verified', 'customer_verification_level', 'property', 'property_details',
                  'bank', 'bank_name', 'bank_details',
                  'loan_amount', 'down_payment', 'repayment_period',
                  'monthly_income', 'monthly_expenses', 'employment_status',
                  'status', 'review_stage', 'review_stage_display', 'review_message', 'review_note', 'timeline', 'corrections',
                  'loan_type', 'mortgage_type', 'current_step', 'draft_data',
                  'affordability_score', 'risk_score',
                  'monthly_installment', 'dti_ratio', 'documents', 'notes',
                  'created_at', 'updated_at', 'monthly_installment_display']
        read_only_fields = ['customer', 'application_number', 'affordability_score', 'risk_score', 'monthly_installment',
                           'dti_ratio', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else None

    def get_customer_is_verified(self, obj):
        return obj.customer.is_verified if obj.customer else False

    def get_customer_verification_level(self, obj):
        return obj.customer.verification_level if obj.customer else 'not_verified'

    def get_bank_name(self, obj):
        return obj.bank.get_full_name() if obj.bank else None

    def get_bank_details(self, obj):
        if not obj.bank:
            return None
        b = obj.bank
        return {
            'id': b.id,
            'name': b.get_full_name(),
            'email': b.email,
            'interest_rate': str(b.interest_rate) if b.interest_rate else None,
            'processing_fee': str(b.processing_fee) if b.processing_fee else None,
            'min_loan_amount': str(b.min_loan_amount) if b.min_loan_amount else None,
            'max_loan_amount': str(b.max_loan_amount) if b.max_loan_amount else None,
            'bank_requirements': b.bank_requirements,
        }

    def get_monthly_installment_display(self, obj):
        if obj.monthly_installment:
            return f"{obj.monthly_installment:,.2f} TZS"
        return None

    def get_application_number(self, obj):
        try:
            return obj.application_number
        except:
            return f"APP-{obj.id:06d}"

    def get_review_stage_display(self, obj):
        return dict(ApplicationTimelineEvent.STAGE_CHOICES).get(obj.review_stage or 'received', obj.review_stage)

    def get_review_message(self, obj):
        # Live customer-facing message: latest timeline message or stage default
        try:
            latest = obj.timeline_events.order_by('-created_at').first()
            if latest and latest.message:
                return latest.message
        except Exception:
            pass
        from .models import REVIEW_STAGE_MESSAGES
        if obj.status == 'approved':
            return REVIEW_STAGE_MESSAGES.get('approved')
        if obj.status == 'rejected':
            return REVIEW_STAGE_MESSAGES.get('rejected')
        if obj.status == 'disbursed':
            return REVIEW_STAGE_MESSAGES.get('disbursed')
        return REVIEW_STAGE_MESSAGES.get(obj.review_stage or 'received', '')

    def validate_bank(self, value):
        if value and value.role != 'bank':
            raise serializers.ValidationError("Selected user is not a bank.")
        return value

    def validate(self, attrs):
        # Step 6: if bank is provided, ensure loan is within bank min/max
        bank = attrs.get('bank') or (self.instance.bank if self.instance else None)
        loan = attrs.get('loan_amount')
        if bank and loan:
            if bank.min_loan_amount and loan < bank.min_loan_amount:
                raise serializers.ValidationError({'loan_amount': f"Loan below bank minimum {bank.min_loan_amount} TZS"})
            if bank.max_loan_amount and loan > bank.max_loan_amount:
                raise serializers.ValidationError({'loan_amount': f"Loan exceeds bank maximum {bank.max_loan_amount} TZS"})
        # A purchase loan can never exceed the property value (collateral).
        # E.g. property worth 2M with a 10M request must be rejected outright.
        prop = attrs.get('property') or (self.instance.property if self.instance else None)
        mtype = attrs.get('mortgage_type') or (self.instance.mortgage_type if self.instance else None)
        if prop and loan and mtype in ('residential', 'commercial', 'land'):
            try:
                price = float(prop.price or 0)
            except (TypeError, ValueError):
                price = 0
            if price > 0 and float(loan) > price:
                raise serializers.ValidationError({
                    'loan_amount': f"Loan amount (TZS {float(loan):,.0f}) exceeds the property value (TZS {price:,.0f}). Reduce the amount."})
        return attrs


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepaymentSchedule
        fields = '__all__'
