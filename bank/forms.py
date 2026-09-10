from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class BankVerificationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['business_license', 'tax_clearance', 'company_registration']
        widgets = {
            'business_license': forms.ClearableFileInput(attrs={'class': 'morgi-input w-full rounded-lg p-2 text-sm'}),
            'tax_clearance': forms.ClearableFileInput(attrs={'class': 'morgi-input w-full rounded-lg p-2 text-sm'}),
            'company_registration': forms.ClearableFileInput(attrs={'class': 'morgi-input w-full rounded-lg p-2 text-sm'}),
        }
