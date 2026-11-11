from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

transaction_id_validator = RegexValidator(
    regex=r"^[A-Za-z0-9]{6,20}$",
    message="Enter the transaction ID exactly as shown in your payment message (6 to 20 letters and numbers).",
)


class Payment(models.Model):
    class Method(models.TextChoices):
        COD = "cod", "Cash on delivery"
        BKASH = "bkash", "bKash"
        NAGAD = "nagad", "Nagad"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    method = models.CharField(max_length=10, choices=Method.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(
        max_length=30, blank=True, validators=[transaction_id_validator]
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["method", "transaction_id"],
                condition=~models.Q(transaction_id=""),
                name="unique_transaction_id_per_method",
            )
        ]

    def save(self, *args, **kwargs):
        if self.status == self.Status.PAID and self.paid_at is None:
            self.paid_at = timezone.now()
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = list(update_fields) + ["paid_at"]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order.order_number}: {self.get_method_display()} ({self.get_status_display()})"