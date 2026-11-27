from decimal import Decimal

from django.urls import reverse

from catalog.models import Product

from .models import Order, OrderItem
from .tests import CheckoutTestBase
from .workflow import OrderTransitionError, apply_seller_action


class WorkflowTestBase(CheckoutTestBase):
    def setUp(self):
        super().setUp()
        self.cap = Product.objects.create(
            shop=self.shop1, name="Cotton Cap", price=Decimal("200.00"), stock=5, is_published=True
        )

    def make_order(self, items=None, shop=None, status=Order.Status.PENDING, customer=None):
        shop = shop or self.shop1
        items = items or [(self.shirt, 3)]
        subtotal = sum((p.price * q for p, q in items), Decimal("0"))
        order = Order.objects.create(
            customer=customer or self.customer,
            shop=shop,
            status=status,
            subtotal=subtotal,
            delivery_charge=shop.delivery_charge,
            total=subtotal + shop.delivery_charge,
            shipping_name="Karim Uddin",
            shipping_phone="01812345678",
            shipping_address="House 12, Road 5",
            shipping_city="Dhaka",
        )
        for product, quantity in items:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )
        return order

    def act(self, order, action, follow=False):
        url = reverse("orders:seller_order_action", args=[order.order_number])
        return self.client.post(url, {"action": action}, follow=follow)

    def stock(self, product):
        product.refresh_from_db()
        return product.stock

    def status(self, order):
        order.refresh_from_db()
        return order.status

    def detail(self, order):
        return self.client.get(reverse("orders:seller_order_detail", args=[order.order_number]))


class ConfirmTests(WorkflowTestBase):
    def test_confirming_reduces_the_stock_and_sets_the_status(self):
        order = self.make_order([(self.shirt, 3)])
        self.login("seller1")
        self.act(order, "confirm")
        self.assertEqual(self.status(order), Order.Status.CONFIRMED)
        self.assertEqual(self.stock(self.shirt), 7)

    def test_every_item_of_the_order_is_reduced(self):
        order = self.make_order([(self.shirt, 2), (self.cap, 5)])
        self.login("seller1")
        self.act(order, "confirm")
        self.assertEqual(self.stock(self.shirt), 8)
        self.assertEqual(self.stock(self.cap), 0)

    def test_success_message_is_shown(self):
        order = self.make_order()
        self.login("seller1")
        response = self.act(order, "confirm", follow=True)
        self.assertContains(response, "confirmed")

    def test_not_enough_stock_blocks_confirmation(self):
        Product.objects.filter(pk=self.shirt.pk).update(stock=2)
        order = self.make_order([(self.shirt, 3)])
        self.login("seller1")
        response = self.act(order, "confirm", follow=True)
        self.assertContains(response, "Not enough stock")
        self.assertEqual(self.status(order), Order.Status.PENDING)
        self.assertEqual(self.stock(self.shirt), 2)

    def test_a_shortage_in_one_item_changes_nothing(self):
        Product.objects.filter(pk=self.cap.pk).update(stock=1)
        order = self.make_order([(self.shirt, 2), (self.cap, 3)])
        self.login("seller1")
        self.act(order, "confirm")
        self.assertEqual(self.status(order), Order.Status.PENDING)
        self.assertEqual(self.stock(self.shirt), 10)  # not reduced: all or nothing
        self.assertEqual(self.stock(self.cap), 1)

    def test_deleted_product_blocks_confirmation(self):
        order = self.make_order([(self.shirt, 1)])
        self.shirt.delete()
        self.login("seller1")
        response = self.act(order, "confirm", follow=True)
        self.assertContains(response, "no longer exists")
        self.assertEqual(self.status(order), Order.Status.PENDING)

    def test_confirming_twice_reduces_the_stock_only_once(self):
        order = self.make_order([(self.shirt, 3)])
        self.login("seller1")
        self.act(order, "confirm")
        self.act(order, "confirm")
        self.assertEqual(self.stock(self.shirt), 7)

    def test_two_orders_for_the_last_items_cannot_both_be_confirmed(self):
        Product.objects.filter(pk=self.shirt.pk).update(stock=3)
        first = self.make_order([(self.shirt, 3)])
        second = self.make_order([(self.shirt, 2)], customer=self.other_customer)
        self.login("seller1")
        self.act(first, "confirm")
        self.act(second, "confirm")
        self.assertEqual(self.status(first), Order.Status.CONFIRMED)
        self.assertEqual(self.status(second), Order.Status.PENDING)
        self.assertEqual(self.stock(self.shirt), 0)


class RejectTests(WorkflowTestBase):
    def test_rejecting_keeps_the_stock(self):
        order = self.make_order([(self.shirt, 3)])
        self.login("seller1")
        self.act(order, "reject")
        self.assertEqual(self.status(order), Order.Status.REJECTED)
        self.assertEqual(self.stock(self.shirt), 10)

    def test_rejected_order_cannot_be_confirmed(self):
        order = self.make_order(status=Order.Status.REJECTED)
        self.login("seller1")
        self.act(order, "confirm")
        self.assertEqual(self.status(order), Order.Status.REJECTED)
        self.assertEqual(self.stock(self.shirt), 10)

    def test_cancelled_order_cannot_be_confirmed(self):
        order = self.make_order(status=Order.Status.CANCELLED)
        self.login("seller1")
        self.act(order, "confirm")
        self.assertEqual(self.status(order), Order.Status.CANCELLED)
        self.assertEqual(self.stock(self.shirt), 10)


class StatusFlowTests(WorkflowTestBase):
    def test_an_order_can_go_through_every_step(self):
        order = self.make_order()
        self.login("seller1")
        for action, expected in [
            ("confirm", Order.Status.CONFIRMED),
            ("process", Order.Status.PROCESSING),
            ("ship", Order.Status.SHIPPED),
            ("complete", Order.Status.COMPLETED),
        ]:
            with self.subTest(action=action):
                self.act(order, action)
                self.assertEqual(self.status(order), expected)

    def test_steps_cannot_be_skipped(self):
        order = self.make_order()
        self.login("seller1")
        self.act(order, "ship")
        self.assertEqual(self.status(order), Order.Status.PENDING)
        self.act(order, "complete")
        self.assertEqual(self.status(order), Order.Status.PENDING)

    def test_confirmed_order_cannot_be_rejected_or_completed(self):
        order = self.make_order(status=Order.Status.CONFIRMED)
        self.login("seller1")
        self.act(order, "reject")
        self.act(order, "complete")
        self.assertEqual(self.status(order), Order.Status.CONFIRMED)

    def test_completed_order_cannot_be_changed(self):
        order = self.make_order(status=Order.Status.COMPLETED)
        self.login("seller1")
        for action in ["confirm", "reject", "process", "ship", "complete"]:
            with self.subTest(action=action):
                self.act(order, action)
                self.assertEqual(self.status(order), Order.Status.COMPLETED)

    def test_unknown_action_is_refused(self):
        order = self.make_order()
        self.login("seller1")
        self.act(order, "delete")
        self.assertEqual(self.status(order), Order.Status.PENDING)

    def test_error_message_explains_why(self):
        order = self.make_order(status=Order.Status.SHIPPED)
        self.login("seller1")
        response = self.act(order, "confirm", follow=True)
        self.assertContains(response, "the order is shipped")


class WorkflowAccessTests(WorkflowTestBase):
    def test_another_seller_cannot_change_the_order(self):
        order = self.make_order()
        self.login("seller2")
        response = self.act(order, "confirm")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.status(order), Order.Status.PENDING)
        self.assertEqual(self.stock(self.shirt), 10)

    def test_customer_cannot_use_seller_actions(self):
        order = self.make_order()
        self.login("cust")
        self.assertEqual(self.act(order, "confirm").status_code, 403)
        self.assertEqual(self.status(order), Order.Status.PENDING)

    def test_visitor_is_sent_to_login(self):
        order = self.make_order()
        response = self.act(order, "confirm")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertEqual(self.status(order), Order.Status.PENDING)

    def test_actions_require_a_post_request(self):
        order = self.make_order()
        self.login("seller1")
        url = reverse("orders:seller_order_action", args=[order.order_number])
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_workflow_function_refuses_the_wrong_shop(self):
        order = self.make_order()
        with self.assertRaises(OrderTransitionError):
            apply_seller_action(order.pk, self.shop2, "confirm")
        self.assertEqual(self.status(order), Order.Status.PENDING)


class OrderPageButtonTests(WorkflowTestBase):
    def test_pending_order_shows_confirm_and_reject(self):
        order = self.make_order()
        self.login("seller1")
        response = self.detail(order)
        self.assertContains(response, "Confirm order")
        self.assertContains(response, "Reject order")

    def test_each_status_shows_its_own_button(self):
        self.login("seller1")
        cases = [
            (Order.Status.CONFIRMED, "Start processing"),
            (Order.Status.PROCESSING, "Mark as shipped"),
            (Order.Status.SHIPPED, "Mark as completed"),
        ]
        for status, label in cases:
            with self.subTest(status=status):
                order = self.make_order(status=status)
                response = self.detail(order)
                self.assertContains(response, label)
                self.assertNotContains(response, "Confirm order")

    def test_finished_orders_show_no_actions(self):
        self.login("seller1")
        for status in [Order.Status.COMPLETED, Order.Status.REJECTED, Order.Status.CANCELLED]:
            with self.subTest(status=status):
                order = self.make_order(status=status)
                self.assertContains(self.detail(order), "No further actions")

    def test_pending_order_shows_the_current_stock(self):
        Product.objects.filter(pk=self.shirt.pk).update(stock=2)
        order = self.make_order([(self.shirt, 3)])
        self.login("seller1")
        response = self.detail(order)
        self.assertContains(response, "In stock now")
        self.assertContains(response, "Not enough stock")

    def test_enough_stock_is_shown_as_ok(self):
        order = self.make_order([(self.shirt, 3)])
        self.login("seller1")
        self.assertNotContains(self.detail(order), "Not enough stock")