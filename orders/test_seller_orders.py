from decimal import Decimal

from django.urls import reverse

from accounts.models import User
from payments.models import Payment

from .models import Order, OrderItem
from .tests import CheckoutTestBase


class SellerOrderTestBase(CheckoutTestBase):
    def setUp(self):
        super().setUp()
        self.list_url = reverse("orders:seller_order_list")
        self.pending_a = self.make_order(self.shop1)
        self.confirmed_a = self.make_order(
            self.shop1,
            status=Order.Status.CONFIRMED,
            shipping_name="Rina Akter",
            phone="01912345678",
        )
        self.order_b = self.make_order(
            self.shop2,
            customer=self.other_customer,
            shipping_name="Secret Person",
            phone="01555555555",
        )

    def make_order(
        self,
        shop,
        customer=None,
        status=Order.Status.PENDING,
        shipping_name="Karim Uddin",
        phone="01812345678",
        method=Payment.Method.COD,
        transaction_id="",
        with_payment=True,
    ):
        order = Order.objects.create(
            customer=customer or self.customer,
            shop=shop,
            status=status,
            subtotal=Decimal("450.00"),
            delivery_charge=shop.delivery_charge,
            total=Decimal("450.00") + shop.delivery_charge,
            shipping_name=shipping_name,
            shipping_phone=phone,
            shipping_address="House 12, Road 5",
            shipping_city="Dhaka",
        )
        OrderItem.objects.create(
            order=order,
            product=None,
            product_name="Blue T-Shirt",
            unit_price=Decimal("450.00"),
            quantity=1,
        )
        if with_payment:
            Payment.objects.create(
                order=order, method=method, amount=order.total, transaction_id=transaction_id
            )
        return order

    def detail_url(self, order):
        return reverse("orders:seller_order_detail", args=[order.order_number])

    def tab_counts(self, response):
        return {tab["value"]: tab["count"] for tab in response.context["tabs"]}


class SellerOrderAccessTests(SellerOrderTestBase):
    def test_visitor_is_sent_to_login(self):
        for url in [self.list_url, self.detail_url(self.pending_a)]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("accounts:login"), response.url)

    def test_customer_cannot_open_seller_order_pages(self):
        self.login("cust")
        self.assertEqual(self.client.get(self.list_url).status_code, 403)
        self.assertEqual(self.client.get(self.detail_url(self.pending_a)).status_code, 403)

    def test_seller_without_a_shop_is_sent_to_create_one(self):
        User.objects.create_user(username="newseller", password="StrongPass#2026", role="seller")
        self.login("newseller")
        response = self.client.get(self.list_url)
        self.assertRedirects(response, reverse("shops:shop_profile"))


class SellerOrderListTests(SellerOrderTestBase):
    def test_seller_sees_only_the_orders_of_their_own_shop(self):
        self.login("seller1")
        response = self.client.get(self.list_url)
        self.assertContains(response, self.pending_a.order_number)
        self.assertContains(response, self.confirmed_a.order_number)
        self.assertNotContains(response, self.order_b.order_number)
        self.assertNotContains(response, "Secret Person")

    def test_the_other_seller_sees_only_their_own_order(self):
        self.login("seller2")
        response = self.client.get(self.list_url)
        self.assertContains(response, self.order_b.order_number)
        self.assertNotContains(response, self.pending_a.order_number)

    def test_newest_order_comes_first(self):
        self.login("seller1")
        response = self.client.get(self.list_url)
        self.assertEqual(list(response.context["page_obj"]), [self.confirmed_a, self.pending_a])

    def test_status_tabs_count_only_this_shops_orders(self):
        self.login("seller1")
        counts = self.tab_counts(self.client.get(self.list_url))
        self.assertEqual(counts[""], 2)
        self.assertEqual(counts["pending"], 1)
        self.assertEqual(counts["confirmed"], 1)
        self.assertEqual(counts["shipped"], 0)

    def test_status_filter_shows_only_that_status(self):
        self.login("seller1")
        response = self.client.get(self.list_url, {"status": "pending"})
        self.assertContains(response, self.pending_a.order_number)
        self.assertNotContains(response, self.confirmed_a.order_number)

    def test_tab_counts_do_not_change_with_the_filter(self):
        self.login("seller1")
        counts = self.tab_counts(self.client.get(self.list_url, {"status": "pending"}))
        self.assertEqual(counts[""], 2)

    def test_unknown_status_is_ignored(self):
        self.login("seller1")
        response = self.client.get(self.list_url, {"status": "hacker"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_status"], "")
        self.assertContains(response, self.pending_a.order_number)

    def test_search_by_order_number(self):
        self.login("seller1")
        response = self.client.get(self.list_url, {"q": self.pending_a.order_number[-6:]})
        self.assertContains(response, self.pending_a.order_number)
        self.assertNotContains(response, self.confirmed_a.order_number)

    def test_search_by_customer_name_and_phone(self):
        self.login("seller1")
        by_name = self.client.get(self.list_url, {"q": "Rina"})
        self.assertContains(by_name, self.confirmed_a.order_number)
        self.assertNotContains(by_name, self.pending_a.order_number)

        by_phone = self.client.get(self.list_url, {"q": "0191"})
        self.assertContains(by_phone, self.confirmed_a.order_number)
        self.assertNotContains(by_phone, self.pending_a.order_number)

    def test_search_never_finds_another_shops_orders(self):
        self.login("seller1")
        response = self.client.get(self.list_url, {"q": "Secret"})
        self.assertNotContains(response, self.order_b.order_number)
        self.assertContains(response, "No orders match")

    def test_search_and_status_work_together(self):
        self.login("seller1")
        response = self.client.get(self.list_url, {"q": "Karim", "status": "confirmed"})
        self.assertContains(response, "No orders match")

    def test_very_long_search_does_not_crash(self):
        self.login("seller1")
        response = self.client.get(self.list_url, {"q": "a" * 500})
        self.assertEqual(response.status_code, 200)

    def test_orders_are_paged_and_paging_keeps_the_filter(self):
        for _ in range(11):
            self.make_order(self.shop1)
        self.login("seller1")
        page1 = self.client.get(self.list_url, {"status": "pending"})
        page2 = self.client.get(self.list_url, {"status": "pending", "page": 2})
        self.assertEqual(len(page1.context["page_obj"]), 10)
        self.assertEqual(len(page2.context["page_obj"]), 2)
        self.assertContains(page1, "status=pending&amp;page=2")

    def test_order_without_a_payment_record_is_listed(self):
        order = self.make_order(self.shop1, with_payment=False)
        self.login("seller1")
        response = self.client.get(self.list_url)
        self.assertContains(response, order.order_number)

    def test_empty_shop_shows_a_message(self):
        Order.objects.filter(shop=self.shop2).delete()
        self.login("seller2")
        response = self.client.get(self.list_url)
        self.assertContains(response, "has no orders yet")


class SellerOrderDetailTests(SellerOrderTestBase):
    def test_seller_can_open_own_order(self):
        self.login("seller1")
        response = self.client.get(self.detail_url(self.pending_a))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pending_a.order_number)
        self.assertContains(response, "Blue T-Shirt")
        self.assertContains(response, "Karim Uddin")
        self.assertContains(response, "House 12, Road 5")
        self.assertContains(response, "01812345678")
        self.assertContains(response, "Cash on delivery")
        self.assertContains(response, "Pending")

    def test_seller_cannot_open_another_shops_order(self):
        self.login("seller1")
        response = self.client.get(self.detail_url(self.order_b))
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, "Secret Person", status_code=404)

    def test_unknown_order_number_is_not_found(self):
        self.login("seller1")
        url = reverse("orders:seller_order_detail", args=["MF-000000-AAAAAA"])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_transaction_id_is_shown_to_the_seller(self):
        order = self.make_order(
            self.shop1, method=Payment.Method.BKASH, transaction_id="8N7A6D5EE7"
        )
        self.login("seller1")
        response = self.client.get(self.detail_url(order))
        self.assertContains(response, "8N7A6D5EE7")
        self.assertContains(response, "bKash")

    def test_missing_transaction_id_is_explained(self):
        order = self.make_order(self.shop1, method=Payment.Method.NAGAD)
        self.login("seller1")
        response = self.client.get(self.detail_url(order))
        self.assertContains(response, "has not entered a transaction ID")

    def test_order_without_a_payment_record_still_opens(self):
        order = self.make_order(self.shop1, with_payment=False)
        self.login("seller1")
        self.assertEqual(self.client.get(self.detail_url(order)).status_code, 200)


class PendingOrderCountTests(SellerOrderTestBase):
    def test_count_includes_only_pending_orders_of_the_shop(self):
        self.assertEqual(self.shop1.pending_order_count, 1)
        self.assertEqual(self.shop2.pending_order_count, 1)

    def test_dashboard_alert_appears_and_disappears(self):
        self.login("seller1")
        dashboard = reverse("shops:seller_dashboard")
        self.assertContains(self.client.get(dashboard), "waiting for your attention")

        Order.objects.filter(pk=self.pending_a.pk).update(status=Order.Status.CONFIRMED)
        self.assertNotContains(self.client.get(dashboard), "waiting for your attention")