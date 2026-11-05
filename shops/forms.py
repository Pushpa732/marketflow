from django import forms

from .models import Shop


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ("name", "logo", "description", "category", "contact_phone", "contact_email")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"