import re

from django import forms

from .models import Address, phone_validator


class PhoneField(forms.CharField):
    """A text field that removes spaces and hyphens before checking the number."""

    def to_python(self, value):
        value = super().to_python(value)
        return re.sub(r"[\s-]", "", value) if value else value


class AddressForm(forms.ModelForm):
    phone = PhoneField(max_length=20, validators=[phone_validator])

    class Meta:
        model = Address
        fields = ("full_name", "phone", "address_line", "city", "is_default")
        labels = {
            "address_line": "Address (house, road, area)",
            "is_default": "Use as my default address",
        }
        widgets = {"address_line": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "is_default":
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"