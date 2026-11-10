import re
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from accounts.models import User
from catalog.models import Product
from shops.models import Shop

from .models import Order, OrderItem

PASSWORD = "StrongPass#2026"


class OrderModelTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="cust", password=PASSWORD, role="customer")
        seller = User.objects.create_user(username="seller", password=PASSWORD, role="seller")
        self.shop = Shop.objects.create(
            owner=seller, name="Rahim Fashion", description="Clothes", is_published=True
        )
        self.product = Product.objects.create(
            shop=self.shop, name="Blue T-Shirt", price=Decimal("450.00"), stock=10, is_published=True
        )

    def make_order(self, **changes):
        data = {
            "customer": self.customer,
            "shop": self.shop,
            "subtotal": Decimal("900.00"),
            "delivery_charge": Decimal("60.00"),
            "total": Decimal("960.00"),
            "shipping_name": "Rahim Uddin",
            "shipping_phone": "01712345678",
            "shipping_address": "House 12, Road 5",
            "shipping_city": "Dhaka",
        }
        data.update(changes)
        return Order.objects.create(**data)

    def make_item(self, order, quantity=2):
        return OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=quantity,
        )

    def test_order_number_has_the_expected_format(self):
        order = self.make_order()
        self.assertRegex(order.order_number, r"^MF-\d{6}-[A-HJ-NP-Z2-9]{6}$")

    def test_order_numbers_are_unique(self):
        numbers = {self.make_order().order_number for _ in range(20)}
        self.assertEqual(len(numbers), 20)

    def test_order_number_never_changes(self):
        order = self.make_order()
        number = order.order_number
        order.status = Order.Status.CONFIRMED
        order.save()
        order.refresh_from_db()
        self.assertEqual(order.order_number, number)

    def test_new_orders_start_as_pending(self):
        self.assertEqual(self.make_order().status, Order.Status.PENDING)

    def test_newest_order_comes_first(self):
        first = self.make_order()
        second = self.make_order()
        self.assertEqual(list(Order.objects.all()), [second, first])

    def test_line_total_is_price_times_quantity(self):
        item = self.make_item(self.make_order(), quantity=3)
        self.assertEqual(item.line_total, Decimal("1350.00"))

    def test_order_keeps_its_items(self):
        order = self.make_order()
        self.make_item(order)
        self.make_item(order, quantity=1)
        self.assertEqual(order.items.count(), 2)

    def test_item_keeps_the_old_price_and_name_when_the_product_changes(self):
        item = self.make_item(self.make_order())
        self.product.price = Decimal("999.00")
        self.product.name = "Renamed Shirt"
        self.product.save()
        item.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal("450.00"))
        self.assertEqual(item.product_name, "Blue T-Shirt")
        self.assertEqual(item.line_total, Decimal("900.00"))

    def test_item_survives_when_the_product_is_deleted(self):
        item = self.make_item(self.make_order())
        self.product.delete()
        item.refresh_from_db()
        self.assertIsNone(item.product)
        self.assertEqual(item.product_name, "Blue T-Shirt")
        self.assertEqual(item.unit_price, Decimal("450.00"))

    def test_order_keeps_its_delivery_charge_when_the_shop_changes_it(self):
        order = self.make_order()
        self.shop.delivery_charge = Decimal("100.00")
        self.shop.save()
        order.refresh_from_db()
        self.assertEqual(order.delivery_charge, Decimal("60.00"))
        self.assertEqual(order.total, Decimal("960.00"))

    def test_database_refuses_a_quantity_of_zero(self):
        order = self.make_order()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OrderItem.objects.create(
                    order=order,
                    product=self.product,
                    product_name="Blue T-Shirt",
                    unit_price=Decimal("450.00"),
                    quantity=0,
                )

    def test_customer_with_orders_cannot_be_deleted(self):
        self.make_order()
        with self.assertRaises(ProtectedError):
            self.customer.delete()

    def test_shop_with_orders_cannot_be_deleted(self):
        self.make_order()
        with self.assertRaises(ProtectedError):
            self.shop.delete()