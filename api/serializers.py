from rest_framework import serializers

from accounts.models import User
from properties.models import Property
from mortgages.models import MortgageApplication, RepaymentSchedule
from transactions.models import Contract, Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_verified']
        read_only_fields = ['id', 'email', 'role', 'is_verified']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'is_verified', 'first_name', 'last_name',
                  'phone_number', 'profile_image']
        # Mobile app edits first/last/phone/photo - rest read-only
        read_only_fields = ['id', 'email', 'role', 'is_verified']


class PropertyListSerializer(serializers.ModelSerializer):
    seller_name = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ['id', 'title', 'price', 'location', 'property_type', 'status', 'image', 'seller_name']

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() if obj.seller else None


class PropertyDetailSerializer(serializers.ModelSerializer):
    seller_name = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() if obj.seller else None


class MortgageApplicationListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    property_title = serializers.SerializerMethodField()

    class Meta:
        model = MortgageApplication
        fields = ['id', 'customer_name', 'property_title', 'loan_amount', 'status',
                  'affordability_score', 'risk_score', 'created_at']

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else None

    def get_property_title(self, obj):
        return obj.property.title if obj.property else None


class MortgageApplicationDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    property_details = PropertyListSerializer(source='property', read_only=True)

    class Meta:
        model = MortgageApplication
        fields = '__all__'

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else None

    def validate(self, attrs):
        # Same guards as the web serializer: bank min/max + purchase loan capped at property value.
        bank = attrs.get('bank') or (self.instance.bank if self.instance else None)
        loan = attrs.get('loan_amount')
        if bank and loan:
            if bank.min_loan_amount and loan < bank.min_loan_amount:
                raise serializers.ValidationError({'loan_amount': f"Loan below bank minimum {bank.min_loan_amount} TZS"})
            if bank.max_loan_amount and loan > bank.max_loan_amount:
                raise serializers.ValidationError({'loan_amount': f"Loan exceeds bank maximum {bank.max_loan_amount} TZS"})
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


class ContractListSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    property_title = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = ['id', 'customer_name', 'property_title', 'status', 'created_at']

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else None

    def get_property_title(self, obj):
        return obj.mortgage.property.title if obj.mortgage and obj.mortgage.property else None


class ContractDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    mortgage_details = MortgageApplicationListSerializer(source='mortgage', read_only=True)

    class Meta:
        model = Contract
        fields = '__all__'

    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else None

    def get_seller_name(self, obj):
        return obj.seller.get_full_name() if obj.seller else None

    def get_bank_name(self, obj):
        return obj.bank.get_full_name() if obj.bank else None


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'