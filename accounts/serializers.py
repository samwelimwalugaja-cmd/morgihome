from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    initials = serializers.ReadOnlyField()
    avatar_url = serializers.ReadOnlyField()
    profile_image = serializers.ImageField(required=False, allow_null=True)
    verification_level = serializers.ReadOnlyField()
    verification_level_display = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'phone_number', 'is_verified',
                  'verification_level', 'verification_level_display',
                  'profile_image', 'avatar_url', 'initials',
                  'business_license_verified', 'tax_clearance_verified', 'company_registration_verified',
                  'interest_rate', 'processing_fee', 'min_loan_amount', 'max_loan_amount', 'bank_requirements']
        read_only_fields = ['id', 'verification_level',
                            'verification_level_display', 'avatar_url', 'initials', 'full_name',
                            'business_license_verified', 'tax_clearance_verified', 'company_registration_verified']


class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=15, required=True)
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    # role is set automatically to customer/seller only - bank/realestate is Admin only
    role = serializers.ChoiceField(choices=[('customer','Customer'),('seller','Seller')], required=False, default='customer')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'confirm_password', 'role']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip()).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.strip().lower()

    def validate_phone_number(self, value):
        import re
        cleaned = re.sub(r'\s+', '', value or '')
        if not re.match(r'^\+?\d{9,15}$', cleaned):
            raise serializers.ValidationError("Phone number invalid. Use e.g. +255 712 345 678")
        return value.strip()

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if len(attrs.get('first_name','').strip()) < 2:
            raise serializers.ValidationError({"first_name": "First name must be at least 2 characters."})
        if len(attrs.get('last_name','').strip()) < 2:
            raise serializers.ValidationError({"last_name": "Last name must be at least 2 characters."})
        # Only customer/seller allowed self-register
        if attrs.get('role') not in ['customer','seller']:
            raise serializers.ValidationError({"role": "Only customer/seller can self-register. Bank/RealEstate is Admin only."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['email'] = validated_data['email'].strip().lower()
        user = User.objects.create_user(**validated_data)
        return user
