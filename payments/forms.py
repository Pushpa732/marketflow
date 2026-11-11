import re

from django import forms

from .models import transaction_id_validator


class TransactionIdField(forms.CharField):
    """Removes spaces and capitalizes the ID before it is checked."""

    def to_python(self, value):
        value = super().to_python(value)
        return re.sub(r"\s", "", value).upper() if value else value


class TransactionIdForm(forms.Form):
    transaction_id = TransactionIdField(
        max_length=30,
        validators=[transaction_id_validator],
        label="Transaction ID",
    )