from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Product
from customers.models import Address
from shops.models import Shop

PASSWORD = "StrongPass#2026"


class CheckoutTestBase(TestCase):
    def setUp(self):
        seller1 = User.objects.create_user(username="seller1", password=PASSWORD, role="seller")
        seller2 = User.objects.create_user(username="seller2", password=PASSWORD, role="seller")
        self.customer = User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        self.other_customer = User.objects.create_user(
            username="other", password=PASSWORD, role="customer"
        )

        self.shop1 = Shop.objects.create(
            owner=seller1, name="Rahim Fashion", description="Clothes",
            is_published=True, delivery_charge=Decimal("60.00"),
        )
        self.shop2 = Shop.objects.create(
            owner=seller2, name="Karim Books", description="Books",
            is_published=True, delivery_charge=Decimal("100.00"),
        )
        self.shirt = Product.objects.create(
            shop=self.shop1, name="Blue T-Shirt", price=Decimal("450.00"), stock=10, is_published=True
        )
        self.novel = Product.objects.create(
            shop=self.shop2, name="Story Novel", price=Decimal("300.00"), stock=5, is_published=True
        )

        self.home = Address.objects.create(
            user=self.customer, full_name="Home", phone="01712345678",
            address_line="House 1", city="Dhaka",
        )
        self.office = Address.objects.create(
            user=self.customer, full_name="Office", phone="01812345678",
            address_line="Floor 3", city="Dhaka",
        )
        self.others_address = Address.objects.create(
            user=self.other_customer, full_name="Secret Person", phone="01912345678",
            address_line="Hidden Road", city="Khulna",
        )

        self.url = reverse("orders:checkout")

    def login(self, username="cust"):
        self.client.login(username=username, password=PASSWORD)

    def add(self, product, quantity=1):
        self.client.post(reverse("cart:add", args=[product.pk]), {"quantity": str(quantity)})


class CheckoutAccessTests(CheckoutTestBase):
    def test_visitor_is_sent_to_login_and_returns_to_checkout(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertIn("next=/checkout/", response.url)

    def test_seller_cannot_check_out(self):
        self.login("seller1")
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertContains(response, "customer account")

    def test_empty_cart_goes_back_to_the_cart_page(self):
        self.login()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("cart:detail"))

    def test_customer_with_items_sees_checkout(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blue T-Shirt")

    def test_cart_survives_the_login_step(self):
        self.add(self.shirt, 1)
        self.client.post(reverse("accounts:login"), {"username": "cust", "password": PASSWORD})
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class CheckoutTotalsTests(CheckoutTestBase):
    def test_each_shop_has_its_own_delivery_charge(self):
        self.login()
        self.add(self.shirt, 1)
        self.add(self.novel, 2)
        response = self.client.get(self.url)

        totals = {group["shop"].name: group["total"] for group in response.context["groups"]}
        self.assertEqual(
            totals,
            {"Rahim Fashion": Decimal("510.00"), "Karim Books": Decimal("700.00")},
        )

        summary = response.context["summary"]
        self.assertEqual(summary["items_total"], Decimal("1050.00"))
        self.assertEqual(summary["delivery_total"], Decimal("160.00"))
        self.assertEqual(summary["grand_total"], Decimal("1210.00"))

    def test_free_delivery_when_the_charge_is_zero(self):
        self.shop1.delivery_charge = Decimal("0.00")
        self.shop1.save()
        self.login()
        self.add(self.shirt, 1)
        response = self.client.get(self.url)
        self.assertEqual(response.context["summary"]["grand_total"], Decimal("450.00"))
        self.assertContains(response, "Free")

    def test_a_changed_delivery_charge_is_used_immediately(self):
        self.login()
        self.add(self.shirt, 1)
        self.shop1.delivery_charge = Decimal("80.00")
        self.shop1.save()
        response = self.client.get(self.url)
        self.assertEqual(response.context["summary"]["grand_total"], Decimal("530.00"))

    def test_item_that_became_unavailable_is_dropped(self):
        self.login()
        self.add(self.shirt, 1)
        self.shirt.is_published = False
        self.shirt.save()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("cart:detail"))


class CheckoutAddressTests(CheckoutTestBase):
    def test_default_address_is_preselected(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.client.get(self.url)
        self.assertEqual(response.context["selected_address_id"], self.home.pk)

    def test_another_own_address_can_be_selected(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.client.get(self.url, {"address": self.office.pk})
        self.assertEqual(response.context["selected_address_id"], self.office.pk)

    def test_another_customers_address_is_never_used_or_shown(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.client.get(self.url, {"address": self.others_address.pk})
        self.assertEqual(response.context["selected_address_id"], self.home.pk)
        self.assertNotContains(response, "Secret Person")

    def test_customer_without_an_address_is_asked_to_add_one(self):
        self.login("other")
        Address.objects.filter(user=self.other_customer).delete()
        self.add(self.shirt, 1)
        response = self.client.get(self.url)
        self.assertContains(response, "Add a delivery address")
        self.assertIsNone(response.context["selected_address_id"])