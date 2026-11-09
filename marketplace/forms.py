from django import forms
from django.db.models import Q

from catalog.models import Category
from shops.models import Shop


class ProductFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        to_field_name="slug",
        required=False,
        empty_label="All categories",
    )
    shop = forms.ModelChoiceField(
        queryset=Shop.objects.none(),
        to_field_name="slug",
        required=False,
        empty_label="All shops",
    )
    min_price = forms.DecimalField(
        min_value=0, max_digits=10, decimal_places=2, required=False, label="Min price"
    )
    max_price = forms.DecimalField(
        min_value=0, max_digits=10, decimal_places=2, required=False, label="Max price"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = (
            Category.objects.filter(
                products__is_published=True, products__shop__is_published=True
            )
            .distinct()
            .order_by("name")
        )
        self.fields["shop"].queryset = Shop.objects.filter(is_published=True).order_by("name")

        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["shop"].widget.attrs["class"] = "form-select"
        self.fields["min_price"].widget.attrs.update({"class": "form-control", "placeholder": "Min ৳"})
        self.fields["max_price"].widget.attrs.update({"class": "form-control", "placeholder": "Max ৳"})

    def clean(self):
        cleaned_data = super().clean()
        low = cleaned_data.get("min_price")
        high = cleaned_data.get("max_price")
        if low is not None and high is not None and low > high:
            raise forms.ValidationError("Minimum price cannot be higher than maximum price.")
        return cleaned_data

    def filter_products(self, products):
        """Apply the chosen filters. Call this only when the form is valid."""
        data = self.cleaned_data

        category = data.get("category")
        if category:
            products = products.filter(Q(category=category) | Q(category__parent=category))

        shop = data.get("shop")
        if shop:
            products = products.filter(shop=shop)

        if data.get("min_price") is not None:
            products = products.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            products = products.filter(price__lte=data["max_price"])

        return products