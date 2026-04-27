# customers/forms.py

from django import forms
from .models import Customer
from django.core.validators import RegexValidator
class CustomerForm(forms.ModelForm):

    phone = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^[0-9]{10}$',
                message="Enter a valid 10-digit phone number"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 10-digit mobile number',
            'maxlength': '10',
            'inputmode': 'numeric'
        })
    )

    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'address']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address (optional)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter customer address'
            }),
        }


    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if Customer.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Customer with this phone already exists")

        return phone