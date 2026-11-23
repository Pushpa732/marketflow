from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Category, Product
from customers.models import Address
from orders.models import Order
from payments.models import Payment
from shops.models import Shop

PASSWORD = "StrongPass#2026"


def register(client, username, role):
    return client.post(
        reverse("accounts:register"),
        {
            "username": username,
            "email": f"{username}@example.com",
            "phone": "01712345678",
            "role": role,
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )


class CompleteJourneyTest(TestCase):
    def test_from_shop_setup_to_a_paid_order(self):
        # 1. A business owner registers, sets up the shop, and adds a product.
        seller = Client()
        register(seller, "rahim", "seller")
        seller.post(
            reverse("shops:shop_profile"),
            {
                "name": "Rahim Fashion",
                "description": "Clothes for everyone",
                "category": "Fashion",
                "delivery_charge": "80",
                "bkash_number": "01711111111",
            },
        )
        seller.post(reverse("shops:toggle_publish"))

        category = Category.objects.create(name="Fashion")
        seller.post(
            reverse("catalog:product_create"),
            {
                "name": "Blue T-Shirt",
                "category": category.pk,
                "description": "Soft cotton t-shirt",
                "price": "450.00",
                "stock": "5",
                "low_stock_threshold": "2",
                "is_published": "on",
            },
        )
        shop = Shop.objects.get()
        product = Product.objects.get()
        self.assertTrue(shop.is_published)
        self.assertEqual(product.shop, shop)

        # 2. A visitor finds the product by browsing, searching, and filtering.
        visitor = Client()
        self.assertContains(visitor.get(reverse("marketplace:home")), "Blue T-Shirt")
        self.assertContains(
            visitor.get(reverse("marketplace:search"), {"q": "shirt"}), "Blue T-Shirt"
        )
        listing = reverse("marketplace:product_list")
        self.assertContains(visitor.get(listing, {"max_price": "500"}), "Blue T-Shirt")
        self.assertNotContains(visitor.get(listing, {"max_price": "100"}), "Blue T-Shirt")
        detail = visitor.get(reverse("marketplace:product_detail", args=[product.slug]))
        self.assertContains(detail, "Soft cotton t-shirt")

        # 3. The visitor adds two shirts to the cart and tries to check out.
        visitor.post(reverse("cart:add", args=[product.pk]), {"quantity": "2"})
        self.assertEqual(visitor.session["cart"], {str(product.pk): 2})
        response = visitor.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("next=/checkout/", response.url)

        # 4. The visitor registers as a customer. The cart is kept.
        register(visitor, "karim", "customer")
        self.assertEqual(visitor.session["cart"], {str(product.pk): 2})

        # 5. The customer saves a delivery address and opens checkout.
        visitor.post(
            reverse("customers:address_create"),
            {
                "full_name": "Karim Uddin",
                "phone": "01812345678",
                "address_line": "House 12, Road 5",
                "city": "Dhaka",
            },
        )
        address = Address.objects.get()
        page = visitor.get(reverse("orders:checkout"))
        self.assertEqual(page.status_code, 200)
        summary = page.context["summary"]
        self.assertEqual(summary["grand_total"], Decimal("980.00"))  # 2 x 450 + 80
        options = {o["value"]: o for o in page.context["payment_options"]}
        self.assertTrue(options["bkash"]["available"])
        self.assertFalse(options["nagad"]["available"])

        # 6. The customer places the order, paying by bKash.
        response = visitor.post(
            reverse("orders:checkout"),
            {
                "address": address.pk,
                "payment_method": "bkash",
                "expected_total": str(summary["grand_total"]),
            },
        )
        self.assertRedirects(response, reverse("orders:order_list"))

        order = Order.objects.get()
        self.assertEqual(order.shop, shop)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.total, Decimal("980.00"))
        self.assertEqual(order.shipping_name, "Karim Uddin")
        item = order.items.get()
        self.assertEqual((item.product_name, item.unit_price, item.quantity), ("Blue T-Shirt", Decimal("450.00"), 2))

        payment = Payment.objects.get()
        self.assertEqual(payment.method, Payment.Method.BKASH)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.amount, Decimal("980.00"))

        # 7. The cart is empty, and stock is not reduced until the seller confirms.
        self.assertEqual(visitor.session["cart"], {})
        product.refresh_from_db()
        self.assertEqual(product.stock, 5)

        # 8. The customer submits the bKash transaction ID and sees the order.
        visitor.post(
            reverse("payments:submit_transaction_id", args=[order.order_number]),
            {"transaction_id": "8n7a6d5ee7"},
        )
        payment.refresh_from_db()
        self.assertEqual(payment.transaction_id, "8N7A6D5EE7")
        self.assertEqual(payment.status, Payment.Status.PENDING)

        order_page = visitor.get(reverse("orders:order_detail", args=[order.order_number]))
        self.assertContains(order_page, order.order_number)
        self.assertContains(order_page, "8N7A6D5EE7")
        self.assertContains(order_page, "Pending")

        # 9. Privacy: another customer and the seller cannot open the order page.
        other = Client()
        register(other, "other", "customer")
        detail_url = reverse("orders:order_detail", args=[order.order_number])
        self.assertEqual(other.get(detail_url).status_code, 404)
        self.assertEqual(seller.get(detail_url).status_code, 403)

        # 10. Changing the price later does not change the order.
        product.price = Decimal("999.00")
        product.save()
        item.refresh_from_db()
        self.assertEqual(item.unit_price, Decimal("450.00"))