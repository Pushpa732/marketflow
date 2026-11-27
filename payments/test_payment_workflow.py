from django.urls import reverse

from orders.models import Order
from orders.test_seller_orders import SellerOrderTestBase

from .models import Payment
from .services import (
    PaymentActionError,
    apply_payment_action,
    available_payment_actions,
    check_payment_action,
)


class PaymentActionTestBase(SellerOrderTestBase):
    def act(self, order, action, follow=False):
        url = reverse("payments:seller_payment_action", args=[order.order_number])
        return self.client.post(url, {"action": action}, follow=follow)

    def bkash_order(self, transaction_id="8N7A6D5EE7", **extra):
        return self.make_order(
            self.shop1, method=Payment.Method.BKASH, transaction_id=transaction_id, **extra
        )

    def cod_order(self, **extra):
        return self.make_order(self.shop1, method=Payment.Method.COD, **extra)

    def payment(self, order):
        return Payment.objects.get(order=order)

    def set_payment(self, order, status):
        Payment.objects.filter(order=order).update(status=status)

    def order_status(self, order):
        order.refresh_from_db()
        return order.status

    def detail(self, order):
        return self.client.get(self.detail_url(order))


class MarkAsPaidTests(PaymentActionTestBase):
    def test_bkash_payment_with_a_transaction_id_can_be_marked_paid(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "paid")
        payment = self.payment(order)
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertIsNotNone(payment.paid_at)

    def test_bkash_payment_without_a_transaction_id_cannot_be_marked_paid(self):
        order = self.bkash_order(transaction_id="")
        self.login("seller1")
        response = self.act(order, "paid", follow=True)
        self.assertContains(response, "has not entered a transaction ID")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_nagad_payment_follows_the_same_rule(self):
        order = self.make_order(self.shop1, method=Payment.Method.NAGAD)
        self.login("seller1")
        self.act(order, "paid")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_cash_on_delivery_cannot_be_marked_paid_before_shipping(self):
        for status in [Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.PROCESSING]:
            with self.subTest(status=status):
                order = self.cod_order(status=status)
                self.login("seller1")
                response = self.act(order, "paid", follow=True)
                self.assertContains(response, "after the order is shipped")
                self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_cash_on_delivery_can_be_marked_paid_after_shipping(self):
        self.login("seller1")
        for status in [Order.Status.SHIPPED, Order.Status.COMPLETED]:
            with self.subTest(status=status):
                order = self.cod_order(status=status)
                self.act(order, "paid")
                self.assertEqual(self.payment(order).status, Payment.Status.PAID)

    def test_rejected_or_cancelled_order_cannot_be_marked_paid(self):
        self.login("seller1")
        for status in [Order.Status.REJECTED, Order.Status.CANCELLED]:
            with self.subTest(status=status):
                order = self.bkash_order(status=status)
                self.act(order, "paid")
                self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_a_paid_payment_cannot_be_marked_paid_again(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "paid")
        paid_time = self.payment(order).paid_at
        self.act(order, "paid")
        self.assertEqual(self.payment(order).paid_at, paid_time)


class FailRefundReopenTests(PaymentActionTestBase):
    def test_pending_payment_can_be_marked_failed(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "failed")
        self.assertEqual(self.payment(order).status, Payment.Status.FAILED)

    def test_failed_payment_cannot_be_marked_paid_directly(self):
        order = self.bkash_order()
        self.set_payment(order, Payment.Status.FAILED)
        self.login("seller1")
        self.act(order, "paid")
        self.assertEqual(self.payment(order).status, Payment.Status.FAILED)

    def test_failed_payment_can_be_reopened(self):
        order = self.bkash_order()
        self.set_payment(order, Payment.Status.FAILED)
        self.login("seller1")
        self.act(order, "reopen")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_pending_payment_cannot_be_reopened(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "reopen")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_reopened_order_lets_the_customer_correct_the_transaction_id(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "failed")

        # While the payment is failed, the customer cannot change the ID.
        self.client.logout()
        self.login("cust")
        submit = reverse("payments:submit_transaction_id", args=[order.order_number])
        self.client.post(submit, {"transaction_id": "CCCCCC3333"})
        self.assertEqual(self.payment(order).transaction_id, "8N7A6D5EE7")

        # After the seller reopens it, the customer can.
        self.client.logout()
        self.login("seller1")
        self.act(order, "reopen")
        self.client.logout()
        self.login("cust")
        self.client.post(submit, {"transaction_id": "CCCCCC3333"})
        self.assertEqual(self.payment(order).transaction_id, "CCCCCC3333")

    def test_closed_order_payment_cannot_be_reopened(self):
        order = self.bkash_order(status=Order.Status.REJECTED)
        self.set_payment(order, Payment.Status.FAILED)
        self.login("seller1")
        self.act(order, "reopen")
        self.assertEqual(self.payment(order).status, Payment.Status.FAILED)

    def test_paid_payment_can_be_refunded_and_keeps_its_paid_time(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "paid")
        paid_time = self.payment(order).paid_at
        self.act(order, "refunded")
        payment = self.payment(order)
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
        self.assertEqual(payment.paid_at, paid_time)

    def test_pending_payment_cannot_be_refunded(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "refunded")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_paid_payment_cannot_be_marked_failed(self):
        order = self.bkash_order()
        self.set_payment(order, Payment.Status.PAID)
        self.login("seller1")
        self.act(order, "failed")
        self.assertEqual(self.payment(order).status, Payment.Status.PAID)

    def test_refunded_payment_cannot_be_changed(self):
        order = self.bkash_order()
        self.set_payment(order, Payment.Status.REFUNDED)
        self.login("seller1")
        for action in ["paid", "failed", "refunded", "reopen"]:
            with self.subTest(action=action):
                self.act(order, action)
                self.assertEqual(self.payment(order).status, Payment.Status.REFUNDED)

    def test_payment_of_a_rejected_order_can_be_failed_or_refunded(self):
        self.login("seller1")
        pending = self.bkash_order(status=Order.Status.REJECTED)
        self.act(pending, "failed")
        self.assertEqual(self.payment(pending).status, Payment.Status.FAILED)

        paid = self.bkash_order(transaction_id="AAAAAA1111", status=Order.Status.REJECTED)
        self.set_payment(paid, Payment.Status.PAID)
        self.act(paid, "refunded")
        self.assertEqual(self.payment(paid).status, Payment.Status.REFUNDED)


class SeparationAndAccessTests(PaymentActionTestBase):
    def test_changing_the_payment_never_changes_the_order_status(self):
        order = self.bkash_order(status=Order.Status.CONFIRMED)
        self.login("seller1")
        for action in ["paid", "refunded"]:
            self.act(order, action)
            self.assertEqual(self.order_status(order), Order.Status.CONFIRMED)

    def test_unknown_action_is_refused(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "delete")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_order_without_a_payment_record_is_handled(self):
        order = self.make_order(self.shop1, with_payment=False)
        self.login("seller1")
        response = self.act(order, "paid", follow=True)
        self.assertContains(response, "no payment record")

    def test_another_seller_cannot_change_the_payment(self):
        order = self.bkash_order()
        self.login("seller2")
        response = self.act(order, "paid")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_customer_cannot_use_seller_payment_actions(self):
        order = self.bkash_order()
        self.login("cust")
        self.assertEqual(self.act(order, "paid").status_code, 403)
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)

    def test_visitor_is_sent_to_login(self):
        order = self.bkash_order()
        response = self.act(order, "paid")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_actions_require_a_post_request(self):
        order = self.bkash_order()
        self.login("seller1")
        url = reverse("payments:seller_payment_action", args=[order.order_number])
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_service_function_refuses_the_wrong_shop(self):
        order = self.bkash_order()
        with self.assertRaises(PaymentActionError):
            apply_payment_action(order.pk, self.shop2, "paid")
        self.assertEqual(self.payment(order).status, Payment.Status.PENDING)


class RulesAndPageTests(PaymentActionTestBase):
    def test_rules_return_an_explanation_or_nothing(self):
        order = self.bkash_order(transaction_id="")
        payment = self.payment(order)
        self.assertIn("transaction ID", check_payment_action(payment, order, "paid"))
        self.assertIsNone(check_payment_action(payment, order, "failed"))
        self.assertIn("Only a paid payment", check_payment_action(payment, order, "refunded"))

    def test_available_actions_depend_on_the_status(self):
        order = self.bkash_order()
        payment = self.payment(order)
        names = [item["action"] for item in available_payment_actions(payment, order)]
        self.assertEqual(names, ["paid", "failed"])

        payment.status = Payment.Status.PAID
        names = [item["action"] for item in available_payment_actions(payment, order)]
        self.assertEqual(names, ["refunded"])

        payment.status = Payment.Status.REFUNDED
        self.assertEqual(available_payment_actions(payment, order), [])

    def test_page_shows_an_active_paid_button_when_allowed(self):
        order = self.bkash_order()
        self.login("seller1")
        response = self.detail(order)
        self.assertContains(response, "Mark as paid")
        self.assertContains(response, "Mark as failed")

    def test_page_explains_why_paid_is_not_possible_yet(self):
        order = self.cod_order()
        self.login("seller1")
        response = self.detail(order)
        self.assertContains(response, "Mark as paid")
        self.assertContains(response, "can be marked as paid after the order is shipped")

    def test_page_shows_refund_for_a_paid_payment(self):
        order = self.bkash_order()
        self.set_payment(order, Payment.Status.PAID)
        self.login("seller1")
        response = self.detail(order)
        self.assertContains(response, "Mark as refunded")
        self.assertNotContains(response, "Mark as paid")

    def test_page_shows_no_buttons_for_a_refunded_payment(self):
        order = self.bkash_order()
        self.set_payment(order, Payment.Status.REFUNDED)
        self.login("seller1")
        response = self.detail(order)
        self.assertContains(response, "No further payment actions")

    def test_customer_sees_the_new_payment_status(self):
        order = self.bkash_order()
        self.login("seller1")
        self.act(order, "paid")
        self.client.logout()
        self.login("cust")
        page = self.client.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertContains(page, "Payment confirmed")