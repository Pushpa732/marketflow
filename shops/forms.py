from django import forms

from .models import Shop


class ShopForm(forms.ModelForm):
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