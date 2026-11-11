from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from orders.models import Order
from orders.test_place_order import PlaceOrderTestBase
from orders.tests import CheckoutTestBase

from .models import Payment, transaction_id_validator

BKASH_NUMBER = "01711111111"
NAGAD_NUMBER = "01822222222"


class PaymentModelTests(CheckoutTestBase):
    def make_order(self, customer=None, shop=None):
        return Order.objects.create(
            customer=customer or self.customer,
            shop=shop or self.shop1,
            subtotal=Decimal("450.00"),
            delivery_charge=Decimal("60.00"),
            total=Decimal("510.00"),
            shipping_name="Home",
            shipping_phone="01712345678",
            shipping_address="House 1",
            shipping_city="Dhaka",
        )

    def make_payment(self, order=None, method=Payment.Method.BKASH, transaction_id=""):
        return Payment.objects.create(
            order=order or self.make_order(),
            method=method,
            amount=Decimal("510.00"),
            transaction_id=transaction_id,
        )

    def test_new_payment_is_pending_and_has_no_paid_time(self):
        payment = self.make_payment()
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertIsNone(payment.paid_at)

    def test_paid_time_is_set_when_marked_paid(self):
        payment = self.make_payment()
        payment.status = Payment.Status.PAID
        payment.save()
        payment.refresh_from_db()
        self.assertIsNotNone(payment.paid_at)

    def test_an_order_has_only_one_payment(self):
        order = self.make_order()
        self.make_payment(order)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_payment(order)

    def test_transaction_id_can_be_used_only_once_per_method(self):
        self.make_payment(transaction_id="8N7A6D5EE7")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_payment(transaction_id="8N7A6D5EE7")

    def test_same_transaction_id_is_allowed_for_a_different_method(self):
        self.make_payment(method=Payment.Method.BKASH, transaction_id="8N7A6D5EE7")
        self.make_payment(method=Payment.Method.NAGAD, transaction_id="8N7A6D5EE7")
        self.assertEqual(Payment.objects.count(), 2)

    def test_many_payments_can_have_no_transaction_id(self):
        self.make_payment(method=Payment.Method.COD)
        self.make_payment(method=Payment.Method.COD)
        self.assertEqual(Payment.objects.count(), 2)

    def test_transaction_id_format(self):
        transaction_id_validator("8N7A6D5EE7")
        for bad in ["abc", "ab-cd-ef-gh", "x" * 21, "৩৪৫৬৭৮", "AB CD EF GH"]:
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    transaction_id_validator(bad)


class ShopPaymentNumberTests(CheckoutTestBase):
    def test_cash_on_delivery_is_always_accepted(self):
        self.assertTrue(self.shop1.accepts_payment_method("cod"))

    def test_bkash_and_nagad_need_a_number(self):
        self.assertFalse(self.shop1.accepts_payment_method("bkash"))
        self.assertFalse(self.shop1.accepts_payment_method("nagad"))
        self.shop1.bkash_number = BKASH_NUMBER
        self.shop1.nagad_number = NAGAD_NUMBER
        self.assertTrue(self.shop1.accepts_payment_method("bkash"))
        self.assertTrue(self.shop1.accepts_payment_method("nagad"))

    def test_unknown_method_is_not_accepted(self):
        self.assertFalse(self.shop1.accepts_payment_method("paypal"))

    def save_profile(self, **changes):
        data = {"name": "Rahim Fashion", "description": "Clothes"}
        data.update(changes)
        return self.client.post(reverse("shops:shop_profile"), data)

    def test_seller_can_save_payment_numbers(self):
        self.login("seller1")
        self.save_profile(bkash_number="017-1111 1111", nagad_number=NAGAD_NUMBER)
        self.shop1.refresh_from_db()
        self.assertEqual(self.shop1.bkash_number, BKASH_NUMBER)
        self.assertEqual(self.shop1.nagad_number, NAGAD_NUMBER)

    def test_invalid_payment_number_is_rejected(self):
        self.login("seller1")
        response = self.save_profile(bkash_number="12345")
        self.assertEqual(response.status_code, 200)
        self.shop1.refresh_from_db()
        self.assertEqual(self.shop1.bkash_number, "")

    def test_leaving_the_number_empty_is_allowed(self):
        self.login("seller1")
        self.save_profile(bkash_number="")
        self.shop1.refresh_from_db()
        self.assertEqual(self.shop1.bkash_number, "")


class PlaceOrderWithPaymentTests(PlaceOrderTestBase):
    def enable_digital_payments(self, *shops):
        for shop in shops:
            shop.bkash_number = BKASH_NUMBER
            shop.nagad_number = NAGAD_NUMBER
            shop.save()

    def test_cash_on_delivery_is_the_default(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        order = Order.objects.get()
        payment = Payment.objects.get()
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.method, Payment.Method.COD)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, order.total)
        self.assertEqual(payment.transaction_id, "")

    def test_bkash_order_gets_a_bkash_payment(self):
        self.enable_digital_payments(self.shop1)
        self.login()
        self.add(self.shirt, 1)
        self.place(payment_method="bkash")
        self.assertEqual(Payment.objects.get().method, Payment.Method.BKASH)

    def test_method_is_refused_when_the_shop_has_no_number(self):
        self.login()
        self.add(self.shirt, 1)
        response = self.place(payment_method="bkash", follow=True)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertContains(response, "does not accept bKash")

    def test_one_shop_without_a_number_blocks_the_whole_checkout(self):
        self.enable_digital_payments(self.shop1)  # shop2 has no numbers
        self.login()
        self.add(self.shirt, 1)
        self.add(self.novel, 1)
        self.place(payment_method="nagad")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_two_shops_get_two_payments_with_the_same_method(self):
        self.enable_digital_payments(self.shop1, self.shop2)
        self.login()
        self.add(self.shirt, 1)
        self.add(self.novel, 1)
        self.place(payment_method="nagad")
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(
            set(Payment.objects.values_list("method", flat=True)), {Payment.Method.NAGAD}
        )

    def test_unknown_payment_method_is_refused(self):
        self.login()
        self.add(self.shirt, 1)
        self.place(payment_method="paypal")
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_page_shows_which_methods_are_available(self):
        self.login()
        self.add(self.shirt, 1)
        options = {
            option["value"]: option
            for option in self.client.get(self.url).context["payment_options"]
        }
        self.assertTrue(options["cod"]["available"])
        self.assertFalse(options["bkash"]["available"])
        self.assertEqual(options["bkash"]["blocking_shops"], ["Rahim Fashion"])

        self.enable_digital_payments(self.shop1)
        options = {
            option["value"]: option
            for option in self.client.get(self.url).context["payment_options"]
        }
        self.assertTrue(options["bkash"]["available"])
        self.assertTrue(options["nagad"]["available"])


class SubmitTransactionIdTests(PlaceOrderTestBase):
    def setUp(self):
        super().setUp()
        self.shop1.bkash_number = BKASH_NUMBER
        self.shop1.save()

    def make_bkash_order(self):
        self.login()
        self.add(self.shirt, 1)
        self.place(payment_method="bkash")
        return Order.objects.get()

    def submit(self, order, value):
        url = reverse("payments:submit_transaction_id", args=[order.order_number])
        return self.client.post(url, {"transaction_id": value})

    def transaction_id(self, order):
        return Payment.objects.get(order=order).transaction_id

    def test_customer_can_submit_a_transaction_id(self):
        order = self.make_bkash_order()
        response = self.submit(order, "8n7a 6d5e e7")
        self.assertRedirects(
            response, reverse("orders:order_detail", args=[order.order_number])
        )
        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.transaction_id, "8N7A6D5EE7")
        self.assertEqual(payment.status, Payment.Status.PENDING)

    def test_invalid_ids_are_rejected(self):
        order = self.make_bkash_order()
        for value in ["abc", "ab-cd-ef-gh", "", "x" * 40]:
            with self.subTest(value=value):
                self.submit(order, value)
                self.assertEqual(self.transaction_id(order), "")

    def test_id_can_be_corrected_while_pending(self):
        order = self.make_bkash_order()
        self.submit(order, "AAAAAA1111")
        self.submit(order, "BBBBBB2222")
        self.assertEqual(self.transaction_id(order), "BBBBBB2222")

    def test_id_already_used_for_another_order_is_rejected(self):
        order = self.make_bkash_order()
        other_order = Order.objects.create(
            customer=self.other_customer,
            shop=self.shop1,
            subtotal=Decimal("450.00"),
            delivery_charge=Decimal("60.00"),
            total=Decimal("510.00"),
            shipping_name="Other",
            shipping_phone="01912345678",
            shipping_address="Road 9",
            shipping_city="Khulna",
        )
        Payment.objects.create(
            order=other_order,
            method=Payment.Method.BKASH,
            amount=Decimal("510.00"),
            transaction_id="8N7A6D5EE7",
        )
        response = self.client.post(
            reverse("payments:submit_transaction_id", args=[order.order_number]),
            {"transaction_id": "8N7A6D5EE7"},
            follow=True,
        )
        self.assertContains(response, "already been used")
        self.assertEqual(self.transaction_id(order), "")

    def test_cash_on_delivery_order_does_not_take_a_transaction_id(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        order = Order.objects.get()
        self.submit(order, "8N7A6D5EE7")
        self.assertEqual(self.transaction_id(order), "")

    def test_id_is_locked_after_the_seller_marks_the_payment(self):
        order = self.make_bkash_order()
        Payment.objects.filter(order=order).update(status=Payment.Status.PAID)
        self.submit(order, "8N7A6D5EE7")
        self.assertEqual(self.transaction_id(order), "")

    def test_id_cannot_be_added_to_a_rejected_order(self):
        order = self.make_bkash_order()
        Order.objects.filter(pk=order.pk).update(status=Order.Status.REJECTED)
        self.submit(order, "8N7A6D5EE7")
        self.assertEqual(self.transaction_id(order), "")

    def test_another_customer_cannot_submit_for_this_order(self):
        order = self.make_bkash_order()
        self.client.logout()
        self.login("other")
        response = self.submit(order, "8N7A6D5EE7")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.transaction_id(order), "")

    def test_visitor_is_sent_to_login(self):
        order = self.make_bkash_order()
        self.client.logout()
        response = self.submit(order, "8N7A6D5EE7")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_seller_cannot_submit(self):
        order = self.make_bkash_order()
        self.client.logout()
        self.login("seller1")
        self.assertEqual(self.submit(order, "8N7A6D5EE7").status_code, 403)

    def test_submitting_requires_a_post_request(self):
        order = self.make_bkash_order()
        url = reverse("payments:submit_transaction_id", args=[order.order_number])
        self.assertEqual(self.client.get(url).status_code, 405)


class OrderPagePaymentTests(PlaceOrderTestBase):
    def test_bkash_order_page_shows_the_sellers_number_and_instructions(self):
        self.shop1.bkash_number = BKASH_NUMBER
        self.shop1.save()
        self.login()
        self.add(self.shirt, 1)
        self.place(payment_method="bkash")
        order = Order.objects.get()
        response = self.client.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertContains(response, BKASH_NUMBER)
        self.assertContains(response, "transaction ID")
        self.assertContains(response, "Never share your PIN")

    def test_cash_on_delivery_order_page_shows_the_cash_message(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        order = Order.objects.get()
        response = self.client.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertContains(response, "Cash on delivery")
        self.assertContains(response, "in cash when your order is delivered")

    def test_paid_order_page_shows_confirmation(self):
        self.login()
        self.add(self.shirt, 1)
        self.place()
        order = Order.objects.get()
        Payment.objects.filter(order=order).update(
            method=Payment.Method.BKASH, status=Payment.Status.PAID
        )
        response = self.client.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertContains(response, "Payment confirmed")

    def test_old_order_without_a_payment_record_still_opens(self):
        order = Order.objects.create(
            customer=self.customer,
            shop=self.shop1,
            subtotal=Decimal("450.00"),
            delivery_charge=Decimal("60.00"),
            total=Decimal("510.00"),
            shipping_name="Home",
            shipping_phone="01712345678",
            shipping_address="House 1",
            shipping_city="Dhaka",
        )
        self.login()
        response = self.client.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertEqual(response.status_code, 200)