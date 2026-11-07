from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "description",
            "price",
            "stock",
            "low_stock_threshold",
            "is_published",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        labels = {
            "low_stock_threshold": "Low-stock alert level",
            "is_published": "Publish this product (visible to customers)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "is_published":
                field.widget.attrs["class"] = "form-check-input"
            elif name == "category":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"
        self.fields["category"].empty_label = "Choose a category"