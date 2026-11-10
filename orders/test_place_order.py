from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse

from catalog.models import Product

from .models import Order, OrderItem
from .tests import CheckoutTestBase


class PlaceOrderTestBase(CheckoutTestBase):
    def place(self, address=None, expected_total="auto", follow=False, **extra):
        """Open checkout, then press Place order the way a browser would."""
        if expected_total == "auto":
            page = self.client.get(self.url)
            expected_total = str(page.context["summary"]["grand_total"])
        data = {"address": str((address or self.home).pk), "expected_total": expected_total}
        data.update(extra)
        return self.client.post(self.url, data, follow=follow)

    def session_cart(self):
        return self.client.session.get("cart", {})


class PlaceOrderTests(PlaceOrderTestBase):
    def test_customer_can_place_an_order_for_one_shop(self):
        self.login()
        self.add(self.shirt, 2)
        response = self.place()
        self.assertRedirects(response, reverse("orders:order_list"))

        order = Order.objects.get()
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.shop, self.shop1)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.subtotal, Decimal("900.00"))
        self.assertEqual(order.delivery_charge, Decimal("60.00"))
        self.assertEqual(order.total, Decimal("960.00"))

        item = order.items.get()
        self.assertEqual(item.product, self.shirt)
        self.assertEqual(item.product_name, "Blue T-Shirt")
        self.assertEqual(item.unit_price, Decimal("450.00"))
        self.assertEqual(item.quantity, 2)

    def test_the_delivery_address_is_copied_into_the_order(self):
        self.login()
        self.add(self.shirt, 1)
        self.place(address=self.office)
        order = Order.objects.get()
        self.assertEqual(order.shipping_name, "Office")
        self.assertEqual(order.shipping_phone, "01812345678")
        self.assertEqual(order.shipping_address, "Floor 3")
        self.assertEqual(order.shipping_city, "Dhaka")

    def test_editing_the_address_later_does_not_change_the_order(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        self.home.city = "Sylhet"
        self.home.save()
        self.assertEqual(Order.objects.get().shipping_city, "Dhaka")

    def test_cart_is_empty_after_ordering(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        self.assertEqual(self.session_cart(), {})

    def test_cart_with_two_shops_creates_two_orders(self):
        self.login()
        self.add(self.shirt, 1)
        self.add(self.novel, 2)
        self.place()

        orders = {order.shop.name: order for order in Order.objects.all()}
        self.assertEqual(set(orders), {"Rahim Fashion", "Karim Books"})
        self.assertEqual(orders["Rahim Fashion"].total, Decimal("510.00"))
        self.assertEqual(orders["Karim Books"].total, Decimal("700.00"))
        self.assertEqual(
            [item.product_name for item in orders["Rahim Fashion"].items.all()], ["Blue T-Shirt"]
        )
        self.assertEqual(
            [item.product_name for item in orders["Karim Books"].items.all()], ["Story Novel"]
        )

    def test_each_order_gets_its_own_order_number(self):
        self.login()
        self.add(self.shirt, 1)
        self.add(self.novel, 1)
        self.place()
        numbers = set(Order.objects.values_list("order_number", flat=True))
        self.assertEqual(len(numbers), 2)

    def test_stock_is_not_reduced_when_the_order_is_placed(self):
        self.login()
        self.add(self.shirt, 3)
        self.place()
        self.shirt.refresh_from_db()
        self.assertEqual(self.shirt.stock, 10)

    def test_order_keeps_the_old_price_when_the_seller_changes_it(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        self.shirt.price = Decimal("999.00")
        self.shirt.save()
        item = OrderItem.objects.get()
        self.assertEqual(item.unit_price, Decimal("450.00"))

    def test_prices_and_totals_sent_by_the_browser_are_ignored(self):
        self.login()
        self.add(self.shirt, 2)
        self.place(total="1", subtotal="1", delivery_charge="0", price="1")
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("960.00"))
        self.assertEqual(order.delivery_charge, Decimal("60.00"))

    def test_success_message_is_shown(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.place(follow=True)
        self.assertContains(response, "Thank you")


class PlaceOrderRefusalTests(PlaceOrderTestBase):
    def test_another_customers_address_cannot_be_used(self):
        self.login()
        self.add(self.shirt, 1)
        self.place(address=self.others_address)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 1})

    def test_an_address_is_required(self):
        self.login()
        self.add(self.shirt, 1)
        self.client.post(self.url, {"expected_total": "510.00"})
        self.assertEqual(Order.objects.count(), 0)

    def test_the_total_the_customer_saw_must_match(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.place(expected_total="1.00", follow=True)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, "Prices or delivery charges changed")

    def test_missing_total_is_refused(self):
        self.login()
        self.add(self.shirt, 1)
        self.place(expected_total="")
        self.assertEqual(Order.objects.count(), 0)

    def test_price_change_while_on_the_checkout_page_stops_the_order(self):
        self.login()
        self.add(self.shirt, 1)
        page = self.client.get(self.url)
        seen_total = str(page.context["summary"]["grand_total"])

        self.shirt.price = Decimal("600.00")
        self.shirt.save()

        self.place(expected_total=seen_total)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.session_cart(), {str(self.shirt.pk): 1})

    def test_stock_that_dropped_stops_the_order_and_corrects_the_cart(self):
        self.login()
        self.add(self.novel, 5)
        Product.objects.filter(pk=self.novel.pk).update(stock=2)
        self.place(expected_total="1")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.session_cart(), {str(self.novel.pk): 2})

    def test_product_that_was_unpublished_stops_the_order(self):
        self.login()
        self.add(self.shirt, 1)
        self.shirt.is_published = False
        self.shirt.save()
        response = self.place(expected_total="1")
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(Order.objects.count(), 0)

    def test_empty_cart_cannot_place_an_order(self):
        self.login()
        response = self.place(expected_total="0")
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(Order.objects.count(), 0)

    def test_visitor_cannot_place_an_order(self):
        response = self.client.post(self.url, {"address": str(self.home.pk), "expected_total": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertEqual(Order.objects.count(), 0)

    def test_seller_cannot_place_an_order(self):
        self.login("seller1")
        response = self.client.post(self.url, {"address": str(self.home.pk), "expected_total": "1"})
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(Order.objects.count(), 0)

    def test_double_submit_creates_only_one_order(self):
        self.login()
        self.add(self.shirt, 1)
        self.place(expected_total="510.00")
        self.place(expected_total="510.00")
        self.assertEqual(Order.objects.count(), 1)

    def test_a_failure_in_the_middle_saves_nothing(self):
        self.login()
        self.add(self.shirt, 1)
        self.add(self.novel, 1)
        self.client.raise_request_exception = False

        with patch.object(OrderItem.objects, "bulk_create", side_effect=RuntimeError("boom")):
            response = self.place()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(len(self.session_cart()), 2)