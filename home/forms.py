from django import forms


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(max_length=100, label="Full name")
    phone = forms.CharField(max_length=20, label="Phone number")
    email = forms.EmailField(max_length=100, required=False, label="Email (optional)")
    address = forms.CharField(widget=forms.Textarea, label="Full delivery address")

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "").replace("-", "")
        if phone.startswith("+880"):
            phone = "0" + phone[4:]
        if not phone.isdigit() or len(phone) != 11 or not phone.startswith("01"):
            raise forms.ValidationError("Enter a valid Bangladeshi phone number.")
        return phone
