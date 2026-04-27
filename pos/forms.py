from django import forms
from billing.models import BillItem


class BillItemForm(forms.ModelForm):

    class Meta:
        model = BillItem
        fields = ["product", "quantity"]

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")

        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0.")

        return quantity
