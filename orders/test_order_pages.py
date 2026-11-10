from decimal import Decimal

from django.urls import reverse

from .models import Order, OrderItem
from .tests import CheckoutTestBase


class OrderPagesTestBase(CheckoutTestBase):
    def make_order(self, customer=None, shop=None, name="Blue T-Shirt", price="450.00"):
        order = Order.objects.create(
            customer=customer or self.customer,
            shop=shop or self.shop1,
            subtotal=Decimal(price),
            delivery_charge=Decimal("60.00"),
            total=Decimal(price) + Decimal("60.00"),
            shipping_name="Home",
            shipping_phone="01712345678",
            shipping_address="House 1",
            shipping_city="Dhaka",
        )
        OrderItem.objects.create(
            order=order,
            product=self.shirt,
            product_name=name,
            unit_price=Decimal(price),
            quantity=1,
        )
        return order

    def detail_url(self, order):
        return reverse("orders:order_detail", args=[order.order_number])


class OrderAccessTests(OrderPagesTestBase):
    def test_visitor_is_sent_to_login(self):
        order = self.make_order()
        for url in [reverse("orders:order_list"), self.detail_url(order)]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("accounts:login"), response.url)

    def test_seller_cannot_open_customer_order_pages(self):
        order = self.make_order()
        self.login("seller1")
        self.assertEqual(self.client.get(reverse("orders:order_list")).status_code, 403)
        self.assertEqual(self.client.get(self.detail_url(order)).status_code, 403)


class OrderListTests(OrderPagesTestBase):
    def test_customer_sees_only_own_orders(self):
        own = self.make_order()
        other = self.make_order(customer=self.other_customer)
        self.login()
        response = self.client.get(reverse("orders:order_list"))
        self.assertContains(response, own.order_number)
        self.assertNotContains(response, other.order_number)

    def test_newest_order_comes_first(self):
        first = self.make_order()
        second = self.make_order()
        self.login()
        response = self.client.get(reverse("orders:order_list"))
        self.assertEqual(list(response.context["page_obj"]), [second, first])

    def test_empty_history_shows_a_message(self):
        self.login()
        response = self.client.get(reverse("orders:order_list"))
        self.assertContains(response, "You have not placed any orders yet")


class OrderDetailTests(OrderPagesTestBase):
    def test_customer_can_open_own_order(self):
        order = self.make_order()
        self.login()
        response = self.client.get(self.detail_url(order))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blue T-Shirt")
        self.assertContains(response, "510.00")
        self.assertContains(response, "House 1")
        self.assertContains(response, "Pending")

    def test_order_shows_the_price_paid_not_todays_price(self):
        order = self.make_order()
        self.shirt.price = Decimal("999.00")
        self.shirt.name = "Renamed Shirt"
        self.shirt.save()
        self.login()
        response = self.client.get(self.detail_url(order))
        self.assertContains(response, "450.00")
        self.assertContains(response, "Blue T-Shirt")
        self.assertNotContains(response, "999.00")
        self.assertNotContains(response, "Renamed Shirt")

    def test_another_customers_order_is_not_found(self):
        order = self.make_order(customer=self.other_customer)
        self.login()
        self.assertEqual(self.client.get(self.detail_url(order)).status_code, 404)

    def test_unknown_order_number_is_not_found(self):
        self.login()
        response = self.client.get(reverse("orders:order_detail", args=["MF-000000-AAAAAA"]))
        self.assertEqual(response.status_code, 404)