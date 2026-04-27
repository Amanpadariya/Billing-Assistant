from django import forms
from billing.models import Bill
from customers.models import Customer
from django.core.validators import RegexValidator

class InvoiceForm(forms.ModelForm):

    created_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            "class": "form-control"
        })
    )

    # ✅ FIXED FIELD
    customer_phone = forms.CharField(
        required=False,
        max_length=10,
        min_length=10,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "maxlength": "10",
            "pattern": "[0-9]{10}",
            "title": "Enter 10 digit phone number",
            "inputmode": "numeric"
        })
    )

    class Meta:
        model = Bill
        fields = ["customer", "customer_name", "customer_phone", "created_at"]

        widgets = {
            "customer": forms.Select(attrs={"class": "form-select","required": False}),
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone')

        if phone:
            if not phone.isdigit():
                raise forms.ValidationError("Only digits allowed")
            if len(phone) != 10:
                raise forms.ValidationError("Must be 10 digits")

        return phone

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["customer"].required = False
        self.fields["customer"].empty_label = "Select Customer"

