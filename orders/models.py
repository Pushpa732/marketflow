import secrets
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

# No 0, 1, I, or O, because they are easy to confuse when read aloud or typed.
ORDER_NUMBER_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_order_number():
    """Create a unique, hard-to-guess order number such as MF-261110-K7M2QX."""
    while True:
        random_part = "".join(secrets.choice(ORDER_NUMBER_CHARS) for _ in range(6))
        number = f"MF-{timezone.localdate():%y%m%d}-{random_part}"
        if not Order.objects.filter(order_number=number).exists():
            return number


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    order_number = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    shop = models.ForeignKey(
        "shops.Shop",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    # Money, copied at the moment the order is placed.
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge = models.DecimalField(max_digits=7, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Delivery details, copied from the customer's chosen address.
    shipping_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["shop", "status"])]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    # Copied at the moment the order is placed.
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_item_quantity_at_least_one",
            )
        ]

    @property
    def line_total(self):
        if self.unit_price is None or self.quantity is None:
            return Decimal("0.00")
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"