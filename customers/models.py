from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models, transaction

MAX_ADDRESSES_PER_USER = 5

phone_validator = RegexValidator(
    regex=r"^(?:\+?88)?01[3-9][0-9]{8}$",
    message="Enter a valid Bangladesh mobile number, for example 01712345678.",
)


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "addresses"
        ordering = ["-is_default", "-created_at"]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # A customer always has exactly one default address.
            has_other_default = (
                Address.objects.filter(user=self.user, is_default=True)
                .exclude(pk=self.pk)
                .exists()
            )
            if not has_other_default:
                self.is_default = True

            super().save(*args, **kwargs)

            if self.is_default:
                Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}"