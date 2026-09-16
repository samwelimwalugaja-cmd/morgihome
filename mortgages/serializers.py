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


def calc_paye_tz(income):
    """PAYE Tanzania brackets per spec - returns tax amount"""
    try:
        inc = float(income or 0)
    except:
        return 0
    if inc <= 270000:
        return 0
    elif inc <= 520000:
        return (inc - 270000) * 0.08
    elif inc <= 760000:
        return 20000 + (inc - 520000) * 0.20
    elif inc <= 1000000:
        return 68000 + (inc - 760000) * 0.25
    else:
        return 128000 + (inc - 1000000) * 0.30


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
                  'marital_status', 'dob', 'nida_number', 'marriage_certificate_number', 'marriage_certificate_file',
                  'business_type', 'business_registration_number', 'annual_income',
                  'employment_sector', 'deduction_psssf', 'deduction_heslb', 'deduction_paye',
                  'psssf_amount', 'heslb_amount', 'paye_amount', 'total_deductions', 'net_monthly_income',
                  'has_other_loan', 'other_loan_bank', 'other_loan_amount', 'other_loan_balance', 'other_loan_monthly_payment', 'other_loan_consolidate',
                  'has_existing_loan', 'existing_loan_bank', 'existing_loan_amount', 'existing_loan_repayment', 'existing_loan_balance',
                  'status', 'review_stage', 'review_stage_display', 'review_message', 'review_note', 'timeline', 'corrections',
                  'loan_type', 'mortgage_type', 'current_step', 'draft_data',
                  'affordability_score', 'risk_score',
                  'monthly_installment', 'dti_ratio', 'documents', 'notes',
                  'created_at', 'updated_at', 'monthly_installment_display']
        read_only_fields = ['customer', 'application_number', 'affordability_score', 'risk_score', 'monthly_installment',
                           'dti_ratio', 'psssf_amount', 'heslb_amount', 'paye_amount', 'total_deductions', 'net_monthly_income',
                           'created_at', 'updated_at']

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
            'max_repayment_period': b.max_repayment_period,
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

    def _validate_nida_dob(self, nida, dob):
        """Validate NIDA first 8 = YYYYMMDD must match dob, and age 18-57"""
        import re
        from datetime import date
        errors = {}
        if nida:
            nida = str(nida).strip().replace(' ', '').replace('-', '')
            # NIDA Tanzania 20 digits, but we check first 8
            if not re.match(r'^\d{20}$', nida):
                errors['nida_number'] = 'NIDA must be 20 digits.'
            else:
                try:
                    y = int(nida[0:4]); m = int(nida[4:6]); d = int(nida[6:8])
                    nida_date = date(y, m, d)
                    if dob and nida_date != dob:
                        errors['nida_number'] = f'NIDA DOB {nida_date} does not match birth date {dob}. First 8 of NIDA must be YYYYMMDD of birth.'
                    # also validate nida date itself is realistic
                    if nida_date > date.today():
                        errors['nida_number'] = 'NIDA birth date cannot be in future.'
                except Exception:
                    errors['nida_number'] = 'Invalid NIDA date part (first 8 digits must be YYYYMMDD).'
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                errors['dob'] = 'Age must be at least 18 years. You are too young to apply.'
            if age > 57:
                errors['dob'] = 'Maximum age is 57 years. You exceed limit to apply for mortgage.'
            if dob.year == today.year:
                errors['dob'] = 'Birth date cannot be this year. Must be at least 18 years ago.'
        if errors:
            raise serializers.ValidationError(errors)

    def validate(self, attrs):
        # Validate NIDA / DOB / marital
        nida = attrs.get('nida_number') or (self.instance.nida_number if self.instance else None)
        dob = attrs.get('dob') or (self.instance.dob if self.instance else None)
        marital = attrs.get('marital_status') or (self.instance.marital_status if self.instance else None)
        mcert = attrs.get('marriage_certificate_number') or (self.instance.marriage_certificate_number if self.instance else None)
        # If dob is string, parse
        if isinstance(dob, str):
            try:
                from datetime import datetime
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
                attrs['dob'] = dob
            except Exception:
                pass
        self._validate_nida_dob(nida, dob)
        if marital == 'married' and not mcert:
            raise serializers.ValidationError({'marriage_certificate_number': 'Married applicants must provide marriage certificate card number.'})
        # Business validation: BRELA or LIC format, wholesale/retail only
        btype = attrs.get('business_type') or (self.instance.business_type if self.instance else None)
        breg = attrs.get('business_registration_number') or (self.instance.business_registration_number if self.instance else None)
        emp = attrs.get('employment_status') or (self.instance.employment_status if self.instance else None)
        if emp in ('business_owner', 'business', 'self_employed'):
            if btype and btype not in ('wholesale','retail'):
                raise serializers.ValidationError({'business_type': 'Business type must be Wholesale or Retail only.'})
            if breg:
                import re
                # BRELA: BRL-2024-001234, LIC: LIC-DSM-2024-005678
                if not (re.match(r'^BRL-\d{4}-\d{6}$', str(breg).strip()) or re.match(r'^LIC-[A-Z]{2,4}-\d{4}-\d{6}$', str(breg).strip())):
                    raise serializers.ValidationError({'business_registration_number': 'Invalid format. Use BRELA BRL-YYYY-XXXXXX or Council LIC-XXX-YYYY-XXXXXX (e.g. BRL-2024-001234 or LIC-DSM-2024-005678).'})
        # Step 6: if bank is provided, ensure loan is within bank min/max and period within bank max
        bank = attrs.get('bank') or (self.instance.bank if self.instance else None)
        loan = attrs.get('loan_amount')
        period = attrs.get('repayment_period') or (self.instance.repayment_period if self.instance else None)
        if bank and loan:
            if bank.min_loan_amount and loan < bank.min_loan_amount:
                raise serializers.ValidationError({'loan_amount': f"Loan below bank minimum {bank.min_loan_amount:,.0f} TZS. Bank limit is {bank.min_loan_amount:,.0f} - {bank.max_loan_amount or '—'} TZS."})
            if bank.max_loan_amount and loan > bank.max_loan_amount:
                raise serializers.ValidationError({'loan_amount': f"Loan exceeds bank maximum {bank.max_loan_amount:,.0f} TZS. Bank limit is {bank.min_loan_amount or '—'} - {bank.max_loan_amount:,.0f} TZS."})
        if bank and period and getattr(bank, 'max_repayment_period', None):
            if period > bank.max_repayment_period:
                years = bank.max_repayment_period / 12
                raise serializers.ValidationError({'repayment_period': f"Repayment period exceeds bank maximum {bank.max_repayment_period} months ({years:.0f} years). Selected bank allows max {bank.max_repayment_period} months."})
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
        # Statutory deductions validation: PSSSF only for employed public sector; but allow but backend will ignore if not applicable
        has_other = attrs.get('has_other_loan') or (self.instance.has_other_loan if self.instance else None)
        if has_other == 'yes':
            other_bank = attrs.get('other_loan_bank') or (self.instance.other_loan_bank if self.instance else None)
            other_bal = attrs.get('other_loan_balance') or (self.instance.other_loan_balance if self.instance else None)
            if not other_bank:
                raise serializers.ValidationError({'other_loan_bank': 'Benki ya mkopo wa zamani inahitajika kama una mkopo mwingine.'})
            if not other_bal:
                raise serializers.ValidationError({'other_loan_balance': 'Deni lililobaki linahitajika.'})
            # consolidate flag recommended
            consolidate = attrs.get('other_loan_consolidate') or (self.instance.other_loan_consolidate if self.instance else None)
            if not consolidate:
                # auto default to no, but warn - no error, allow
                pass
        return attrs


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepaymentSchedule
        fields = '__all__'
