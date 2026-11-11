from django import forms

from customers.forms import PhoneField
from customers.models import phone_validator

from .models import Shop


class ShopForm(forms.ModelForm):
    bkash_number = PhoneField(
        required=False,
        max_length=20,
        validators=[phone_validator],
        label="bKash number for payments (optional)",
        help_text="Customers who choose bKash are asked to send money to this number.",
    )
    nagad_number = PhoneField(
        required=False,
        max_length=20,
        validators=[phone_validator],
        label="Nagad number for payments (optional)",
        help_text="Customers who choose Nagad are asked to send money to this number.",
    )

    class Meta:
        model = Shop
        fields = (
            "name",
            "logo",
            "description",
            "category",
            "contact_phone",
            "contact_email",
            "delivery_charge",
            "bkash_number",
            "nagad_number",
        )
        labels = {"delivery_charge": "Delivery charge per order (৳)"}
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["delivery_charge"].required = False

    def clean_delivery_charge(self):
        charge = self.cleaned_data.get("delivery_charge")
        if charge is None:
            # Left empty: keep the current charge (or the default for a new shop).
            return self.instance.delivery_charge
        return charge