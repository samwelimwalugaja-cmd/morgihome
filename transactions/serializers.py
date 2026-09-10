from rest_framework import serializers

from mortgages.serializers import MortgageApplicationSerializer
from .models import Contract, Transaction


class ContractSerializer(serializers.ModelSerializer):
    mortgage_details = MortgageApplicationSerializer(source='mortgage', read_only=True)
    customer_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = ['id', 'mortgage', 'mortgage_details', 'customer', 'customer_name',
                  'seller', 'seller_name', 'bank', 'bank_name',
                  'contract_file', 'status', 'customer_signed', 'seller_signed',
                  'bank_signed', 'signed_date', 'executed_date',
                  'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

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
        read_only_fields = ['reference_number', 'created_at']
