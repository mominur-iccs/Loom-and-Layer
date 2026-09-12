from django import forms
from .models import SIZE_CHOICES


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        max_length=100,
        label="Full name",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Mominur Rahman"}),
    )
    phone = forms.CharField(
        max_length=20,
        label="Phone number",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 01712345678"}),
    )
    email = forms.EmailField(
        max_length=100,
        required=False,
        label="Email (optional)",
        help_text="We'll send you a copy of your order with the design preview.",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    address = forms.CharField(
        label="Delivery address",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "House / road / area, city — anything the courier needs to find you.",
        }),
    )
    size = forms.ChoiceField(
        choices=SIZE_CHOICES,
        initial="M",
        label="Size",
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        label="Quantity",
        widget=forms.NumberInput(attrs={"placeholder": "1"}),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = phone.replace("+", "").replace(" ", "")
        if not digits.isdigit() or len(digits) < 10:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone