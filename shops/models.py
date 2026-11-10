from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class Shop(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop",
        limit_choices_to={"role": "seller"},
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to="shop_logos/", blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    is_published = models.BooleanField(default=False)
    delivery_charge = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("60.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("5000"))],
        help_text="Flat delivery charge for one order from this shop. Enter 0 for free delivery.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "shop"
            slug = base_slug
            counter = 2
            while Shop.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name