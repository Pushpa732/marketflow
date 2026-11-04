from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        (User.Role.CUSTOMER, "Customer (I want to buy)"),
        (User.Role.SELLER, "Seller (I want to open a shop)"),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="I am a")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "phone", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        for name, field in self.fields.items():
            css_class = "form-select" if name == "role" else "form-control"
            field.widget.attrs["class"] = css_class