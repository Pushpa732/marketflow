from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Shop

PASSWORD = "StrongPass#2026"


class DeliveryChargeTests(TestCase):
    def setUp(self):
        seller = User.objects.create_user(username="seller", password=PASSWORD, role="seller")
        self.shop = Shop.objects.create(owner=seller, name="My Shop", description="Things")
        self.client.login(username="seller", password=PASSWORD)

    def save_profile(self, **changes):
        data = {"name": "My Shop", "description": "Things"}
        data.update(changes)
        return self.client.post(reverse("shops:shop_profile"), data)

    def charge(self):
        self.shop.refresh_from_db()
        return self.shop.delivery_charge

    def test_new_shops_start_with_the_default_charge(self):
        self.assertEqual(self.charge(), Decimal("60.00"))

    def test_seller_can_set_a_charge(self):
        self.save_profile(delivery_charge="80")
        self.assertEqual(self.charge(), Decimal("80.00"))

    def test_zero_means_free_delivery(self):
        self.save_profile(delivery_charge="0")
        self.assertEqual(self.charge(), Decimal("0.00"))

    def test_leaving_the_field_empty_keeps_the_current_charge(self):
        self.save_profile(delivery_charge="80")
        self.save_profile()
        self.assertEqual(self.charge(), Decimal("80.00"))

    def test_invalid_charges_are_rejected(self):
        for value in ["-5", "5001", "abc", "10.555"]:
            with self.subTest(value=value):
                response = self.save_profile(delivery_charge=value)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.charge(), Decimal("60.00"))